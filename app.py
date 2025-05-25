from datetime import datetime
import subprocess
import platform
import os
import time

from flask import Flask, render_template, jsonify
import psutil
import pynvml

app = Flask(__name__)

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

def get_system_metrics():
    """Collect and return system metrics including CPU, memory, disk, and GPU usage."""
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory metrics
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Disk metrics
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
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
        'gpu_metrics': gpu_metrics,
        'platform': {
            'system': platform.system(),
            'machine': platform.machine(),
            'is_jetson': is_jetson()
        }
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