# Jetson Monitor

A real-time web-based monitoring dashboard for Jetson devices. This application provides a comprehensive interface to monitor system resources, performance metrics, and thermal status.

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
- Jetson device with NVIDIA drivers installed
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
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── requirements-test.txt  # Test dependencies
├── run_tests.py          # Test runner script
├── Makefile              # Build and test commands
├── pytest.ini           # pytest configuration
├── static/
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       ├── charts.js     # Chart functionality
│       └── monitor.js    # Frontend logic
├── templates/
│   └── index.html        # Main dashboard template
└── tests/
    ├── __init__.py       # Tests package
    ├── test_app.py       # Unit tests
    ├── test_integration.py # Integration tests
    └── README.md         # Test documentation
```

## Notes

- The application requires NVIDIA Management Library (NVML) for GPU monitoring
- Default update interval is 1 second, adjustable between 1 and 60 seconds
- Charts display the last 60 data points by default
- Memory pressure scoring is weighted to prioritize memory usage and swap utilization
- Thermal monitoring is optimized for Jetson devices but works on other systems

## Testing

The project includes a comprehensive test suite with both unit and integration tests.

### Running Tests

#### Using Make (Recommended)
```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage report
make test-coverage

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration
```

#### Using the Test Runner
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run with coverage report
python run_tests.py --coverage
```

#### Using pytest (if installed)
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Coverage

The test suite covers:
- **Unit Tests**: All major functions with mocked dependencies
- **Integration Tests**: Flask application endpoints and JSON responses
- **Error Handling**: Various error conditions and edge cases
- **Platform Compatibility**: Both Jetson and non-Jetson systems

For detailed test documentation, see [tests/README.md](tests/README.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Guidelines

1. **Write Tests**: All new features should include appropriate tests
2. **Run Tests**: Ensure all tests pass before submitting changes
3. **Follow Style**: Use the existing code style and patterns
4. **Documentation**: Update documentation for any new features

## License

MIT License - See LICENSE file for details
