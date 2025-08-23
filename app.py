from datetime import datetime
import subprocess
import platform
import time
import logging

from flask import Flask, render_template, jsonify
import psutil
import pynvml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TEGRASTATS_INTERVAL = 1000
MEMORY_PRESSURE_WEIGHTS = {
    'memory_usage': 0.7,
    'swap_usage': 0.2,
    'available': 0.1
}
LOW_MEMORY_THRESHOLD = 50
LOW_SWAP_THRESHOLD = 20
MAX_PRESSURE_CAP = 50
BYTES_PER_MB = 1024 * 1024
BYTES_PER_KB = 1024
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60

app = Flask(__name__, static_folder='static')

def is_jetson():
    """Check if the system is a Jetson device."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().lower()
            return 'jetson' in model
    except (FileNotFoundError, PermissionError, OSError):
        return False

def parse_tegrastats_value(stats, key, unit=''):
    """Parse a value from tegrastats output."""
    try:
        if key in stats:
            part = stats.split(key)[1].split(unit)[0].strip()
            return float(part)
    except (ValueError, IndexError):
        logger.debug(f"Could not parse {key} value from tegrastats output")
    return None

def get_jetson_gpu_metrics():
    """Get GPU metrics using tegrastats for Jetson devices."""
    try:
        # Use Popen to start tegrastats and pipe its output
        tegrastats_process = subprocess.Popen(
            ['tegrastats', '--interval', str(TEGRASTATS_INTERVAL)], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Read the first line of output
        stats = tegrastats_process.stdout.readline().strip()
        logger.debug("Processing tegrastats line: %s", stats)
        
        # Terminate the process
        tegrastats_process.terminate()
        tegrastats_process.wait(timeout=1)
        
        metrics = {}
        
        # Extract GR3D_FREQ (GPU usage)
        gpu_util = parse_tegrastats_value(stats, 'GR3D_FREQ', '%')
        if gpu_util is not None:
            metrics['gpu_utilization'] = gpu_util
        
        # Extract temperatures
        gpu_temp = parse_tegrastats_value(stats, 'gpu@', 'C')
        if gpu_temp is not None:
            metrics['gpu_temperature'] = gpu_temp
        
        cpu_temp = parse_tegrastats_value(stats, 'cpu@', 'C')
        if cpu_temp is not None:
            metrics['cpu_temperature'] = cpu_temp
        
        # Extract power information
        total_power = parse_tegrastats_value(stats, 'VDD_IN', 'mW')
        if total_power is not None:
            metrics['total_power'] = total_power
        
        gpu_power = parse_tegrastats_value(stats, 'VDD_CPU_GPU_CV', 'mW')
        if gpu_power is not None:
            metrics['gpu_power'] = gpu_power
        
        # Extract RAM information
        if 'RAM' in stats:
            try:
                ram_part = stats.split('RAM')[1].split('MB')[0].strip()
                used, total = ram_part.split('/')
                metrics['ram_used'] = float(used)
                metrics['ram_total'] = float(total)
                metrics['ram_percent'] = (float(used) / float(total)) * 100
            except (ValueError, IndexError):
                logger.debug("Could not parse RAM information from tegrastats")
        
        # Extract CPU usage for each core
        if 'CPU [' in stats:
            try:
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
            except (ValueError, IndexError):
                logger.debug("Could not parse CPU information from tegrastats")
        
        return metrics
            
    except (subprocess.SubprocessError, ValueError) as e:
        logger.error("Error getting Jetson GPU metrics: %s", str(e))
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
            'gpu_memory_used': info.used / BYTES_PER_MB,  # Convert to MB
            'gpu_memory_total': info.total / BYTES_PER_MB  # Convert to MB
        }
    except pynvml.NVMLError as e:
        logger.error("Error getting NVIDIA GPU metrics: %s", str(e))
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

def calculate_memory_pressure(memory, swap):
    """Calculate memory pressure score based on memory and swap usage."""
    # Calculate memory pressure score (0-100)
    # Factors: memory usage, swap usage, and available memory
    memory_usage_component = memory.percent * MEMORY_PRESSURE_WEIGHTS['memory_usage']
    swap_component = swap.percent * MEMORY_PRESSURE_WEIGHTS['swap_usage']
    available_component = (100 - (memory.available / memory.total * 100)) * MEMORY_PRESSURE_WEIGHTS['available']
    
    logger.debug("Memory pressure components: Memory=%.1f, Swap=%.1f, Available=%.1f",
                memory_usage_component, swap_component, available_component)
    
    memory_pressure = memory_usage_component + swap_component + available_component
    
    # Cap the pressure at 100 and ensure it's not negative
    memory_pressure = min(100, max(0, memory_pressure))
    
    # If memory usage is low (< 50%) and swap usage is low (< 20%), 
    # cap the pressure at 50 to better reflect system state
    if memory.percent < LOW_MEMORY_THRESHOLD and swap.percent < LOW_SWAP_THRESHOLD:
        memory_pressure = min(memory_pressure, MAX_PRESSURE_CAP)
        logger.debug("Low memory and swap usage detected, capping pressure at %d", MAX_PRESSURE_CAP)
    
    logger.debug("Final pressure score: %.1f", memory_pressure)
    return round(memory_pressure, 1)

def get_memory_pressure_metrics():
    """Get memory pressure and swap metrics."""
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Debug logging
        logger.debug("Memory: %.1f%% used, %.1f MB available", 
                    memory.percent, memory.available / BYTES_PER_MB)
        logger.debug("Swap: %.1f%% used, %.1f MB used", 
                    swap.percent, swap.used / BYTES_PER_MB)
        
        memory_pressure = calculate_memory_pressure(memory, swap)
        
        return {
            'memory_pressure': memory_pressure,
            'swap': {
                'used': swap.used / BYTES_PER_MB,  # Convert to MB
                'total': swap.total / BYTES_PER_MB,  # Convert to MB
                'percent': swap.percent,
                'free': swap.free / BYTES_PER_MB  # Convert to MB
            },
            'memory': {
                'available': memory.available / BYTES_PER_MB,  # Convert to MB
                'total': memory.total / BYTES_PER_MB,  # Convert to MB
                'percent': memory.percent
            }
        }
    except Exception as e:
        logger.error("Error getting memory pressure metrics: %s", str(e))
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
            tegrastats_process = subprocess.Popen(
                ['tegrastats', '--interval', str(TEGRASTATS_INTERVAL)], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
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
            except (FileNotFoundError, PermissionError, ValueError):
                return {
                    'cpu_throttled': False,
                    'gpu_throttled': False,
                    'status': 'Unknown'
                }
    except Exception as e:
        logger.error("Error getting thermal throttling status: %s", str(e))
        return {
            'cpu_throttled': False,
            'gpu_throttled': False,
            'status': 'Error'
        }

def format_bytes(bytes_value):
    """Format bytes into human readable format with appropriate units."""
    if bytes_value >= BYTES_PER_MB * 1024:  # GB
        return f"{bytes_value / (BYTES_PER_MB * 1024):.2f} GB"
    elif bytes_value >= BYTES_PER_MB:  # MB
        return f"{bytes_value / BYTES_PER_MB:.1f} MB"
    elif bytes_value >= BYTES_PER_KB:  # KB
        return f"{bytes_value / BYTES_PER_KB:.1f} KB"
    else:
        return f"{bytes_value} B"

def format_uptime(uptime_seconds):
    """Format uptime in seconds to human readable format."""
    hours = uptime_seconds // SECONDS_PER_HOUR
    minutes = (uptime_seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE
    seconds = uptime_seconds % SECONDS_PER_MINUTE
    return f"{hours}h {minutes}m {seconds}s"

def get_network_metrics():
    """Get network metrics including throughput calculation."""
    net_io = psutil.net_io_counters()
    current_time = time.time()
    
    # Calculate network throughput if we have previous values
    if not hasattr(get_network_metrics, 'prev_net_io'):
        get_network_metrics.prev_net_io = net_io
        get_network_metrics.prev_time = current_time
        sent_speed = 0
        recv_speed = 0
    else:
        time_diff = current_time - get_network_metrics.prev_time
        if time_diff > 0:
            sent_speed = (net_io.bytes_sent - get_network_metrics.prev_net_io.bytes_sent) / time_diff
            recv_speed = (net_io.bytes_recv - get_network_metrics.prev_net_io.bytes_recv) / time_diff
        else:
            sent_speed = 0
            recv_speed = 0
        
        get_network_metrics.prev_net_io = net_io
        get_network_metrics.prev_time = current_time
    
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'bytes_sent_human': format_bytes(net_io.bytes_sent),
        'bytes_recv_human': format_bytes(net_io.bytes_recv),
        'sent_speed': sent_speed,
        'recv_speed': recv_speed,
        'sent_speed_human': f"{sent_speed / BYTES_PER_KB:.1f} KB/s",
        'recv_speed_human': f"{recv_speed / BYTES_PER_KB:.1f} KB/s"
    }

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
    network_metrics = get_network_metrics()
    
    # Uptime
    uptime_seconds = int(time.time() - psutil.boot_time())
    uptime_str = format_uptime(uptime_seconds)
    
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