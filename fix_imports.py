#!/usr/bin/env python3
"""
Script to fix incorrect import statements in the trading system
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix import statements in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports from core. to the correct paths
        # Replace from core.exceptions import ... with from core.exceptions import ...
        # (This should work since core.exceptions exists in the root core directory)
        
        # Replace from core.orchestrator import ... with from core.orchestrator import ...
        # (This should work since core.orchestrator exists in the root core directory)
        
        # Replace from src.core.analysis import ... with from src.core.analysis import ...
        content = re.sub(r'from core\.analysis import', 'from src.core.analysis import', content)
        
        # Replace from src.core.market_data import ... with from src.core.market_data import ...
        content = re.sub(r'from core\.market_data import', 'from src.core.market_data import', content)
        
        # Replace from src.core.risk_manager import ... with from src.core.risk_manager import ...
        content = re.sub(r'from core\.risk_manager import', 'from src.core.risk_manager import', content)
        
        # Replace from src.core.position_tracker import ... with from src.core.position_tracker import ...
        content = re.sub(r'from core\.position_tracker import', 'from src.core.position_tracker import', content)
        
        # Replace from src.core.order_manager import ... with from src.core.order_manager import ...
        content = re.sub(r'from core\.order_manager import', 'from src.core.order_manager import', content)
        
        # Replace from src.events import ... with from src.events import ...
        content = re.sub(r'from core\.events import', 'from src.events import', content)
        
        # Replace from core.connection_manager import ... with from core.connection_manager import ...
        # (This should work since core.connection_manager exists in the root core directory)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False

def find_and_fix_imports():
    """Find all Python files and fix their imports"""
    root_dir = Path(".")
    python_files = list(root_dir.rglob("*.py"))
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    find_and_fix_imports() 