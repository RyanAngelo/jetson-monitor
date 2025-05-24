from datetime import datetime

from flask import Flask, render_template, jsonify
import psutil
import pynvml

app = Flask(__name__)

# Initialize NVML for GPU monitoring
try:
    pynvml.nvmlInit()
    device_count = pynvml.nvmlDeviceGetCount()
    if device_count > 0:
        GPU_AVAILABLE = True
        print(f"Found {device_count} NVIDIA GPU(s)")
    else:
        GPU_AVAILABLE = False
        print("No NVIDIA GPUs found")
except pynvml.NVMLError as e:
    GPU_AVAILABLE = False
    print(f"NVML initialization failed: {str(e)}")

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
    gpu_metrics = {}
    if GPU_AVAILABLE:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_metrics = {
                'gpu_memory_percent': (info.used / info.total) * 100,
                'gpu_utilization': gpu_utilization.gpu,
                'gpu_memory_used': info.used / (1024 * 1024),  # Convert to MB
                'gpu_memory_total': info.total / (1024 * 1024)  # Convert to MB
            }
        except pynvml.NVMLError as e:
            gpu_metrics = {'error': f'Failed to get GPU metrics: {str(e)}'}
            print(f"GPU metrics error: {str(e)}")
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'gpu_metrics': gpu_metrics
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