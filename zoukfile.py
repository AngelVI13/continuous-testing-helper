import sys

if sys.platform.startswith("win"):
    PYTHON_CMD = "py -3"
else:
    PYTHON_CMD = "python3"

commands = {
    "black": PYTHON_CMD + " -m black {changed_files}",
    "flake8": PYTHON_CMD + " -m flake8 {changed_files} --max-line-length=100",
    "mypy": PYTHON_CMD + " -m mypy {changed_files}",
    "doctest": PYTHON_CMD + " -m doctest {changed_files}",
    "pytest": PYTHON_CMD + " -m pytest tests/",
}
