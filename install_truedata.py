#!/usr/bin/env python3
"""
TrueData Installation Script for Trading System
Automates TrueData installation and setup
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

def check_python_version():
    """Check if Python version is compatible"""
    print(f"Python version: {sys.version}")
    
    if sys.version_info >= (3, 13):
        print("[WARNING] Python 3.13 detected - may have compatibility issues")
        print("[INFO] Recommended: Use Python 3.11 for best compatibility")
        return False
    elif sys.version_info >= (3, 11) and sys.version_info < (3, 12):
        print("[SUCCESS] Python 3.11 detected - perfect for TrueData")
        return True
    else:
        print("[WARNING] Python version may have compatibility issues")
        return False

def check_pip():
    """Check if pip is available"""
    print("[INFO] Checking pip availability...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"[SUCCESS] pip is available: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("[ERROR] pip is not available")
        return False

def install_truedata_packages():
    """Install TrueData packages"""
    print("[INFO] Installing TrueData packages...")
    
    packages = [
        "truedata-ws",
        "websocket-client",
        "redis",
        "pandas",
        "numpy"
    ]
    
    success_count = 0
    total_packages = len(packages)
    
    for package in packages:
        print(f"[INFO] Installing {package}...")
        if run_command(f"{sys.executable} -m pip install {package}", f"Installing {package}"):
            success_count += 1
        else:
            print(f"[WARNING] Failed to install {package}")
    
    print(f"[INFO] Package installation: {success_count}/{total_packages} successful")
    return success_count == total_packages

def create_env_template():
    """Create .env template file"""
    print("[INFO] Creating .env template...")
    
    env_content = """# TrueData Configuration
TRUEDATA_USERNAME=your_username
TRUEDATA_PASSWORD=your_password
TRUEDATA_LIVE_PORT=8084
TRUEDATA_URL=push.truedata.in
TRUEDATA_LOG_LEVEL=INFO
TRUEDATA_IS_SANDBOX=false

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/trading_system

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/trading_system.log

# Security Configuration
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
"""
    
    try:
        with open(".env.template", "w", encoding='utf-8') as f:
            f.write(env_content)
        print("[SUCCESS] .env.template created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .env.template: {e}")
        return False

def create_test_script():
    """Create a simple test script"""
    print("[INFO] Creating test script...")
    
    test_content = """#!/usr/bin/env python3
\"\"\"
Quick TrueData Test Script
\"\"\"

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    \"\"\"Test TrueData import\"\"\"
    try:
        from truedata_ws import TD_live, TD_hist
        print("✅ TrueData WebSocket package imported successfully")
        return True
    except ImportError:
        try:
            from truedata import TD_live, TD_hist
            print("✅ TrueData legacy package imported successfully")
            return True
        except ImportError:
            print("❌ TrueData not installed")
            print("💡 Install with: pip install truedata-ws")
            return False

def test_config():
    \"\"\"Test configuration\"\"\"
    try:
        from config.truedata_config import get_config
        config = get_config()
        print("✅ Configuration loaded successfully")
        return True
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False

def test_provider():
    \"\"\"Test provider import\"\"\"
    try:
        from data.truedata_provider import TrueDataProvider
        print("✅ TrueData provider imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Provider import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Quick TrueData Test")
    print("=" * 30)
    
    import_success = test_import()
    config_success = test_config()
    provider_success = test_provider()
    
    success_count = sum([import_success, config_success, provider_success])
    total_tests = 3
    
    print(f"\\n🎯 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! TrueData is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the installation.")
"""
    
    try:
        with open("quick_test_truedata.py", "w", encoding='utf-8') as f:
            f.write(test_content)
        print("[SUCCESS] quick_test_truedata.py created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create test script: {e}")
        return False

def create_requirements_truedata():
    """Create requirements file for TrueData"""
    print("[INFO] Creating requirements_truedata.txt...")
    
    requirements = """# TrueData Dependencies
truedata-ws>=1.0.0
websocket-client>=1.8.0
redis>=5.0.1
pandas>=2.1.4
numpy>=1.24.3

# Additional dependencies for trading system
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.23
alembic>=1.13.1
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
requests>=2.31.0
pydantic>=2.11.7
"""
    
    try:
        with open("requirements_truedata.txt", "w", encoding='utf-8') as f:
            f.write(requirements)
        print("[SUCCESS] requirements_truedata.txt created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create requirements: {e}")
        return False

def create_setup_batch():
    """Create Windows batch setup script"""
    print("[INFO] Creating Windows setup script...")
    
    batch_content = """@echo off
REM TrueData Setup Script for Windows

echo Setting up TrueData for trading system...

REM Check Python
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11 first.
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install TrueData dependencies
echo Installing TrueData dependencies...
pip install -r requirements_truedata.txt

REM Install TrueData
echo Installing TrueData...
pip install truedata-ws

REM Test installation
echo Testing installation...
python quick_test_truedata.py

echo Setup complete!
echo Next steps:
echo 1. Copy .env.template to .env
echo 2. Update .env with your TrueData credentials
echo 3. Run: python test_truedata.py
pause
"""
    
    try:
        with open("setup_truedata.bat", "w", encoding='utf-8') as f:
            f.write(batch_content)
        print("[SUCCESS] setup_truedata.bat created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create batch script: {e}")
        return False

def create_setup_shell():
    """Create Linux/macOS shell setup script"""
    print("[INFO] Creating shell setup script...")
    
    shell_content = """#!/bin/bash
# TrueData Setup Script for Linux/macOS

echo "Setting up TrueData for trading system..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.11 first."
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install TrueData dependencies
echo "Installing TrueData dependencies..."
pip3 install -r requirements_truedata.txt

# Install TrueData
echo "Installing TrueData..."
pip3 install truedata-ws

# Test installation
echo "Testing installation..."
python3 quick_test_truedata.py

echo "Setup complete!"
echo "Next steps:"
echo "1. Copy .env.template to .env"
echo "2. Update .env with your TrueData credentials"
echo "3. Run: python3 test_truedata.py"
"""
    
    try:
        with open("setup_truedata.sh", "w", encoding='utf-8') as f:
            f.write(shell_content)
        os.chmod("setup_truedata.sh", 0o755)
        print("[SUCCESS] setup_truedata.sh created")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create shell script: {e}")
        return False

def run_quick_test():
    """Run a quick test after installation"""
    print("[INFO] Running quick test...")
    
    try:
        result = subprocess.run([sys.executable, "quick_test_truedata.py"], 
                              capture_output=True, text=True, check=True)
        print("[SUCCESS] Quick test passed")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Quick test failed: {e.stderr}")
        return False

def main():
    """Main installation function"""
    print("🚀 TrueData Installation for Trading System")
    print("=" * 50)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check pip
    pip_ok = check_pip()
    
    if not pip_ok:
        print("[ERROR] pip is required for installation")
        return
    
    # Install packages
    packages_ok = install_truedata_packages()
    
    # Create files
    env_ok = create_env_template()
    test_ok = create_test_script()
    req_ok = create_requirements_truedata()
    
    # Create setup scripts
    if platform.system() == "Windows":
        batch_ok = create_setup_batch()
        shell_ok = True  # Not needed on Windows
    else:
        shell_ok = create_setup_shell()
        batch_ok = True  # Not needed on Linux/macOS
    
    # Run quick test
    test_result = run_quick_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Installation Summary:")
    print(f"   ✅ Python Version: {python_ok}")
    print(f"   ✅ pip Available: {pip_ok}")
    print(f"   ✅ Packages Installed: {packages_ok}")
    print(f"   ✅ .env Template: {env_ok}")
    print(f"   ✅ Test Script: {test_ok}")
    print(f"   ✅ Requirements: {req_ok}")
    print(f"   ✅ Windows Script: {batch_ok}")
    print(f"   ✅ Shell Script: {shell_ok}")
    print(f"   ✅ Quick Test: {test_result}")
    
    success_count = sum([python_ok, pip_ok, packages_ok, env_ok, test_ok, req_ok, batch_ok, shell_ok, test_result])
    total_checks = 9
    
    print(f"\n🎯 Overall: {success_count}/{total_checks} checks passed")
    
    if success_count >= 7:
        print("\n🎉 TrueData installation completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Copy .env.template to .env")
        print("   2. Update .env with your TrueData credentials:")
        print("      TRUEDATA_USERNAME=your_username")
        print("      TRUEDATA_PASSWORD=your_password")
        print("   3. Test with: python test_truedata.py")
        print("   4. Run integration test: python test_truedata_integration.py")
        print("\n📚 Documentation:")
        print("   - TRUEDATA_INSTALLATION_GUIDE.md")
        print("   - config/truedata_config.py")
        print("   - data/truedata_provider.py")
    else:
        print("\n❌ Installation had issues. Check the errors above.")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure Python 3.11 is installed")
        print("   2. Check internet connection")
        print("   3. Try: pip install --upgrade pip")
        print("   4. Run: python install_truedata.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Installation interrupted by user")
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        import traceback
        traceback.print_exc() 