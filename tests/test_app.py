#!/usr/bin/env python3
"""Unit tests for app.py."""

import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import sys
import os
import tempfile
import shutil
import subprocess

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app


class TestApp(unittest.TestCase):
    """Test cases for the main app module."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset any function attributes that might persist between tests
        if hasattr(app.get_network_metrics, 'prev_net_io'):
            delattr(app.get_network_metrics, 'prev_net_io')
        if hasattr(app.get_network_metrics, 'prev_time'):
            delattr(app.get_network_metrics, 'prev_time')

    def test_constants_defined(self):
        """Test that all constants are properly defined."""
        self.assertEqual(app.TEGRASTATS_INTERVAL, 1000)
        self.assertEqual(app.MEMORY_PRESSURE_WEIGHTS['memory_usage'], 0.7)
        self.assertEqual(app.MEMORY_PRESSURE_WEIGHTS['swap_usage'], 0.2)
        self.assertEqual(app.MEMORY_PRESSURE_WEIGHTS['available'], 0.1)
        self.assertEqual(app.LOW_MEMORY_THRESHOLD, 50)
        self.assertEqual(app.LOW_SWAP_THRESHOLD, 20)
        self.assertEqual(app.MAX_PRESSURE_CAP, 50)
        self.assertEqual(app.BYTES_PER_MB, 1024 * 1024)
        self.assertEqual(app.BYTES_PER_KB, 1024)
        self.assertEqual(app.SECONDS_PER_HOUR, 3600)
        self.assertEqual(app.SECONDS_PER_MINUTE, 60)

    @patch('builtins.open', new_callable=mock_open, read_data='NVIDIA Jetson Nano Developer Kit')
    def test_is_jetson_true(self, mock_file):
        """Test is_jetson() returns True for Jetson device."""
        result = app.is_jetson()
        self.assertTrue(result)
        mock_file.assert_called_once_with('/proc/device-tree/model', 'r')

    @patch('builtins.open', new_callable=mock_open, read_data='Intel Core i7')
    def test_is_jetson_false(self, mock_file):
        """Test is_jetson() returns False for non-Jetson device."""
        result = app.is_jetson()
        self.assertFalse(result)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_is_jetson_file_not_found(self, mock_file):
        """Test is_jetson() handles FileNotFoundError gracefully."""
        result = app.is_jetson()
        self.assertFalse(result)

    @patch('builtins.open', side_effect=PermissionError)
    def test_is_jetson_permission_error(self, mock_file):
        """Test is_jetson() handles PermissionError gracefully."""
        result = app.is_jetson()
        self.assertFalse(result)

    def test_parse_tegrastats_value_success(self):
        """Test parse_tegrastats_value() with valid input."""
        stats = "RAM 2048/8192MB GR3D_FREQ 50% gpu@45C"
        result = app.parse_tegrastats_value(stats, 'GR3D_FREQ', '%')
        self.assertEqual(result, 50.0)

    def test_parse_tegrastats_value_not_found(self):
        """Test parse_tegrastats_value() when key not found."""
        stats = "RAM 2048/8192MB gpu@45C"
        result = app.parse_tegrastats_value(stats, 'GR3D_FREQ', '%')
        self.assertIsNone(result)

    def test_parse_tegrastats_value_invalid_format(self):
        """Test parse_tegrastats_value() with invalid format."""
        stats = "GR3D_FREQ invalid_value%"
        result = app.parse_tegrastats_value(stats, 'GR3D_FREQ', '%')
        self.assertIsNone(result)

    @patch('app.is_jetson', return_value=True)
    @patch('subprocess.Popen')
    def test_get_jetson_gpu_metrics_success(self, mock_popen, mock_is_jetson):
        """Test get_jetson_gpu_metrics() with successful tegrastats output."""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = (
            "RAM 2048/8192MB GR3D_FREQ 75% gpu@65C cpu@70C "
            "VDD_IN 5000mW VDD_CPU_GPU_CV 3000mW"
        )
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        result = app.get_jetson_gpu_metrics()

        self.assertIn('gpu_utilization', result)
        self.assertEqual(result['gpu_utilization'], 75.0)
        self.assertIn('gpu_temperature', result)
        self.assertEqual(result['gpu_temperature'], 65.0)
        self.assertIn('cpu_temperature', result)
        self.assertEqual(result['cpu_temperature'], 70.0)
        self.assertIn('total_power', result)
        self.assertEqual(result['total_power'], 5000.0)
        self.assertIn('gpu_power', result)
        self.assertEqual(result['gpu_power'], 3000.0)

    @patch('app.is_jetson', return_value=True)
    @patch('subprocess.Popen')
    def test_get_jetson_gpu_metrics_with_ram_and_cpu(self, mock_popen, mock_is_jetson):
        """Test get_jetson_gpu_metrics() with RAM and CPU core information."""
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = (
            "RAM 2048/8192MB CPU [25%@1479,50%@1479,75%@1479,100%@1479]"
        )
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        result = app.get_jetson_gpu_metrics()

        self.assertIn('ram_used', result)
        self.assertEqual(result['ram_used'], 2048.0)
        self.assertIn('ram_total', result)
        self.assertEqual(result['ram_total'], 8192.0)
        self.assertIn('ram_percent', result)
        self.assertEqual(result['ram_percent'], 25.0)
        self.assertIn('cpu_cores', result)
        self.assertEqual(len(result['cpu_cores']), 4)
        self.assertEqual(result['cpu_cores'][0]['usage'], 25.0)
        self.assertEqual(result['cpu_cores'][0]['frequency'], 1479.0)

    @patch('app.is_jetson', return_value=True)
    @patch('subprocess.Popen', side_effect=subprocess.SubprocessError("Command not found"))
    def test_get_jetson_gpu_metrics_subprocess_error(self, mock_popen, mock_is_jetson):
        """Test get_jetson_gpu_metrics() handles subprocess errors."""
        result = app.get_jetson_gpu_metrics()
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Failed to get GPU metrics')

    @patch('pynvml.nvmlInit')
    @patch('pynvml.nvmlDeviceGetHandleByIndex')
    @patch('pynvml.nvmlDeviceGetMemoryInfo')
    @patch('pynvml.nvmlDeviceGetUtilizationRates')
    def test_get_nvidia_gpu_metrics_success(self, mock_util, mock_mem, mock_handle, mock_init):
        """Test get_nvidia_gpu_metrics() with successful NVML calls."""
        # Mock memory info
        mock_mem_info = MagicMock()
        mock_mem_info.used = 1024 * 1024 * 1024  # 1GB
        mock_mem_info.total = 4 * 1024 * 1024 * 1024  # 4GB
        mock_mem.return_value = mock_mem_info

        # Mock utilization
        mock_util_info = MagicMock()
        mock_util_info.gpu = 75
        mock_util.return_value = mock_util_info

        result = app.get_nvidia_gpu_metrics()

        self.assertEqual(result['gpu_utilization'], 75)
        self.assertEqual(result['gpu_memory_percent'], 25.0)
        self.assertEqual(result['gpu_memory_used'], 1024.0)  # 1GB in MB
        self.assertEqual(result['gpu_memory_total'], 4096.0)  # 4GB in MB

    @patch('pynvml.nvmlInit')
    @patch('pynvml.nvmlDeviceGetHandleByIndex', side_effect=app.pynvml.NVMLError(1))
    def test_get_nvidia_gpu_metrics_error(self, mock_handle, mock_init):
        """Test get_nvidia_gpu_metrics() handles NVML errors."""
        result = app.get_nvidia_gpu_metrics()
        self.assertIn('error', result)
        self.assertIn('Failed to get GPU metrics', result['error'])

    @patch('app.is_jetson', return_value=True)
    @patch('app.get_jetson_gpu_metrics')
    def test_get_gpu_metrics_jetson(self, mock_jetson_metrics, mock_is_jetson):
        """Test get_gpu_metrics() calls Jetson function when on Jetson device."""
        mock_jetson_metrics.return_value = {'gpu_utilization': 50}
        result = app.get_gpu_metrics()
        mock_jetson_metrics.assert_called_once()
        self.assertEqual(result['gpu_utilization'], 50)

    @patch('app.is_jetson', return_value=False)
    @patch('pynvml.nvmlInit')
    @patch('app.get_nvidia_gpu_metrics')
    def test_get_gpu_metrics_nvidia(self, mock_nvidia_metrics, mock_init, mock_is_jetson):
        """Test get_gpu_metrics() calls NVIDIA function when not on Jetson."""
        mock_nvidia_metrics.return_value = {'gpu_utilization': 60}
        result = app.get_gpu_metrics()
        mock_nvidia_metrics.assert_called_once()
        self.assertEqual(result['gpu_utilization'], 60)

    @patch('app.is_jetson', return_value=False)
    @patch('pynvml.nvmlInit', side_effect=app.pynvml.NVMLError("No GPU"))
    def test_get_gpu_metrics_no_nvidia_gpu(self, mock_init, mock_is_jetson):
        """Test get_gpu_metrics() handles no NVIDIA GPU."""
        result = app.get_gpu_metrics()
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'No NVIDIA GPU detected')

    def test_calculate_memory_pressure_normal(self):
        """Test calculate_memory_pressure() with normal memory usage."""
        mock_memory = MagicMock()
        mock_memory.percent = 60.0
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16GB

        mock_swap = MagicMock()
        mock_swap.percent = 10.0

        result = app.calculate_memory_pressure(mock_memory, mock_swap)
        
        # Expected: 60*0.7 + 10*0.2 + (100-75)*0.1 = 42 + 2 + 2.5 = 46.5
        # But with available memory calculation: (100-75)*0.1 = 2.5
        # So total should be 42 + 2 + 2.5 = 46.5
        # Let's check the actual calculation more carefully
        expected = 60.0 * 0.7 + 10.0 * 0.2 + (100 - (4/16*100)) * 0.1
        self.assertAlmostEqual(result, expected, places=1)

    def test_calculate_memory_pressure_low_usage(self):
        """Test calculate_memory_pressure() with low memory and swap usage."""
        mock_memory = MagicMock()
        mock_memory.percent = 30.0
        mock_memory.available = 12 * 1024 * 1024 * 1024  # 12GB
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16GB

        mock_swap = MagicMock()
        mock_swap.percent = 5.0

        result = app.calculate_memory_pressure(mock_memory, mock_swap)
        
        # Should be capped at MAX_PRESSURE_CAP (50) due to low usage
        self.assertLessEqual(result, app.MAX_PRESSURE_CAP)

    def test_calculate_memory_pressure_high_usage(self):
        """Test calculate_memory_pressure() with high memory usage."""
        mock_memory = MagicMock()
        mock_memory.percent = 95.0
        mock_memory.available = 1 * 1024 * 1024 * 1024  # 1GB
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16GB

        mock_swap = MagicMock()
        mock_swap.percent = 80.0

        result = app.calculate_memory_pressure(mock_memory, mock_swap)
        
        # Should be high but capped at 100
        self.assertGreaterEqual(result, 80.0)
        self.assertLessEqual(result, 100.0)

    @patch('psutil.virtual_memory')
    @patch('psutil.swap_memory')
    def test_get_memory_pressure_metrics_success(self, mock_swap, mock_memory):
        """Test get_memory_pressure_metrics() with successful psutil calls."""
        # Mock memory
        mock_mem = MagicMock()
        mock_mem.percent = 60.0
        mock_mem.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_mem.total = 16 * 1024 * 1024 * 1024  # 16GB
        mock_memory.return_value = mock_mem

        # Mock swap
        mock_swap_mem = MagicMock()
        mock_swap_mem.percent = 10.0
        mock_swap_mem.used = 1 * 1024 * 1024 * 1024  # 1GB
        mock_swap_mem.total = 4 * 1024 * 1024 * 1024  # 4GB
        mock_swap_mem.free = 3 * 1024 * 1024 * 1024  # 3GB
        mock_swap.return_value = mock_swap_mem

        result = app.get_memory_pressure_metrics()

        self.assertIn('memory_pressure', result)
        self.assertIn('swap', result)
        self.assertIn('memory', result)
        self.assertEqual(result['swap']['used'], 1024.0)  # 1GB in MB
        self.assertEqual(result['swap']['total'], 4096.0)  # 4GB in MB
        self.assertEqual(result['memory']['available'], 4096.0)  # 4GB in MB

    @patch('psutil.virtual_memory', side_effect=Exception("psutil error"))
    def test_get_memory_pressure_metrics_error(self, mock_memory):
        """Test get_memory_pressure_metrics() handles exceptions."""
        result = app.get_memory_pressure_metrics()
        self.assertEqual(result['memory_pressure'], 0)
        self.assertEqual(result['swap']['used'], 0)
        self.assertEqual(result['memory']['available'], 0)

    @patch('app.is_jetson', return_value=True)
    @patch('subprocess.Popen')
    def test_get_thermal_throttling_status_jetson_normal(self, mock_popen, mock_is_jetson):
        """Test get_thermal_throttling_status() on Jetson with normal status."""
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = "Normal operation"
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        result = app.get_thermal_throttling_status()

        self.assertFalse(result['cpu_throttled'])
        self.assertFalse(result['gpu_throttled'])
        self.assertEqual(result['status'], 'Normal')

    @patch('app.is_jetson', return_value=True)
    @patch('subprocess.Popen')
    def test_get_thermal_throttling_status_jetson_throttled(self, mock_popen, mock_is_jetson):
        """Test get_thermal_throttling_status() on Jetson with throttling."""
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = "CPU_THROTTLE GPU_THROTTLE"
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        result = app.get_thermal_throttling_status()

        self.assertTrue(result['cpu_throttled'])
        self.assertTrue(result['gpu_throttled'])
        self.assertEqual(result['status'], 'Throttled')

    @patch('app.is_jetson', return_value=False)
    @patch('builtins.open', new_callable=mock_open, read_data='5')
    def test_get_thermal_throttling_status_non_jetson_throttled(self, mock_file, mock_is_jetson):
        """Test get_thermal_throttling_status() on non-Jetson with throttling."""
        result = app.get_thermal_throttling_status()

        self.assertTrue(result['cpu_throttled'])
        self.assertFalse(result['gpu_throttled'])
        self.assertEqual(result['status'], 'Throttled')

    @patch('app.is_jetson', return_value=False)
    @patch('builtins.open', new_callable=mock_open, read_data='0')
    def test_get_thermal_throttling_status_non_jetson_normal(self, mock_file, mock_is_jetson):
        """Test get_thermal_throttling_status() on non-Jetson with normal status."""
        result = app.get_thermal_throttling_status()

        self.assertFalse(result['cpu_throttled'])
        self.assertFalse(result['gpu_throttled'])
        self.assertEqual(result['status'], 'Normal')

    @patch('app.is_jetson', return_value=False)
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_thermal_throttling_status_file_not_found(self, mock_file, mock_is_jetson):
        """Test get_thermal_throttling_status() handles file not found."""
        result = app.get_thermal_throttling_status()

        self.assertFalse(result['cpu_throttled'])
        self.assertFalse(result['gpu_throttled'])
        self.assertEqual(result['status'], 'Unknown')

    def test_format_bytes(self):
        """Test format_bytes() with various byte values."""
        self.assertEqual(app.format_bytes(512), "512 B")
        self.assertEqual(app.format_bytes(1024), "1.0 KB")
        self.assertEqual(app.format_bytes(1024 * 1024), "1.0 MB")
        self.assertEqual(app.format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(app.format_bytes(1536 * 1024), "1.5 MB")

    def test_format_uptime(self):
        """Test format_uptime() with various time values."""
        self.assertEqual(app.format_uptime(3661), "1h 1m 1s")
        self.assertEqual(app.format_uptime(3600), "1h 0m 0s")
        self.assertEqual(app.format_uptime(61), "0h 1m 1s")
        self.assertEqual(app.format_uptime(30), "0h 0m 30s")

    @patch('psutil.net_io_counters')
    def test_get_network_metrics_first_call(self, mock_net_io):
        """Test get_network_metrics() on first call."""
        mock_io = MagicMock()
        mock_io.bytes_sent = 1000
        mock_io.bytes_recv = 2000
        mock_net_io.return_value = mock_io

        result = app.get_network_metrics()

        self.assertEqual(result['bytes_sent'], 1000)
        self.assertEqual(result['bytes_recv'], 2000)
        self.assertEqual(result['sent_speed'], 0)
        self.assertEqual(result['recv_speed'], 0)

    @patch('psutil.net_io_counters')
    @patch('time.time')
    def test_get_network_metrics_with_speed_calculation(self, mock_time, mock_net_io):
        """Test get_network_metrics() with speed calculation."""
        # First call
        mock_io1 = MagicMock()
        mock_io1.bytes_sent = 1000
        mock_io1.bytes_recv = 2000
        
        # Second call
        mock_io2 = MagicMock()
        mock_io2.bytes_sent = 2000  # 1000 bytes more
        mock_io2.bytes_recv = 4000  # 2000 bytes more
        
        mock_net_io.side_effect = [mock_io1, mock_io2]
        mock_time.side_effect = [1000, 1002]  # 2 seconds difference

        # First call
        result1 = app.get_network_metrics()
        self.assertEqual(result1['sent_speed'], 0)
        self.assertEqual(result1['recv_speed'], 0)

        # Second call
        result2 = app.get_network_metrics()
        self.assertEqual(result2['sent_speed'], 500)  # 1000 bytes / 2 seconds
        self.assertEqual(result2['recv_speed'], 1000)  # 2000 bytes / 2 seconds

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.boot_time')
    @patch('time.time')
    @patch('app.get_memory_pressure_metrics')
    @patch('app.get_thermal_throttling_status')
    @patch('app.get_network_metrics')
    @patch('app.get_gpu_metrics')
    @patch('platform.system')
    @patch('platform.machine')
    @patch('app.is_jetson')
    def test_get_system_metrics(self, mock_is_jetson, mock_machine, mock_system,
                               mock_gpu, mock_network, mock_thermal, mock_memory_pressure,
                               mock_time, mock_boot, mock_disk, mock_memory, mock_cpu):
        """Test get_system_metrics() returns complete system information."""
        # Mock all the dependencies
        mock_cpu.return_value = 25.5
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(percent=45.0)
        mock_boot.return_value = 1000000
        mock_time.return_value = 1000361  # 361 seconds after boot
        mock_memory_pressure.return_value = {'memory_pressure': 30.0}
        mock_thermal.return_value = {'status': 'Normal'}
        mock_network.return_value = {'bytes_sent': 1000, 'bytes_recv': 2000}
        mock_gpu.return_value = {'gpu_utilization': 50}
        mock_system.return_value = 'Linux'
        mock_machine.return_value = 'x86_64'
        mock_is_jetson.return_value = False

        result = app.get_system_metrics()

        # Verify all expected keys are present
        expected_keys = [
            'timestamp', 'cpu_percent', 'memory_percent', 'disk_percent',
            'uptime', 'network', 'gpu_metrics', 'platform', 'memory_pressure',
            'thermal_status'
        ]
        for key in expected_keys:
            self.assertIn(key, result)

        # Verify specific values
        self.assertEqual(result['cpu_percent'], 25.5)
        self.assertEqual(result['memory_percent'], 60.0)
        self.assertEqual(result['disk_percent'], 45.0)
        self.assertEqual(result['uptime'], '0h 6m 1s')
        self.assertEqual(result['platform']['system'], 'Linux')
        self.assertEqual(result['platform']['is_jetson'], False)

    def test_flask_app_creation(self):
        """Test that Flask app is created correctly."""
        self.assertIsNotNone(app.app)
        # Flask converts relative paths to absolute paths
        self.assertIn('static', app.app.static_folder)

    @patch('app.render_template')
    def test_index_route(self, mock_render):
        """Test the index route."""
        mock_render.return_value = 'rendered_template'
        
        with app.app.test_client() as client:
            response = client.get('/')
            
        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once_with('index.html')

    @patch('app.get_system_metrics')
    def test_metrics_route(self, mock_metrics):
        """Test the metrics route."""
        mock_metrics.return_value = {'cpu_percent': 25.0}
        
        with app.app.test_client() as client:
            response = client.get('/metrics')
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'cpu_percent': 25.0})
        mock_metrics.assert_called_once()


if __name__ == '__main__':
    unittest.main()
