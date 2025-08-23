.PHONY: test test-verbose test-coverage test-unit test-integration clean install-test-deps

# Default target
test:
	python run_tests.py

# Run tests with verbose output
test-verbose:
	python run_tests.py -v

# Run tests with coverage report
test-coverage:
	python run_tests.py --coverage

# Run only unit tests
test-unit:
	python -c "import sys; sys.path.insert(0, '.'); from tests.test_app import TestApp; import unittest; unittest.main(argv=[''], exit=False, verbosity=2)"

# Run only integration tests
test-integration:
	python -c "import sys; sys.path.insert(0, '.'); from tests.test_integration import TestIntegration; import unittest; unittest.main(argv=[''], exit=False, verbosity=2)"

# Install test dependencies
install-test-deps:
	pip install -r requirements-test.txt

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .coverage

# Run the application
run:
	python app.py

# Help
help:
	@echo "Available commands:"
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  test-unit         - Run only unit tests"
	@echo "  test-integration  - Run only integration tests"
	@echo "  install-test-deps - Install test dependencies"
	@echo "  clean             - Clean up generated files"
	@echo "  run               - Run the application"
	@echo "  help              - Show this help message"
