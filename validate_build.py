#!/usr/bin/env python3
"""
Docker Build Validation Script
Checks Dockerfile syntax, build context, and dependencies before building
"""

import os
import sys
import json
from pathlib import Path

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'Dockerfile',
        'requirements.txt', 
        'package.json',
        'vite.config.js',
        'main.py',
        'start_production.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_frontend_structure():
    """Check frontend directory structure"""
    frontend_path = Path('src/frontend')
    required_frontend_files = [
        'src/frontend/App.jsx',
        'src/frontend/index.jsx',
        'src/frontend/index.html'
    ]
    
    if not frontend_path.exists():
        print("❌ Frontend directory src/frontend/ missing")
        return False
    
    missing_files = []
    for file in required_frontend_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing frontend files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Frontend structure valid")
        return True

def check_package_json():
    """Validate package.json configuration"""
    try:
        with open('package.json', 'r') as f:
            package_data = json.load(f)
        
        # Check if build script exists
        if 'scripts' not in package_data or 'build' not in package_data['scripts']:
            print("❌ package.json missing build script")
            return False
        
        # Check essential dependencies
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}
        
        required_deps = ['react', 'vite', '@vitejs/plugin-react']
        missing_deps = [dep for dep in required_deps if dep not in all_deps]
        
        if missing_deps:
            print(f"❌ Missing essential dependencies: {', '.join(missing_deps)}")
            return False
        
        print("✅ package.json configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False

def check_requirements_txt():
    """Validate Python requirements"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        # Check for essential packages
        essential_packages = ['fastapi', 'uvicorn', 'asyncpg', 'redis']
        missing_packages = []
        
        for package in essential_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing essential Python packages: {', '.join(missing_packages)}")
            return False
        
        # Count total packages
        package_lines = [line.strip() for line in requirements.split('\n') 
                        if line.strip() and not line.startswith('#')]
        print(f"✅ requirements.txt valid ({len(package_lines)} packages)")
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_vite_config():
    """Check Vite configuration"""
    vite_config_path = Path('vite.config.js')
    if not vite_config_path.exists():
        print("❌ vite.config.js missing")
        return False
    
    try:
        with open(vite_config_path, 'r') as f:
            config_content = f.read()
        
        # Check for essential configuration
        if 'src/frontend' not in config_content:
            print("❌ vite.config.js doesn't specify correct root directory")
            return False
        
        if 'dist/frontend' not in config_content:
            print("❌ vite.config.js doesn't specify correct output directory")
            return False
        
        print("✅ vite.config.js configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading vite.config.js: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are documented"""
    env_file = Path('config/production.env')
    
    if not env_file.exists():
        print("⚠️  config/production.env not found (using system environment)")
        return True
    
    required_env_vars = [
        'DATABASE_URL',
        'REDIS_URL', 
        'JWT_SECRET',
        'APP_PORT'
    ]
    
    try:
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        missing_vars = []
        for var in required_env_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ Environment variables configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading production.env: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 Docker Build Validation")
    print("=" * 50)
    
    checks = [
        ("Required Files", check_required_files),
        ("Frontend Structure", check_frontend_structure),
        ("Package.json", check_package_json),
        ("Requirements.txt", check_requirements_txt),
        ("Vite Config", check_vite_config),
        ("Environment Variables", check_environment_variables)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if check_func():
            passed += 1
        else:
            print(f"   Failed: {check_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Ready for Docker build.")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues before building.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 