#!/usr/bin/env python3
"""
Requirements Synchronization Script
Syncs all requirements files with the main requirements.txt to avoid conflicts.
"""

import os
import sys
from pathlib import Path

def read_requirements(file_path):
    """Read requirements from a file"""
    if not file_path.exists():
        return []
    
    requirements = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '>=' in line:
                requirements.append(line)
    return requirements

def write_requirements(file_path, requirements, header=""):
    """Write requirements to a file"""
    with open(file_path, 'w') as f:
        if header:
            f.write(header + '\n\n')
        for req in requirements:
            f.write(req + '\n')

def main():
    """Main synchronization function"""
    print("🔄 Syncing requirements files...")
    
    # Read main requirements
    main_req_file = Path("requirements.txt")
    if not main_req_file.exists():
        print("❌ Main requirements.txt not found!")
        return False
    
    main_requirements = read_requirements(main_req_file)
    print(f"✅ Found {len(main_requirements)} requirements in main file")
    
    # Update other requirements files
    other_files = [
        ("requirements_truedata.txt", "# TrueData Integration Requirements\n# Synced with main requirements.txt"),
        ("requirements_python311.txt", "# Python 3.11 Compatible Requirements\n# Synced with main requirements.txt"),
        ("requirements_python313_compatible.txt", "# Python 3.13 Compatible Requirements\n# Synced with main requirements.txt")
    ]
    
    for file_name, header in other_files:
        file_path = Path(file_name)
        if file_path.exists():
            write_requirements(file_path, main_requirements, header)
            print(f"✅ Updated {file_name}")
        else:
            print(f"⚠️  {file_name} not found, skipping")
    
    # Verify PIP_REQUIREMENTS in app.yaml matches
    app_yaml = Path("app.yaml")
    if app_yaml.exists():
        print("✅ app.yaml exists - PIP_REQUIREMENTS should be synced manually")
        print("💡 Run: python -c \"import yaml; print(yaml.safe_load(open('app.yaml'))['services'][0]['envs'][-1]['value'])\"")
    
    print("🎉 Requirements synchronization complete!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 