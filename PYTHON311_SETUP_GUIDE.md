# Python 3.11 Installation Guide for Trading System

## Why Python 3.11?

Python 3.11 is the most stable version for trading systems because:
- Excellent package compatibility
- Stable NumPy, Pandas, SQLAlchemy support
- Good performance
- Wide ecosystem support

## Installation Steps

### Windows:
1. Download Python 3.11 from: https://www.python.org/downloads/release/python-3118/
2. Choose "Windows installer (64-bit)"
3. Run installer with "Add Python to PATH" checked
4. Verify installation: `python --version`

### macOS:
```bash
# Using Homebrew
brew install python@3.11

# Or download from python.org
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

## Setting up Virtual Environment

After installing Python 3.11:

```bash
# Create new virtual environment
python3.11 -m venv .venv311

# Activate (Windows)
.venv311\Scripts\activate

# Activate (Linux/macOS)
source .venv311/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements_python311.txt
```

## Verify Installation

```bash
python --version  # Should show Python 3.11.x
pip list  # Check installed packages
```

## Troubleshooting

If you still have issues:
1. Delete the old .venv folder
2. Create new virtual environment with Python 3.11
3. Reinstall all packages
4. Run: python test_imports.py
