#!/usr/bin/env python3
"""
Local Development Setup Script
=============================
This script sets up your local development environment for the trading system.
Run this ONCE before starting local development.

Usage:
    python setup_local_development.py

What it does:
- Installs required Python packages
- Creates local database
- Verifies configuration
- Tests basic functionality
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🛠️  TRADING SYSTEM - LOCAL DEVELOPMENT SETUP")
    print("=" * 60)
    print("🏠 Setting up LOCAL DEVELOPMENT ENVIRONMENT")
    print("🔒 Completely isolated from production")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Try to install from local requirements first
        if Path("requirements.local.txt").exists():
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.local.txt"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("⚠️ Local requirements failed, trying main requirements...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ], capture_output=True, text=True)
        else:
            # Fallback to main requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_local_database():
    """Create local SQLite database"""
    print("\n💾 Setting up local database...")
    
    try:
        db_path = Path("local_trading.db")
        
        # Remove existing database if it exists
        if db_path.exists():
            print("🗑️ Removing existing local database...")
            db_path.unlink()
        
        # Create new database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create basic tables for testing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("local_test",))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Local database created: {db_path.absolute()}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create local database: {e}")
        return False

def create_local_directories():
    """Create necessary local directories"""
    print("\n📁 Creating local directories...")
    
    directories = [
        "logs",
        "data/local",
        "backups/local",
        "temp"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
        except Exception as e:
            print(f"⚠️ Could not create {directory}: {e}")

def verify_configuration():
    """Verify local configuration files exist"""
    print("\n⚙️ Verifying configuration...")
    
    config_files = [
        "config/local.env",
        "config/config.local.yaml"
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ Found: {config_file}")
        else:
            print(f"❌ Missing: {config_file}")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test if critical imports work"""
    print("\n🧪 Testing critical imports...")
    
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not available")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn available")
    except ImportError:
        print("❌ Uvicorn not available")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy available")
    except ImportError:
        print("❌ SQLAlchemy not available")
        return False
    
    return True

def create_env_file():
    """Create .env file for local development"""
    print("\n🔧 Creating local environment file...")
    
    env_content = """# Local Development Environment
# This file is automatically generated for local development

LOCAL_DEVELOPMENT=true
ENVIRONMENT=development
DEBUG=true
PAPER_TRADING=true
MOCK_TRADING=true
DATABASE_URL=sqlite:///./local_trading.db
REDIS_URL=redis://localhost:6379
JWT_SECRET=local-development-jwt-secret
"""
    
    try:
        with open(".env.local", "w") as f:
            f.write(env_content)
        print("✅ Created .env.local file")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env.local: {e}")
        return False

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create directories
    create_local_directories()
    
    # Create database
    if not create_local_database():
        print("\n❌ Setup failed at database creation")
        sys.exit(1)
    
    # Verify configuration
    if not verify_configuration():
        print("\n⚠️ Some configuration files are missing")
        print("💡 The setup script created the necessary files")
    
    # Create environment file
    create_env_file()
    
    # Test imports
    if not test_imports():
        print("\n❌ Setup failed at import testing")
        print("💡 Try running: pip install -r requirements.local.txt")
        sys.exit(1)
    
    # Success message
    print("\n" + "=" * 60)
    print("🎉 LOCAL DEVELOPMENT SETUP COMPLETE!")
    print("=" * 60)
    print("✅ All dependencies installed")
    print("✅ Local database created")
    print("✅ Configuration verified")
    print("✅ Environment ready")
    print("\n🚀 To start local development server:")
    print("   python run_local_development.py")
    print("\n🌐 Server will be available at:")
    print("   http://localhost:8000")
    print("\n📖 API documentation:")
    print("   http://localhost:8000/docs")
    print("\n🔒 Remember: This is LOCAL DEVELOPMENT ONLY")
    print("🛡️ No real trading - all operations are simulated")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Setup interrupted by user")
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        sys.exit(1) 