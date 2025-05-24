# Jetson Orin Nano Monitor

A real-time web-based monitoring dashboard for Jetson Orin Nano devices. This application provides a clean interface to monitor CPU usage, GPU usage, memory usage, and disk space utilization.

## Features

- Real-time monitoring of system metrics
- Configurable update interval (1-60 seconds)
- Interactive charts showing historical data
- Modern, responsive web interface
- GPU utilization monitoring using NVIDIA Management Library

## Requirements

- Python 3.6 or higher
- Jetson Orin Nano with NVIDIA drivers installed
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd jetson-monitor
```

2. Install the required packages:
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
http://localhost:5000
```

3. The dashboard will automatically start displaying system metrics. You can adjust the update interval using the control panel at the top of the page.

## Notes

- The application requires NVIDIA Management Library (NVML) for GPU monitoring. If NVML is not available, GPU metrics will not be displayed.
- The default update interval is 1 second, but you can adjust it between 1 and 60 seconds using the web interface.
- The chart displays the last 60 data points by default.

## License

MIT License
