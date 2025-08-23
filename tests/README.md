# Test Suite for Jetson Monitor

This directory contains the comprehensive test suite for the Jetson Monitor application.

## Test Structure

### Unit Tests (`test_app.py`)
- **Purpose**: Test individual functions and components in isolation
- **Coverage**: All major functions in `app.py`
- **Mocking**: Uses `unittest.mock` to mock external dependencies
- **Key Areas Tested**:
  - Platform detection (`is_jetson()`)
  - GPU metrics collection (Jetson and NVIDIA)
  - Memory pressure calculations
  - Thermal throttling detection
  - Data formatting functions
  - Network metrics calculation
  - System metrics aggregation
  - Flask route handlers

### Integration Tests (`test_integration.py`)
- **Purpose**: Test the Flask application as a whole
- **Coverage**: HTTP endpoints and JSON responses
- **Key Areas Tested**:
  - `/` route (index page)
  - `/metrics` route (JSON API)
  - Response formats and data types
  - Error handling (404, 405)
  - Data consistency across requests

## Running Tests

### Using the Test Runner Script
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run with coverage report
python run_tests.py --coverage

# Run specific test patterns
python run_tests.py -p "*gpu*"
```

### Using pytest (Recommended)
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/test_app.py

# Run only integration tests
pytest tests/test_integration.py

# Run with verbose output
pytest -v

# Run specific test functions
pytest -k "test_is_jetson"
```

### Using unittest directly
```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_app

# Run specific test class
python -m unittest tests.test_app.TestApp

# Run specific test method
python -m unittest tests.test_app.TestApp.test_is_jetson_true
```

## Test Coverage

The test suite aims to cover:

- **Function Coverage**: All public functions are tested
- **Branch Coverage**: Both success and error paths are tested
- **Platform Coverage**: Tests for both Jetson and non-Jetson systems
- **Error Handling**: Tests for various error conditions
- **Edge Cases**: Boundary conditions and unusual inputs

## Mocking Strategy

The unit tests use extensive mocking to:

1. **Isolate Units**: Test functions without external dependencies
2. **Control Environment**: Simulate different system states
3. **Test Error Conditions**: Simulate failures and exceptions
4. **Speed Up Tests**: Avoid slow system calls

### Key Mocked Components:
- `subprocess.Popen` for tegrastats calls
- `psutil` functions for system metrics
- `pynvml` for NVIDIA GPU metrics
- File system operations (`open`)
- Time functions for consistent testing

## Adding New Tests

### For New Functions:
1. Add test methods to `TestApp` class in `test_app.py`
2. Follow naming convention: `test_function_name_scenario`
3. Include both success and error cases
4. Mock external dependencies appropriately

### For New Routes:
1. Add test methods to `TestIntegration` class in `test_integration.py`
2. Test HTTP status codes, content types, and response formats
3. Test error conditions (404, 405, etc.)

### Test Guidelines:
- Use descriptive test names
- Test one thing per test method
- Include docstrings explaining test purpose
- Use appropriate assertions
- Clean up any test state in `tearDown()` if needed

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- No external dependencies required (all mocked)
- Fast execution (typically < 5 seconds)
- Deterministic results
- Clear pass/fail indicators

## Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure you're running from the project root
2. **Mock Issues**: Check that mocks are applied to the correct module path
3. **Platform Differences**: Tests should work on any platform due to mocking
4. **Flask Context**: Integration tests use Flask's test client

### Debugging Tests:
```bash
# Run with maximum verbosity
pytest -vvv

# Run single test with print statements
pytest -s -k "test_name"

# Run with debugger
pytest --pdb
```
