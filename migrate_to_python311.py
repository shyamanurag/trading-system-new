#!/usr/bin/env python3
"""
Migration Script: Python 3.11 Setup for Trading System
This script helps migrate from Python 3.13 to Python 3.11
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check current Python version"""
    version = sys.version_info
    print(f"Current Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 11:
        print("✅ Already using Python 3.11!")
        return True
    elif version.major == 3 and version.minor == 13:
        print("❌ Using Python 3.13 - needs migration to 3.11")
        return False
    else:
        print(f"⚠️  Using Python {version.major}.{version.minor} - recommend 3.11")
        return False

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def test_imports():
    """Test critical imports"""
    imports_to_test = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("redis", "redis"),
        ("sqlalchemy", "sqlalchemy"),
        ("truedata_ws", "TrueData"),
        ("websocket", "websocket-client"),
        ("requests", "requests"),
        ("pydantic", "pydantic")
    ]
    
    print("\n🧪 Testing imports...")
    failed_imports = []
    
    for module_name, display_name in imports_to_test:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError as e:
            print(f"❌ {display_name}: {e}")
            failed_imports.append(module_name)
    
    return failed_imports

def test_truedata_specific():
    """Test TrueData specific functionality"""
    print("\n🔍 Testing TrueData integration...")
    
    try:
        from truedata_ws.websocket.TD import TD
        print("✅ TrueData TD class imported successfully")
        
        # Test basic functionality
        td = TD("test_user", "test_pass", url="push.truedata.in")
        print("✅ TrueData TD class instantiated successfully")
        
        return True
    except Exception as e:
        print(f"❌ TrueData test failed: {e}")
        return False

def create_requirements_file():
    """Create requirements.txt with Python 3.11 compatible versions"""
    requirements = """# Python 3.11 Compatible Requirements
fastapi==0.104.1
uvicorn==0.24.0
gunicorn==21.2.0
pydantic==2.5.0
python-multipart==0.0.6
redis==5.0.1
sqlalchemy==2.0.23
alembic==1.12.1
pandas==2.2.0
numpy==1.26.4
python-dateutil==2.8.2
truedata-ws==1.0.0
websocket-client==1.6.4
requests==2.31.0
aiohttp==3.9.1
yfinance==0.2.28
pytest==7.4.3
black==23.11.0
flake8==6.1.0
python-dotenv==1.0.0
colorama==0.4.6
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ Created requirements.txt with Python 3.11 compatible versions")

def main():
    """Main migration function"""
    print("🚀 Python 3.11 Migration Script for Trading System")
    print("=" * 50)
    
    # Check current version
    if check_python_version():
        print("\n✅ No migration needed!")
    else:
        print("\n📋 Migration Steps:")
        print("1. Install Python 3.11 from: https://www.python.org/downloads/release/python-3118/")
        print("2. Create new virtual environment: python3.11 -m venv .venv")
        print("3. Activate environment: .venv\\Scripts\\activate (Windows) or source .venv/bin/activate (Linux/Mac)")
        print("4. Run this script again to test imports")
    
    # Test imports
    failed_imports = test_imports()
    
    # Test TrueData specifically
    truedata_works = test_truedata_specific()
    
    # Create requirements file
    create_requirements_file()
    
    # Summary
    print("\n📊 Migration Summary:")
    print(f"Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Failed Imports: {len(failed_imports)}")
    print(f"TrueData Working: {'✅' if truedata_works else '❌'}")
    
    if failed_imports:
        print(f"\n❌ Failed imports: {', '.join(failed_imports)}")
        print("💡 Install missing packages with: pip install -r requirements.txt")
    
    if truedata_works:
        print("\n🎉 TrueData integration is working!")
    else:
        print("\n⚠️  TrueData needs Python 3.11 to work properly")
    
    print("\n📝 Next Steps:")
    print("1. Update DigitalOcean app spec to use Python 3.11")
    print("2. Test deployment with new environment")
    print("3. Verify all trading strategies work")

if __name__ == "__main__":
    main() 