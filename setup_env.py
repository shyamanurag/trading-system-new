#!/usr/bin/env python3
"""
Environment Setup Script for Trading System
Creates virtual environment and installs all dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"📦 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   Details: {e.stderr.strip()}")
        return False

def main():
    """Setup the development environment."""
    print("🚀 Setting up Trading System Development Environment")
    print("=" * 50)
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📁 Creating virtual environment...")
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Determine Python executable path
    if os.name == 'nt':  # Windows
        python_exe = "venv\\Scripts\\python.exe"
        pip_exe = "venv\\Scripts\\pip.exe"
        activate_script = "venv\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        python_exe = "venv/bin/python"
        pip_exe = "venv/bin/pip"
        activate_script = "source venv/bin/activate"
    
    # Upgrade pip
    print("🔄 Upgrading pip...")
    run_command(f"{pip_exe} install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        print("📋 Installing requirements from requirements.txt...")
        if not run_command(f"{pip_exe} install -r requirements.txt", "Installing requirements"):
            print("⚠️  Some packages failed to install, continuing anyway...")
    
    # Install development dependencies
    dev_packages = [
        "black",
        "flake8", 
        "pytest",
        "pytest-asyncio",
        "pytest-cov"
    ]
    
    print("🛠️  Installing development dependencies...")
    for package in dev_packages:
        run_command(f"{pip_exe} install {package}", f"Installing {package}")
    
    # Test the installation
    print("🧪 Testing installation...")
    test_result = run_command(f"{python_exe} -c \"import main; print('✅ Main module imports successfully')\"", "Testing main module import")
    
    if test_result:
        print("\n🎉 Environment setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Activate the virtual environment:")
        print(f"      {activate_script}")
        print("   2. Run the server:")
        print("      python run_server.py")
        print("   3. Open http://localhost:8000/docs in your browser")
        print("\n💡 VS Code users:")
        print("   - Press Ctrl+Shift+P → 'Python: Select Interpreter'")
        print(f"   - Choose: {os.path.abspath(python_exe)}")
    else:
        print("\n⚠️  Setup completed with some issues. Check the errors above.")
    
    return True

if __name__ == "__main__":
    main() 