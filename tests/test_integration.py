#!/usr/bin/env python3
"""Integration tests for the Flask application."""

import unittest
import json
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app


class TestIntegration(unittest.TestCase):
    """Integration tests for the Flask application."""

    def setUp(self):
        """Set up test fixtures."""
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_index_route_returns_html(self):
        """Test that the index route returns HTML content."""
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)
        # Should contain some basic HTML structure
        self.assertIn(b'<html', response.data.lower())
        self.assertIn(b'</html>', response.data.lower())

    def test_metrics_route_returns_json(self):
        """Test that the metrics route returns valid JSON."""
        response = self.client.get('/metrics')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Parse JSON response
        data = json.loads(response.data)
        
        # Check that required fields are present
        required_fields = [
            'timestamp', 'cpu_percent', 'memory_percent', 'disk_percent',
            'uptime', 'network', 'gpu_metrics', 'platform', 'memory_pressure',
            'thermal_status'
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")

    def test_metrics_route_data_types(self):
        """Test that metrics route returns correct data types."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        # Test numeric fields
        self.assertIsInstance(data['cpu_percent'], (int, float))
        self.assertIsInstance(data['memory_percent'], (int, float))
        self.assertIsInstance(data['disk_percent'], (int, float))
        
        # Test string fields
        self.assertIsInstance(data['timestamp'], str)
        self.assertIsInstance(data['uptime'], str)
        
        # Test dictionary fields
        self.assertIsInstance(data['network'], dict)
        self.assertIsInstance(data['gpu_metrics'], dict)
        self.assertIsInstance(data['platform'], dict)
        self.assertIsInstance(data['memory_pressure'], dict)
        self.assertIsInstance(data['thermal_status'], dict)

    def test_metrics_route_platform_info(self):
        """Test that platform information is correctly included."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        platform = data['platform']
        self.assertIn('system', platform)
        self.assertIn('machine', platform)
        self.assertIn('is_jetson', platform)
        self.assertIsInstance(platform['is_jetson'], bool)

    def test_metrics_route_network_info(self):
        """Test that network information is correctly included."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        network = data['network']
        required_network_fields = [
            'bytes_sent', 'bytes_recv', 'bytes_sent_human', 'bytes_recv_human',
            'sent_speed', 'recv_speed', 'sent_speed_human', 'recv_speed_human'
        ]
        
        for field in required_network_fields:
            self.assertIn(field, network, f"Missing network field: {field}")

    def test_metrics_route_memory_pressure_info(self):
        """Test that memory pressure information is correctly included."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        memory_pressure = data['memory_pressure']
        self.assertIn('memory_pressure', memory_pressure)
        self.assertIn('swap', memory_pressure)
        self.assertIn('memory', memory_pressure)
        
        # Test that memory_pressure is a numeric value
        self.assertIsInstance(memory_pressure['memory_pressure'], (int, float))
        self.assertGreaterEqual(memory_pressure['memory_pressure'], 0)
        self.assertLessEqual(memory_pressure['memory_pressure'], 100)

    def test_metrics_route_thermal_status(self):
        """Test that thermal status information is correctly included."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        thermal_status = data['thermal_status']
        self.assertIn('cpu_throttled', thermal_status)
        self.assertIn('gpu_throttled', thermal_status)
        self.assertIn('status', thermal_status)
        
        # Test that boolean fields are actually boolean
        self.assertIsInstance(thermal_status['cpu_throttled'], bool)
        self.assertIsInstance(thermal_status['gpu_throttled'], bool)
        
        # Test that status is a valid string
        self.assertIn(thermal_status['status'], ['Normal', 'Throttled', 'Unknown', 'Error'])

    def test_metrics_route_gpu_metrics(self):
        """Test that GPU metrics are correctly included."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        gpu_metrics = data['gpu_metrics']
        
        # GPU metrics should either contain actual metrics or an error
        if 'error' in gpu_metrics:
            self.assertIsInstance(gpu_metrics['error'], str)
        else:
            # Should contain at least some GPU information
            self.assertTrue(len(gpu_metrics) > 0)

    def test_metrics_route_timestamp_format(self):
        """Test that timestamp is in the expected format."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        timestamp = data['timestamp']
        # Should be in format: YYYY-MM-DD HH:MM:SS
        import re
        timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        self.assertIsNotNone(re.match(timestamp_pattern, timestamp))

    def test_metrics_route_uptime_format(self):
        """Test that uptime is in the expected format."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        uptime = data['uptime']
        # Should be in format: Xh Ym Zs
        import re
        uptime_pattern = r'^\d+h \d+m \d+s$'
        self.assertIsNotNone(re.match(uptime_pattern, uptime))

    def test_metrics_route_percentage_values(self):
        """Test that percentage values are within valid ranges."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        # CPU, memory, and disk percentages should be between 0 and 100
        self.assertGreaterEqual(data['cpu_percent'], 0)
        self.assertLessEqual(data['cpu_percent'], 100)
        self.assertGreaterEqual(data['memory_percent'], 0)
        self.assertLessEqual(data['memory_percent'], 100)
        self.assertGreaterEqual(data['disk_percent'], 0)
        self.assertLessEqual(data['disk_percent'], 100)

    def test_metrics_route_network_speed_formats(self):
        """Test that network speed human-readable formats are correct."""
        response = self.client.get('/metrics')
        data = json.loads(response.data)
        
        network = data['network']
        
        # Human-readable formats should end with appropriate units
        self.assertTrue(network['sent_speed_human'].endswith(' KB/s'))
        self.assertTrue(network['recv_speed_human'].endswith(' KB/s'))
        
        # Human-readable byte formats should have appropriate units
        self.assertTrue(any(network['bytes_sent_human'].endswith(unit) 
                          for unit in [' B', ' KB', ' MB', ' GB']))
        self.assertTrue(any(network['bytes_recv_human'].endswith(unit) 
                          for unit in [' B', ' KB', ' MB', ' GB']))

    def test_metrics_route_consistency(self):
        """Test that multiple calls to metrics return consistent data structure."""
        response1 = self.client.get('/metrics')
        response2 = self.client.get('/metrics')
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Both responses should have the same structure
        self.assertEqual(set(data1.keys()), set(data2.keys()))
        
        # Platform info should be consistent
        self.assertEqual(data1['platform']['system'], data2['platform']['system'])
        self.assertEqual(data1['platform']['machine'], data2['platform']['machine'])
        self.assertEqual(data1['platform']['is_jetson'], data2['platform']['is_jetson'])

    def test_404_route(self):
        """Test that non-existent routes return 404."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_metrics_route_method_not_allowed(self):
        """Test that POST to metrics route is not allowed."""
        response = self.client.post('/metrics')
        self.assertEqual(response.status_code, 405)

    def test_index_route_method_not_allowed(self):
        """Test that POST to index route is not allowed."""
        response = self.client.post('/')
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main()
