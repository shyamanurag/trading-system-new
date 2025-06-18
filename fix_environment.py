#!/usr/bin/env python3
"""
Comprehensive Environment Fix Script
Fixes Python 3.13 compatibility issues and missing dependencies
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check Python version compatibility"""
    print(f"🐍 Python version: {sys.version}")
    if sys.version_info >= (3, 13):
        print("⚠️  Python 3.13 detected - some packages may need updates")
    return True

def upgrade_pip():
    """Upgrade pip to latest version"""
    return run_command(
        "python -m pip install --upgrade pip",
        "Upgrading pip"
    )

def fix_numpy_issue():
    """Fix NumPy compatibility with Python 3.13"""
    print("🔧 Fixing NumPy compatibility...")
    
    # First, uninstall current numpy
    run_command("pip uninstall numpy -y", "Uninstalling current NumPy")
    
    # Install numpy with specific version for Python 3.13
    success = run_command(
        "pip install numpy==1.26.4 --force-reinstall --no-cache-dir",
        "Installing NumPy 1.26.4"
    )
    
    if not success:
        # Try alternative approach
        print("🔄 Trying alternative NumPy installation...")
        run_command(
            "pip install --upgrade setuptools wheel",
            "Upgrading setuptools and wheel"
        )
        success = run_command(
            "pip install numpy --force-reinstall --no-cache-dir",
            "Installing latest NumPy"
        )
    
    return success

def fix_sqlalchemy_issue():
    """Fix SQLAlchemy compatibility"""
    print("🔧 Fixing SQLAlchemy compatibility...")
    
    # Uninstall current SQLAlchemy
    run_command("pip uninstall sqlalchemy -y", "Uninstalling current SQLAlchemy")
    
    # Install compatible version
    return run_command(
        "pip install sqlalchemy==2.0.23 --force-reinstall",
        "Installing SQLAlchemy 2.0.23"
    )

def install_missing_dependencies():
    """Install missing dependencies for the trading system"""
    print("📦 Installing missing dependencies...")
    
    dependencies = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "redis==5.0.1",
        "pandas==2.2.0",
        "numpy==1.26.4",
        "sqlalchemy==2.0.23",
        "alembic==1.13.1",
        "psycopg2-binary==2.9.9",
        "pydantic==2.11.7",
        "python-dotenv==1.0.0",
        "websockets==12.0",
        "aiofiles==23.2.1",
        "prometheus-client==0.19.0",
        "structlog==23.2.0",
        "tenacity==9.1.2",
        "python-multipart==0.0.6",
        "passlib==1.7.4",
        "python-jose==3.3.0",
        "bcrypt==4.1.2",
        "PyJWT==2.8.0",
        "requests==2.31.0",
        "yfinance==0.2.28",
        "ta==0.10.2",
        "scikit-learn==1.3.2",
        "scipy==1.11.4",
        "plotly==5.18.0",
        "kaleido==0.2.1",
        "lightgbm==4.1.0",
        "xgboost==2.0.3",
        "statsmodels==0.14.1",
        "joblib==1.3.2",
        "orjson==3.10.18",
        "ujson==5.10.0",
        "rich==13.7.0",
        "watchfiles==1.0.5",
        "flask==3.0.0",
        "flask-cors==4.0.0",
        "flask-limiter==3.5.0",
        "flask-jwt-extended==4.6.0",
        "gunicorn==21.2.0",
        "celery==5.3.4",
        "kombu==5.5.4",
        "billiard==4.2.1",
        "amqp==5.3.1",
        "twisted==25.5.0",
        "autobahn==19.11.2",
        "txaio==23.1.1",
        "websocket-client==1.8.0",
        "paho-mqtt==2.1.0",
        "asyncio-mqtt==0.16.1",
        "asyncpg==0.29.0",
        "greenlet==3.2.3",
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1",
        "black==23.11.0",
        "flake8==6.1.0",
        "mypy-extensions==1.1.0"
    ]
    
    success_count = 0
    total_deps = len(dependencies)
    
    for dep in dependencies:
        if run_command(f"pip install {dep}", f"Installing {dep}"):
            success_count += 1
    
    print(f"📊 Dependencies installed: {success_count}/{total_deps}")
    return success_count == total_deps

def install_truedata():
    """Install TrueData package"""
    print("📦 Installing TrueData...")
    
    # Try multiple sources for TrueData
    sources = [
        "pip install truedata",
        "pip install truedata-ws",
        "pip install git+https://github.com/truedata/truedata-python.git"
    ]
    
    for source in sources:
        if run_command(source, f"Installing TrueData from {source}"):
            return True
    
    print("⚠️  TrueData installation failed - you may need to install manually")
    return False

def create_requirements_file():
    """Create a requirements.txt file with all dependencies"""
    print("📝 Creating requirements.txt...")
    
    requirements = """# Trading System Dependencies
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

# Data Processing
pandas==2.2.0
numpy==1.26.4
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
# truedata
# truedata-ws
"""
    
    try:
        with open("requirements.txt", "w") as f:
            f.write(requirements)
        print("✅ requirements.txt created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create requirements.txt: {e}")
        return False

def test_imports():
    """Test critical imports"""
    print("🧪 Testing critical imports...")
    
    test_imports = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("sqlalchemy", "SQLAlchemy"),
        ("fastapi", "FastAPI"),
        ("redis", "Redis"),
        ("websockets", "WebSockets"),
        ("pydantic", "Pydantic"),
        ("sklearn", "Scikit-learn"),
        ("plotly", "Plotly")
    ]
    
    success_count = 0
    total_imports = len(test_imports)
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} imported successfully")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name} import failed: {e}")
    
    print(f"📊 Import tests: {success_count}/{total_imports} passed")
    return success_count == total_imports

def create_environment_script():
    """Create a setup script for easy environment recreation"""
    print("📝 Creating environment setup script...")
    
    script_content = """#!/bin/bash
# Environment Setup Script for Trading System

echo "🚀 Setting up trading system environment..."

# Create virtual environment
python -m venv .venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install TrueData (if available)
pip install truedata-ws || echo "TrueData installation failed - install manually"

echo "✅ Environment setup complete!"
echo "To activate: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)"
"""
    
    try:
        with open("setup_env.sh", "w") as f:
            f.write(script_content)
        os.chmod("setup_env.sh", 0o755)
        print("✅ setup_env.sh created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create setup script: {e}")
        return False

def main():
    """Main environment fix function"""
    print("🔧 Trading System Environment Fix")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Upgrade pip
    upgrade_pip()
    
    # Fix NumPy issue
    if not fix_numpy_issue():
        print("⚠️  NumPy fix failed - continuing with other fixes")
    
    # Fix SQLAlchemy issue
    if not fix_sqlalchemy_issue():
        print("⚠️  SQLAlchemy fix failed - continuing with other fixes")
    
    # Install missing dependencies
    install_missing_dependencies()
    
    # Install TrueData
    install_truedata()
    
    # Create requirements file
    create_requirements_file()
    
    # Create setup script
    create_environment_script()
    
    # Test imports
    print("\n" + "=" * 50)
    print("🧪 Final Import Tests")
    print("=" * 50)
    test_imports()
    
    print("\n" + "=" * 50)
    print("✅ Environment fix completed!")
    print("📝 Next steps:")
    print("   1. Run: pip install -r requirements.txt")
    print("   2. Test your application")
    print("   3. If issues persist, try: python fix_environment.py")
    print("=" * 50)

if __name__ == "__main__":
    main() 