#!/usr/bin/env python3
"""
Fix DateTime Import Error in Redis Token Storage

The Redis token storage fix has a datetime import conflict.
This script fixes the import issue.
"""

import os
import re

def fix_datetime_import():
    """Fix the datetime import error in zerodha_manual_auth.py"""
    
    file_path = "src/api/zerodha_manual_auth.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The problematic code pattern
    problematic_pattern = r'# Store token with expiration \(tokens expire at 6 AM IST next day\)\s*from datetime import datetime\s*current_hour = datetime\.now\(\)\.hour'
    
    # The fixed code
    fixed_code = """# Store token with expiration (tokens expire at 6 AM IST next day)
            current_hour = datetime.now().hour"""
    
    # Apply the fix
    new_content = re.sub(problematic_pattern, fixed_code, content, flags=re.MULTILINE)
    
    # Also remove any duplicate Redis fix blocks
    duplicate_pattern = r'# CRITICAL FIX: Store token in Redis for orchestrator access\s*try:\s*import redis.*?# Don\'t fail the request, just log the error\s*# CRITICAL FIX: Store token in Redis for orchestrator access\s*try:'
    
    new_content = re.sub(duplicate_pattern, '# CRITICAL FIX: Store token in Redis for orchestrator access\n        try:', new_content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ DateTime import error fixed!")
    return True

if __name__ == "__main__":
    print("🔧 Fixing DateTime Import Error...")
    fix_datetime_import()
    print("✅ Fix applied - ready for token submission!") 