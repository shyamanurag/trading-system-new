#!/usr/bin/env python3
"""
Command Runner for Trading System
Avoids PowerShell syntax issues by using Python subprocess
"""

import subprocess
import sys
import os
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def run_command(cmd, shell=True, capture_output=False):
    """Run a command safely"""
    print(f"{Colors.CYAN}Running: {cmd}{Colors.RESET}")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ Success{Colors.RESET}")
                return result.stdout
            else:
                print(f"{Colors.RED}✗ Failed with code {result.returncode}{Colors.RESET}")
                if result.stderr:
                    print(f"{Colors.RED}Error: {result.stderr}{Colors.RESET}")
                return None
        else:
            result = subprocess.run(cmd, shell=shell)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ Success{Colors.RESET}")
                return True
            else:
                print(f"{Colors.RED}✗ Failed with code {result.returncode}{Colors.RESET}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {str(e)}{Colors.RESET}")
        return False

def git_commit(message):
    """Git add and commit"""
    print(f"\n{Colors.BOLD}Git Commit{Colors.RESET}")
    print("=" * 40)
    
    # Add all files
    if run_command("git add -A"):
        # Commit with message
        if run_command(f'git commit -m "{message}"'):
            print(f"{Colors.GREEN}✓ Commit successful!{Colors.RESET}")
            return True
    return False

def git_push():
    """Git push to origin main"""
    print(f"\n{Colors.BOLD}Git Push{Colors.RESET}")
    print("=" * 40)
    
    if run_command("git push origin main"):
        print(f"{Colors.GREEN}✓ Push successful!{Colors.RESET}")
        return True
    return False

def check_deployment():
    """Check deployment status"""
    print(f"\n{Colors.BOLD}Deployment Status{Colors.RESET}")
    print("=" * 40)
    
    # Try Node.js script
    if os.path.exists("check_deployment.js"):
        return run_command("node check_deployment.js")
    elif os.path.exists("check_deployment.py"):
        return run_command("python check_deployment.py")
    else:
        print(f"{Colors.YELLOW}No deployment check script found{Colors.RESET}")
        return False

def run_tests():
    """Run test suite"""
    print(f"\n{Colors.BOLD}Running Tests{Colors.RESET}")
    print("=" * 40)
    
    if os.path.exists("test_deployment_status.py"):
        return run_command("python test_deployment_status.py")
    else:
        print(f"{Colors.YELLOW}No test script found{Colors.RESET}")
        return False

def start_local():
    """Start local development server"""
    print(f"\n{Colors.BOLD}Starting Local Server{Colors.RESET}")
    print("=" * 40)
    
    if os.path.exists("run_local.py"):
        return run_command("python run_local.py")
    else:
        return run_command("python main.py")

def git_status():
    """Show git status"""
    print(f"\n{Colors.BOLD}Git Status{Colors.RESET}")
    print("=" * 40)
    
    run_command("git status")
    print(f"\n{Colors.CYAN}Deployment URL: https://algoauto-9gx56.ondigitalocean.app{Colors.RESET}")

def show_help():
    """Show help message"""
    print(f"""
{Colors.BOLD}{Colors.BLUE}Trading System Command Runner{Colors.RESET}
{Colors.CYAN}============================={Colors.RESET}

{Colors.YELLOW}Usage:{Colors.RESET} python run_cmd.py [command] [args]

{Colors.YELLOW}Commands:{Colors.RESET}
  commit "message"  - Add all files and commit with message
  push             - Push to origin main
  deploy           - Check deployment status
  test             - Run test suite
  local            - Start local server
  status           - Show git status
  help             - Show this help message

{Colors.YELLOW}Examples:{Colors.RESET}
  python run_cmd.py commit "Fixed API endpoints"
  python run_cmd.py push
  python run_cmd.py deploy

{Colors.GREEN}This tool avoids PowerShell syntax issues by using Python subprocess.{Colors.RESET}
""")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "commit":
        if len(sys.argv) < 3:
            print(f"{Colors.RED}Error: Commit message required{Colors.RESET}")
            print("Usage: python run_cmd.py commit \"Your message\"")
            return
        message = " ".join(sys.argv[2:])
        git_commit(message)
    
    elif command == "push":
        git_push()
    
    elif command == "deploy":
        check_deployment()
    
    elif command == "test":
        run_tests()
    
    elif command == "local":
        start_local()
    
    elif command == "status":
        git_status()
    
    elif command == "help":
        show_help()
    
    else:
        print(f"{Colors.RED}Unknown command: {command}{Colors.RESET}")
        show_help()

if __name__ == "__main__":
    main() 