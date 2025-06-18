#!/usr/bin/env python3
"""
Python 3.11 Setup Script for Trading System (Windows Compatible)
Fixes compatibility issues by downgrading to Python 3.11
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"[SUCCESS] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_current_python():
    """Check current Python version"""
    print(f"Python version: {sys.version}")
    if sys.version_info >= (3, 13):
        print("[WARNING] Python 3.13 detected - this will cause compatibility issues!")
        print("[INFO] Recommended: Use Python 3.11 for trading systems")
        return False
    elif sys.version_info >= (3, 11) and sys.version_info < (3, 12):
        print("[SUCCESS] Python 3.11 detected - this is perfect for trading systems!")
        return True
    else:
        print("[WARNING] Python version may have compatibility issues")
        return False

def create_python311_guide():
    """Create a guide for installing Python 3.11"""
    print("[INFO] Creating Python 3.11 installation guide...")
    
    guide_content = """# Python 3.11 Installation Guide for Trading System

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
.venv311\\Scripts\\activate

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
"""
    
    try:
        with open("PYTHON311_SETUP_GUIDE.md", "w", encoding='utf-8') as f:
            f.write(guide_content)
        print("[SUCCESS] Python 3.11 setup guide created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create guide: {e}")
        return False

def create_requirements_python311():
    """Create requirements.txt optimized for Python 3.11"""
    print("[INFO] Creating requirements.txt for Python 3.11...")
    
    requirements = """# Trading System Dependencies - Python 3.11 Optimized
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
asyncpg==0.29.0
greenlet==3.2.3

# Data Processing (Python 3.11 compatible versions)
pandas==2.1.4
numpy==1.24.3
scikit-learn==1.3.2
scipy==1.11.4
statsmodels==0.14.1

# Machine Learning
lightgbm==4.1.0
xgboost==2.0.3
joblib==1.3.2

# Technical Analysis
ta==0.10.2
yfinance==0.2.28

# Caching & Messaging
redis==5.0.1
celery==5.3.4
kombu==5.5.4
billiard==4.2.1
amqp==5.3.1

# WebSocket & Real-time
websockets==12.0
websocket-client==1.8.0
autobahn==19.11.2
twisted==25.5.0
txaio==23.1.1

# MQTT
paho-mqtt==2.1.0
asyncio-mqtt==0.16.1

# Authentication & Security
pydantic==2.11.7
passlib==1.7.4
python-jose==3.3.0
bcrypt==4.1.2
PyJWT==2.8.0

# HTTP & API
requests==2.31.0
python-multipart==0.0.6
aiofiles==23.2.1

# Monitoring & Logging
prometheus-client==0.19.0
structlog==23.2.0
rich==13.7.0

# Utilities
python-dotenv==1.0.0
tenacity==9.1.2
orjson==3.10.18
ujson==5.10.0
watchfiles==1.0.5

# Flask (for REST API)
flask==3.0.0
flask-cors==4.0.0
flask-limiter==3.5.0
flask-jwt-extended==4.6.0

# Visualization
plotly==5.18.0
kaleido==0.2.1

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy-extensions==1.1.0

# TrueData (may need manual installation)
# truedata-ws==1.0.0
"""
    
    try:
        with open("requirements_python311.txt", "w", encoding='utf-8') as f:
            f.write(requirements)
        print("[SUCCESS] requirements_python311.txt created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create requirements: {e}")
        return False

def create_setup_script():
    """Create setup script for Python 3.11"""
    print("[INFO] Creating Python 3.11 setup script...")
    
    if platform.system() == "Windows":
        script_content = """@echo off
REM Python 3.11 Setup Script for Trading System

echo Setting up trading system with Python 3.11...

REM Check if Python 3.11 is available
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11 first.
    echo See PYTHON311_SETUP_GUIDE.md for instructions.
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv311

REM Activate virtual environment
echo Activating virtual environment...
call .venv311\\Scripts\\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements_python311.txt

REM Install TrueData
echo Installing TrueData...
pip install truedata-ws

echo Setup complete!
echo To activate: .venv311\\Scripts\\activate.bat
pause
"""
        filename = "setup_python311.bat"
    else:
        script_content = """#!/bin/bash
# Python 3.11 Setup Script for Trading System

echo "Setting up trading system with Python 3.11..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: Python 3.11 not found. Please install Python 3.11 first."
    echo "See PYTHON311_SETUP_GUIDE.md for instructions."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv .venv311

# Activate virtual environment
echo "Activating virtual environment..."
source .venv311/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_python311.txt

# Install TrueData
echo "Installing TrueData..."
pip install truedata-ws

echo "Setup complete!"
echo "To activate: source .venv311/bin/activate"
"""
        filename = "setup_python311.sh"
    
    try:
        with open(filename, "w", encoding='utf-8') as f:
            f.write(script_content)
        if platform.system() != "Windows":
            os.chmod(filename, 0o755)
        print(f"[SUCCESS] {filename} created successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create setup script: {e}")
        return False

def create_migration_guide():
    """Create guide for migrating from Python 3.13 to 3.11"""
    print("[INFO] Creating migration guide...")
    
    migration_content = """# Migration Guide: Python 3.13 to Python 3.11

## Why Migrate?

Python 3.13 has compatibility issues with:
- NumPy (core data processing)
- SQLAlchemy (database ORM)
- Many scientific packages
- Some trading libraries

## Migration Steps

### 1. Install Python 3.11
Follow the instructions in PYTHON311_SETUP_GUIDE.md

### 2. Backup Current Environment
```bash
pip freeze > requirements_backup.txt
```

### 3. Create New Virtual Environment
```bash
# Windows
python -m venv .venv311
.venv311\\Scripts\\activate

# Linux/macOS
python3.11 -m venv .venv311
source .venv311/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements_python311.txt
```

### 5. Test Installation
```bash
python test_imports.py
```

### 6. Update IDE/Editor
- VS Code: Select Python 3.11 interpreter
- PyCharm: Configure Python 3.11 interpreter
- Jupyter: Install ipykernel for Python 3.11

## Package Compatibility

### Fully Compatible (Python 3.11)
- FastAPI, Uvicorn
- Pandas, NumPy
- SQLAlchemy, Alembic
- Redis, Celery
- All trading libraries

### May Need Updates
- Some newer packages
- Development tools

## Troubleshooting

### Common Issues:
1. Import errors: Reinstall packages
2. Path issues: Update PATH environment variable
3. IDE issues: Reconfigure Python interpreter

### Commands:
```bash
# Check Python version
python --version

# Check pip version
pip --version

# List installed packages
pip list

# Test imports
python -c "import numpy, pandas, sqlalchemy; print('All good!')"
```

## Benefits After Migration

- Stable NumPy operations
- Reliable SQLAlchemy
- Better package compatibility
- Faster development
- Fewer runtime errors
"""
    
    try:
        with open("MIGRATION_GUIDE.md", "w", encoding='utf-8') as f:
            f.write(migration_content)
        print("[SUCCESS] Migration guide created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create migration guide: {e}")
        return False

def test_python311_compatibility():
    """Test if current environment is Python 3.11 compatible"""
    print("[INFO] Testing Python 3.11 compatibility...")
    
    if not check_current_python():
        print("[ERROR] Current Python version is not compatible")
        return False
    
    # Test critical packages
    test_packages = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("sqlalchemy", "SQLAlchemy"),
        ("fastapi", "FastAPI"),
        ("redis", "Redis")
    ]
    
    success_count = 0
    total_packages = len(test_packages)
    
    for package, name in test_packages:
        try:
            __import__(package)
            print(f"[SUCCESS] {name} imported successfully")
            success_count += 1
        except ImportError as e:
            print(f"[ERROR] {name} import failed: {e}")
    
    print(f"[INFO] Compatibility test: {success_count}/{total_packages} packages working")
    return success_count == total_packages

def main():
    """Main function"""
    print("Python 3.11 Setup for Trading System")
    print("=" * 50)
    
    # Check current Python
    is_compatible = check_current_python()
    
    if not is_compatible:
        print("\n[WARNING] Current Python version has compatibility issues!")
        print("[INFO] Creating setup guides for Python 3.11...")
        
        # Create guides
        create_python311_guide()
        create_requirements_python311()
        create_setup_script()
        create_migration_guide()
        
        print("\n" + "=" * 50)
        print("[INFO] Next Steps:")
        print("   1. Install Python 3.11 (see PYTHON311_SETUP_GUIDE.md)")
        print("   2. Run setup script: setup_python311.bat (Windows) or setup_python311.sh (Linux/macOS)")
        print("   3. Test with: python test_imports.py")
        print("   4. If issues persist, see MIGRATION_GUIDE.md")
        print("=" * 50)
    else:
        print("\n[SUCCESS] Current Python version is compatible!")
        print("[INFO] Testing package compatibility...")
        test_python311_compatibility()
        
        print("\n" + "=" * 50)
        print("[SUCCESS] Your environment is ready for trading!")
        print("[INFO] You can now run your trading system")
        print("=" * 50)

if __name__ == "__main__":
    main() 