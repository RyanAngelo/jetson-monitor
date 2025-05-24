from datetime import datetime
import subprocess
import platform
import os

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
        
        # Extract GR3D_FREQ (GPU usage)
        if 'GR3D_FREQ' in stats:
            # Split on GR3D_FREQ and get the part after it
            gpu_part = stats.split('GR3D_FREQ')[1].split('%')[0].strip()
            print("Extracted GPU part:", gpu_part)  # Debug print
            try:
                gpu_util = float(gpu_part)
                print("Parsed GPU utilization:", gpu_util)  # Debug print
                return {
                    'gpu_utilization': gpu_util,
                    'gpu_memory_percent': gpu_util,
                    'gpu_memory_used': 0,
                    'gpu_memory_total': 0
                }
            except ValueError as e:
                print(f"Could not parse GPU value: {gpu_part}, error: {str(e)}")
        else:
            print("No GR3D_FREQ found in output")
            
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
    
    # GPU metrics
    gpu_metrics = get_gpu_metrics()
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
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