#!/usr/bin/env python3
"""
Windows Command Line Fix Script
Helps resolve hanging cmd/PowerShell issues
"""

import os
import subprocess
import sys
import psutil
import signal

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def kill_hanging_processes():
    """Kill any hanging cmd, powershell, or node processes"""
    print(f"\n{Colors.BOLD}Checking for hanging processes...{Colors.RESET}")
    
    processes_to_check = ['cmd.exe', 'powershell.exe', 'node.exe', 'curl.exe']
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if proc.info['name'].lower() in processes_to_check:
                # Check if process is hanging (high CPU or been running too long)
                proc.cpu_percent(interval=0.1)
                if proc.cpu_percent() > 90:
                    print(f"{Colors.YELLOW}Killing hanging {proc.info['name']} (PID: {proc.info['pid']}){Colors.RESET}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_count > 0:
        print(f"{Colors.GREEN}✓ Killed {killed_count} hanging processes{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✓ No hanging processes found{Colors.RESET}")

def clear_temp_files():
    """Clear Windows temp files that might cause issues"""
    print(f"\n{Colors.BOLD}Clearing temporary files...{Colors.RESET}")
    
    temp_dirs = [
        os.environ.get('TEMP'),
        os.environ.get('TMP'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
    ]
    
    cleared = 0
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Only clear old temp files (older than 1 day)
                import time
                current_time = time.time()
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if current_time - os.path.getmtime(file_path) > 86400:  # 1 day
                                os.remove(file_path)
                                cleared += 1
                        except:
                            pass
            except:
                pass
    
    print(f"{Colors.GREEN}✓ Cleared {cleared} old temp files{Colors.RESET}")

def reset_npm_cache():
    """Clear npm cache which can cause node hanging"""
    print(f"\n{Colors.BOLD}Clearing npm cache...{Colors.RESET}")
    
    try:
        subprocess.run(['npm', 'cache', 'clean', '--force'], 
                      capture_output=True, text=True, timeout=10)
        print(f"{Colors.GREEN}✓ npm cache cleared{Colors.RESET}")
    except:
        print(f"{Colors.YELLOW}⚠ Could not clear npm cache{Colors.RESET}")

def set_execution_policy():
    """Set PowerShell execution policy to avoid script blocking"""
    print(f"\n{Colors.BOLD}Setting PowerShell execution policy...{Colors.RESET}")
    
    try:
        subprocess.run(['powershell', '-Command', 
                       'Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force'],
                      capture_output=True, text=True, timeout=10)
        print(f"{Colors.GREEN}✓ PowerShell execution policy set{Colors.RESET}")
    except:
        print(f"{Colors.YELLOW}⚠ Could not set execution policy{Colors.RESET}")

def recommendations():
    """Print recommendations"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== RECOMMENDATIONS ==={Colors.RESET}")
    print(f"""
{Colors.YELLOW}To avoid command line hanging issues:{Colors.RESET}

1. {Colors.GREEN}Use Python scripts instead of cmd/PowerShell:{Colors.RESET}
   - python run_cmd.py commit "message"  (instead of git commit)
   - python run_cmd.py push              (instead of git push)
   - python test_api.py                  (instead of curl/node)

2. {Colors.GREEN}If you must use cmd, use these workarounds:{Colors.RESET}
   - Use: cmd /c "command"               (forces cmd to exit after)
   - Use: python -c "import os; os.system('command')"
   - Use the batch file: commands.bat

3. {Colors.GREEN}For HTTP requests:{Colors.RESET}
   - Use: python test_api.py             (instead of curl)
   - This uses Python requests library which is more reliable

4. {Colors.GREEN}If PowerShell keeps hanging:{Colors.RESET}
   - Open a new terminal
   - Use Windows Terminal instead of default PowerShell
   - Consider using Git Bash or WSL

5. {Colors.GREEN}To test the deployment:{Colors.RESET}
   - python test_api.py                  (tests all endpoints)
   - python test_api.py /api/v1/elite/   (test specific endpoint)
""")

def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.BLUE}Windows Command Line Fix Tool{Colors.RESET}")
    print("=" * 40)
    
    if sys.platform != 'win32':
        print(f"{Colors.YELLOW}This script is for Windows only{Colors.RESET}")
        return
    
    # Install psutil if not available
    try:
        import psutil
    except ImportError:
        print(f"{Colors.YELLOW}Installing psutil...{Colors.RESET}")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil'])
        import psutil
    
    # Run fixes
    kill_hanging_processes()
    clear_temp_files()
    reset_npm_cache()
    set_execution_policy()
    
    # Show recommendations
    recommendations()
    
    print(f"\n{Colors.GREEN}✓ Fixes applied. Try using the Python scripts instead of cmd/curl.{Colors.RESET}")

if __name__ == "__main__":
    main() 