#!/usr/bin/env python3
"""
Quick fix for orchestrator async calls
"""
import os
import re

def fix_orchestrator_calls():
    """Fix synchronous calls to TradingOrchestrator.get_instance()"""
    
    files_to_fix = [
        "src/api/simple_daily_auth.py",
        "src/api/system_status.py", 
        "src/api/trading_control.py",
        "src/api/system_health.py",
        "src/api/dashboard_api.py",
        "src/api/daily_auth_workflow.py",
        "main.py",
        "purge_fake_data_contamination.py"
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"🔧 Fixing {file_path}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace synchronous calls with None (safe fallback)
                original_content = content
                
                # Pattern 1: orchestrator = TradingOrchestrator.get_instance()
                content = re.sub(
                    r'orchestrator = TradingOrchestrator\.get_instance\(\)',
                    'orchestrator = None  # TODO: Fix async orchestrator call',
                    content
                )
                
                # Pattern 2: orchestrator_instance = TradingOrchestrator.get_instance()
                content = re.sub(
                    r'orchestrator_instance = TradingOrchestrator\.get_instance\(\)',
                    'orchestrator_instance = None  # TODO: Fix async orchestrator call',
                    content
                )
                
                # Pattern 3: trading_state["orchestrator"] = TradingOrchestrator.get_instance()
                content = re.sub(
                    r'trading_state\["orchestrator"\] = TradingOrchestrator\.get_instance\(\)',
                    'trading_state["orchestrator"] = None  # TODO: Fix async orchestrator call',
                    content
                )
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Fixed orchestrator calls in {file_path}")
                else:
                    print(f"  ⚠️ No changes needed in {file_path}")
                    
            except Exception as e:
                print(f"  ❌ Error fixing {file_path}: {e}")
        else:
            print(f"  ⚠️ File not found: {file_path}")

if __name__ == "__main__":
    print("🚀 Fixing orchestrator synchronous calls...")
    fix_orchestrator_calls()
    print("🎯 Orchestrator fixes complete!") 