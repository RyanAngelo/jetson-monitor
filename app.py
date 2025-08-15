from datetime import datetime
import subprocess
import platform
import os
import time

from flask import Flask, render_template, jsonify
import psutil
import pynvml

app = Flask(__name__, static_folder='static')

def is_jetson():
    """Check if the system is a Jetson device."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().lower()
            return 'jetson' in model
    except:
        return False

def get_jetson_gpu_metrics():
    """Get GPU metrics using tegrastats for Jetson devices."""
    try:
        # Use Popen to start tegrastats and pipe its output
        tegrastats_process = subprocess.Popen(['tegrastats', '--interval', '1000'], 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE,
                                            text=True)
        
        # Read the first line of output
        stats = tegrastats_process.stdout.readline().strip()
        print("Processing line:", stats)  # Debug print
        
        # Terminate the process
        tegrastats_process.terminate()
        tegrastats_process.wait(timeout=1)
        
        metrics = {}
        
        # Extract GR3D_FREQ (GPU usage)
        if 'GR3D_FREQ' in stats:
            gpu_part = stats.split('GR3D_FREQ')[1].split('%')[0].strip()
            try:
                metrics['gpu_utilization'] = float(gpu_part)
            except ValueError as e:
                print(f"Could not parse GPU value: {gpu_part}, error: {str(e)}")
        
        # Extract temperatures
        if 'gpu@' in stats:
            gpu_temp = stats.split('gpu@')[1].split('C')[0]
            try:
                metrics['gpu_temperature'] = float(gpu_temp)
            except ValueError:
                pass
        
        if 'cpu@' in stats:
            cpu_temp = stats.split('cpu@')[1].split('C')[0]
            try:
                metrics['cpu_temperature'] = float(cpu_temp)
            except ValueError:
                pass
        
        # Extract power information
        if 'VDD_IN' in stats:
            power_part = stats.split('VDD_IN')[1].split('mW')[0].strip()
            try:
                metrics['total_power'] = float(power_part)
            except ValueError:
                pass
        
        if 'VDD_CPU_GPU_CV' in stats:
            gpu_power_part = stats.split('VDD_CPU_GPU_CV')[1].split('mW')[0].strip()
            try:
                metrics['gpu_power'] = float(gpu_power_part)
            except ValueError:
                pass
        
        # Extract RAM information
        if 'RAM' in stats:
            ram_part = stats.split('RAM')[1].split('MB')[0].strip()
            try:
                used, total = ram_part.split('/')
                metrics['ram_used'] = float(used)
                metrics['ram_total'] = float(total)
                metrics['ram_percent'] = (float(used) / float(total)) * 100
            except ValueError:
                pass
        
        # Extract CPU usage for each core
        if 'CPU [' in stats:
            cpu_part = stats.split('CPU [')[1].split(']')[0]
            cpu_cores = []
            for core in cpu_part.split(','):
                try:
                    usage = float(core.split('@')[0].strip('%'))
                    freq = float(core.split('@')[1])
                    cpu_cores.append({'usage': usage, 'frequency': freq})
                except (ValueError, IndexError):
                    continue
            metrics['cpu_cores'] = cpu_cores
        
        return metrics
            
    except (subprocess.SubprocessError, ValueError) as e:
        print(f"Error getting Jetson GPU metrics: {str(e)}")
    return {'error': 'Failed to get GPU metrics'}

def get_nvidia_gpu_metrics():
    """Get GPU metrics using NVML for standard NVIDIA GPUs."""
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return {
            'gpu_utilization': gpu_utilization.gpu,
            'gpu_memory_percent': (info.used / info.total) * 100,
            'gpu_memory_used': info.used / (1024 * 1024),  # Convert to MB
            'gpu_memory_total': info.total / (1024 * 1024)  # Convert to MB
        }
    except pynvml.NVMLError as e:
        print(f"Error getting NVIDIA GPU metrics: {str(e)}")
        return {'error': f'Failed to get GPU metrics: {str(e)}'}

def get_gpu_metrics():
    """Get GPU metrics based on the platform."""
    if is_jetson():
        return get_jetson_gpu_metrics()
    else:
        try:
            pynvml.nvmlInit()
            return get_nvidia_gpu_metrics()
        except pynvml.NVMLError:
            return {'error': 'No NVIDIA GPU detected'}

def get_memory_pressure_metrics():
    """Get memory pressure and swap metrics."""
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Debug logging
        print(f"Memory: {memory.percent}% used, {memory.available / (1024*1024):.1f} MB available")
        print(f"Swap: {swap.percent}% used, {swap.used / (1024*1024):.1f} MB used")
        
        # Calculate memory pressure score (0-100)
        # Factors: memory usage, swap usage, and available memory
        memory_usage_component = memory.percent * 0.7
        swap_component = swap.percent * 0.2
        available_component = (100 - (memory.available / memory.total * 100)) * 0.1
        
        print(f"Components: Memory={memory_usage_component:.1f}, Swap={swap_component:.1f}, Available={available_component:.1f}")
        
        memory_pressure = memory_usage_component + swap_component + available_component
        
        # Cap the pressure at 100 and ensure it's not negative
        memory_pressure = min(100, max(0, memory_pressure))
        
        # If memory usage is low (< 50%) and swap usage is low (< 20%), 
        # cap the pressure at 50 to better reflect system state
        if memory.percent < 50 and swap.percent < 20:
            memory_pressure = min(memory_pressure, 50)
            print("Low memory and swap usage detected, capping pressure at 50")
        
        print(f"Final pressure score: {memory_pressure:.1f}")
        
        return {
            'memory_pressure': round(memory_pressure, 1),
            'swap': {
                'used': swap.used / (1024 * 1024),  # Convert to MB
                'total': swap.total / (1024 * 1024),  # Convert to MB
                'percent': swap.percent,
                'free': swap.free / (1024 * 1024)  # Convert to MB
            },
            'memory': {
                'available': memory.available / (1024 * 1024),  # Convert to MB
                'total': memory.total / (1024 * 1024),  # Convert to MB
                'percent': memory.percent
            }
        }
    except Exception as e:
        print(f"Error getting memory pressure metrics: {str(e)}")
        return {
            'memory_pressure': 0,
            'swap': {'used': 0, 'total': 0, 'percent': 0, 'free': 0},
            'memory': {'available': 0, 'total': 0, 'percent': 0}
        }

def get_thermal_throttling_status():
    """Get thermal throttling status for CPU and GPU."""
    try:
        # For Jetson devices, we can get this from tegrastats
        if is_jetson():
            tegrastats_process = subprocess.Popen(['tegrastats', '--interval', '1000'], 
                                                stdout=subprocess.PIPE, 
                                                stderr=subprocess.PIPE,
                                                text=True)
            stats = tegrastats_process.stdout.readline().strip()
            tegrastats_process.terminate()
            tegrastats_process.wait(timeout=1)
            
            # Check for thermal throttling indicators in tegrastats output
            cpu_throttled = 'CPU_THROTTLE' in stats
            gpu_throttled = 'GPU_THROTTLE' in stats
            
            return {
                'cpu_throttled': cpu_throttled,
                'gpu_throttled': gpu_throttled,
                'status': 'Throttled' if (cpu_throttled or gpu_throttled) else 'Normal'
            }
        else:
            # For non-Jetson systems, we can check CPU thermal throttling
            try:
                with open('/sys/devices/system/cpu/cpu0/thermal_throttle/core_throttle_count', 'r') as f:
                    throttle_count = int(f.read().strip())
                return {
                    'cpu_throttled': throttle_count > 0,
                    'gpu_throttled': False,  # We don't have GPU throttling info for non-Jetson
                    'status': 'Throttled' if throttle_count > 0 else 'Normal'
                }
            except:
                return {
                    'cpu_throttled': False,
                    'gpu_throttled': False,
                    'status': 'Unknown'
                }
    except Exception as e:
        print(f"Error getting thermal throttling status: {str(e)}")
        return {
            'cpu_throttled': False,
            'gpu_throttled': False,
            'status': 'Error'
        }

def format_bytes(bytes_value):
    """Format bytes into human readable format with appropriate units."""
    if bytes_value >= 1024**3:  # GB
        return f"{bytes_value / (1024**3):.2f} GB"
    elif bytes_value >= 1024**2:  # MB
        return f"{bytes_value / (1024**2):.1f} MB"
    elif bytes_value >= 1024:  # KB
        return f"{bytes_value / 1024:.1f} KB"
    else:
        return f"{bytes_value} B"

def get_system_metrics():
    """Collect and return system metrics including CPU, memory, disk, and GPU usage."""
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory metrics
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get memory pressure metrics
    memory_pressure_metrics = get_memory_pressure_metrics()
    
    # Get thermal throttling status
    thermal_status = get_thermal_throttling_status()
    
    # Disk metrics
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Network metrics
    net_io = psutil.net_io_counters()
    
    # Get the current time
    current_time = time.time()
    
    # Calculate network throughput if we have previous values
    if not hasattr(get_system_metrics, 'prev_net_io'):
        get_system_metrics.prev_net_io = net_io
        get_system_metrics.prev_time = current_time
        sent_speed = 0
        recv_speed = 0
    else:
        time_diff = current_time - get_system_metrics.prev_time
        if time_diff > 0:
            sent_speed = (net_io.bytes_sent - get_system_metrics.prev_net_io.bytes_sent) / time_diff
            recv_speed = (net_io.bytes_recv - get_system_metrics.prev_net_io.bytes_recv) / time_diff
        else:
            sent_speed = 0
            recv_speed = 0
        
        get_system_metrics.prev_net_io = net_io
        get_system_metrics.prev_time = current_time
    
    network_metrics = {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'bytes_sent_human': format_bytes(net_io.bytes_sent),
        'bytes_recv_human': format_bytes(net_io.bytes_recv),
        'sent_speed': sent_speed,
        'recv_speed': recv_speed,
        'sent_speed_human': f"{sent_speed / 1024:.1f} KB/s",
        'recv_speed_human': f"{recv_speed / 1024:.1f} KB/s"
    }
    
    # Uptime
    uptime_seconds = int(time.time() - psutil.boot_time())
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    # GPU metrics
    gpu_metrics = get_gpu_metrics()
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'uptime': uptime_str,
        'network': network_metrics,
        'gpu_metrics': gpu_metrics,
        'platform': {
            'system': platform.system(),
            'machine': platform.machine(),
            'is_jetson': is_jetson()
        },
        'memory_pressure': memory_pressure_metrics,
        'thermal_status': thermal_status
    }

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/metrics')
def metrics():
    """Return system metrics as JSON response."""
    return jsonify(get_system_metrics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True) 