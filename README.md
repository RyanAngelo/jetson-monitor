# Jetson Orin Nano Monitor

A real-time web-based monitoring dashboard for Jetson Orin Nano devices. This application provides a comprehensive interface to monitor system resources, performance metrics, and thermal status.

## Features

### System Monitoring
- CPU usage and temperature
- Memory usage and pressure indicators
- Swap space utilization
- Disk space monitoring
- Network throughput (sent/received)
- System uptime tracking

### GPU Monitoring
- GPU utilization
- GPU temperature
- GPU power consumption
- Total system power draw

### Thermal Management
- Real-time thermal status monitoring
- CPU and GPU throttling detection
- Visual indicators for thermal states
- Detailed thermal event reporting

### Memory Management
- Memory pressure scoring
- Swap usage monitoring
- Memory availability tracking
- Visual pressure indicators

### Visualization
- Real-time interactive charts
- Historical data tracking
- Configurable update intervals (1-60 seconds)
- Color-coded status indicators

### User Interface
- Modern, responsive dark theme
- Mobile-friendly design
- Real-time metric updates
- Intuitive layout

## Requirements

- Python 3.6 or higher
- Jetson Orin Nano with NVIDIA drivers installed
- Required Python packages:
  - Flask 3.0.2
  - psutil 5.9.8
  - nvidia-ml-py3 7.352.0

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd jetson-monitor
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
.\venv\Scripts\activate  # On Windows
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the monitoring server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5005
```

3. The dashboard will automatically start displaying system metrics. You can adjust the update interval using the control panel at the top of the page.

## Features in Detail

### Memory Pressure Monitoring
- Pressure score (0-100) based on:
  - Memory usage (60% weight)
  - Swap usage (30% weight)
  - Available memory (10% weight)
- Color-coded indicators:
  - Green: Low pressure (≤ 30)
  - Yellow: Moderate pressure (31-70)
  - Red: High pressure (> 70)

### Thermal Monitoring
- Real-time thermal status tracking
- CPU and GPU throttling detection
- Status indicators:
  - Normal: Green
  - Throttled: Red
  - Unknown: Yellow
  - Error: Grey

### Network Monitoring
- Real-time throughput tracking
- Sent and received data rates
- Historical network usage charts
- Human-readable data units

## Project Structure

```
jetson-monitor/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Stylesheet
│   └── js/
│       └── monitor.js # Frontend logic
└── templates/
    └── index.html     # Main dashboard template
```

## Notes

- The application requires NVIDIA Management Library (NVML) for GPU monitoring
- Default update interval is 1 second, adjustable between 1 and 60 seconds
- Charts display the last 60 data points by default
- Memory pressure scoring is weighted to prioritize memory usage and swap utilization
- Thermal monitoring is optimized for Jetson devices but works on other systems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details
