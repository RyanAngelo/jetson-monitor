from flask import Flask, render_template, jsonify
import psutil
import pynvml
import os
import time
from datetime import datetime

app = Flask(__name__)

# Initialize NVML for GPU monitoring
try:
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False

def get_system_metrics():
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
                'gpu_utilization': gpu_utilization.gpu
            }
        except:
            gpu_metrics = {'error': 'Failed to get GPU metrics'}
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'gpu_metrics': gpu_metrics
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/metrics')
def metrics():
    return jsonify(get_system_metrics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 