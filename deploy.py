#!/usr/bin/env python3
"""
Unified Deployment Script
Handles all deployment scenarios: local, staging, and production
"""

import argparse
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
import platform

class DeploymentManager:
    """Manages deployments across different environments"""
    
    def __init__(self, environment: str, verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_command(self, command: str, shell: bool = True, check: bool = True):
        """Run shell command with error handling"""
        if self.verbose:
            self.log(f"Running: {command}", "DEBUG")
            
        try:
            result = subprocess.run(
                command,
                shell=shell,
                check=check,
                capture_output=True,
                text=True
            )
            if self.verbose and result.stdout:
                self.log(f"Output: {result.stdout}", "DEBUG")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error output: {e.stderr}", "ERROR")
            raise
            
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        self.log("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log("Python 3.8+ is required", "ERROR")
            return False
            
        # Check required files
        required_files = ["requirements.txt", "main.py"]
        for file in required_files:
            if not (self.project_root / file).exists():
                self.log(f"Required file missing: {file}", "ERROR")
                return False
                
        # Check environment-specific requirements
        if self.environment == "production":
            if not (self.project_root / "Dockerfile").exists():
                self.log("Dockerfile required for production deployment", "ERROR")
                return False
                
        self.log("Prerequisites check passed", "SUCCESS")
        return True
        
    def backup_current_deployment(self):
        """Create backup of current deployment"""
        self.log("Creating deployment backup...")
        
        backup_dir = self.project_root / "deployment_backups" / self.timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup important files
        files_to_backup = [
            ".env",
            "config/production.env",
            "config/config.yaml"
        ]
        
        for file in files_to_backup:
            source = self.project_root / file
            if source.exists():
                dest = backup_dir / file
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                self.log(f"Backed up: {file}")
                
        self.log(f"Backup created at: {backup_dir}", "SUCCESS")
        
    def run_tests(self):
        """Run test suite before deployment"""
        self.log("Running tests...")
        
        # Run pytest
        result = self.run_command("pytest -v --tb=short", check=False)
        
        if result.returncode != 0:
            self.log("Tests failed! Aborting deployment", "ERROR")
            return False
            
        self.log("All tests passed", "SUCCESS")
        return True
        
    def build_application(self):
        """Build application for deployment"""
        self.log("Building application...")
        
        # Install dependencies
        self.log("Installing dependencies...")
        self.run_command(f"{sys.executable} -m pip install -r requirements.txt")
        
        # Build frontend if exists
        if (self.project_root / "frontend").exists():
            self.log("Building frontend...")
            os.chdir(self.project_root / "frontend")
            self.run_command("npm install")
            self.run_command("npm run build")
            os.chdir(self.project_root)
            
        self.log("Build completed", "SUCCESS")
        
    def deploy_local(self):
        """Deploy to local environment"""
        self.log("Deploying to local environment...")
        
        # Create virtual environment if not exists
        venv_path = self.project_root / "venv_local"
        if not venv_path.exists():
            self.log("Creating virtual environment...")
            self.run_command(f"{sys.executable} -m venv venv_local")
            
        # Activate and install dependencies
        if platform.system() == "Windows":
            activate_cmd = "venv_local\\Scripts\\activate.bat && "
        else:
            activate_cmd = "source venv_local/bin/activate && "
            
        self.run_command(f"{activate_cmd}pip install -r requirements.txt")
        
        # Start services
        self.log("Starting local services...")
        self.run_command(f"{activate_cmd}python main.py", check=False)
        
    def deploy_staging(self):
        """Deploy to staging environment"""
        self.log("Deploying to staging environment...")
        
        # Build Docker image
        self.log("Building Docker image...")
        self.run_command("docker build -t trading-system:staging .")
        
        # Run container
        self.log("Starting staging container...")
        self.run_command(
            "docker run -d --name trading-system-staging "
            "-p 8001:8001 "
            "--env-file config/staging.env "
            "trading-system:staging"
        )
        
        self.log("Staging deployment completed", "SUCCESS")
        
    def deploy_production(self):
        """Deploy to production environment"""
        self.log("Deploying to production environment...")
        
        # Ensure we're on main branch
        result = self.run_command("git branch --show-current", check=False)
        if result.stdout.strip() != "main":
            self.log("Must be on main branch for production deployment", "ERROR")
            return
            
        # Check for uncommitted changes
        result = self.run_command("git status --porcelain", check=False)
        if result.stdout.strip():
            self.log("Uncommitted changes detected. Please commit or stash", "ERROR")
            return
            
        # Tag the release
        tag = f"v{datetime.now().strftime('%Y.%m.%d')}-{self.timestamp}"
        self.run_command(f"git tag {tag}")
        self.log(f"Created release tag: {tag}")
        
        # Deploy to DigitalOcean
        if (self.project_root / ".do" / "app.yaml").exists():
            self.log("Deploying to DigitalOcean App Platform...")
            self.run_command("doctl apps create-deployment $APP_ID")
        else:
            self.log("DigitalOcean app spec not found", "WARNING")
            
        self.log("Production deployment initiated", "SUCCESS")
        
    def deploy(self):
        """Main deployment method"""
        self.log(f"Starting deployment to {self.environment} environment")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
            
        # Create backup
        self.backup_current_deployment()
        
        # Run tests (skip for local)
        if self.environment != "local":
            if not self.run_tests():
                return False
                
        # Build application
        self.build_application()
        
        # Deploy based on environment
        if self.environment == "local":
            self.deploy_local()
        elif self.environment == "staging":
            self.deploy_staging()
        elif self.environment == "production":
            self.deploy_production()
        else:
            self.log(f"Unknown environment: {self.environment}", "ERROR")
            return False
            
        self.log("Deployment completed successfully!", "SUCCESS")
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified deployment script for trading system"
    )
    parser.add_argument(
        "environment",
        choices=["local", "staging", "production"],
        help="Target deployment environment"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests before deployment"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before deployment"
    )
    
    args = parser.parse_args()
    
    # Create deployment manager
    manager = DeploymentManager(args.environment, args.verbose)
    
    # Override methods if flags are set
    if args.skip_tests:
        manager.run_tests = lambda: True
    if args.no_backup:
        manager.backup_current_deployment = lambda: None
        
    # Run deployment
    try:
        success = manager.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        manager.log("Deployment cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        manager.log(f"Deployment failed: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main() 