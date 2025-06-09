#!/usr/bin/env python3
"""
Comprehensive System Audit Script
Checks all components, integrations, and potential issues
"""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import importlib.util

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SystemAuditor:
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "unused_files": [],
            "missing_integrations": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log audit messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_issue(self, component: str, issue: str, severity: str = "HIGH"):
        """Add an issue to the audit"""
        self.audit_results["issues"].append({
            "component": component,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        self.log(f"Issue found in {component}: {issue}", "ERROR")
        
    def add_warning(self, component: str, warning: str):
        """Add a warning to the audit"""
        self.audit_results["warnings"].append({
            "component": component,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        })
        self.log(f"Warning in {component}: {warning}", "WARN")
        
    def add_recommendation(self, recommendation: str):
        """Add a recommendation"""
        self.audit_results["recommendations"].append(recommendation)
        
    async def check_python_imports(self):
        """Check all Python imports and dependencies"""
        self.log("Checking Python imports and dependencies...")
        component = "python_imports"
        self.audit_results["components"][component] = {"status": "checking"}
        
        issues = []
        python_files = list(Path(".").rglob("*.py"))
        
        for py_file in python_files:
            if "venv" in str(py_file) or "trading_env" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for imports
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')):
                        # Try to parse the import
                        try:
                            if 'import' in line:
                                module_name = line.split()[1].split('.')[0]
                                # Check if it's a local module or installed package
                                if not Path(f"{module_name}.py").exists() and not Path(module_name).is_dir():
                                    # Try to import it
                                    try:
                                        __import__(module_name)
                                    except ImportError:
                                        issues.append(f"{py_file}:{i+1} - Missing module: {module_name}")
                        except:
                            pass
            except Exception as e:
                issues.append(f"Error reading {py_file}: {e}")
                
        if issues:
            for issue in issues[:10]:  # Show first 10 issues
                self.add_issue(component, issue, "MEDIUM")
                
        self.audit_results["components"][component] = {
            "status": "completed",
            "total_files": len(python_files),
            "issues_found": len(issues)
        }
        
    async def check_frontend_backend_integration(self):
        """Check frontend-backend API integration"""
        self.log("Checking frontend-backend integration...")
        component = "frontend_backend_integration"
        self.audit_results["components"][component] = {"status": "checking"}
        
        # Check API endpoints in frontend
        frontend_api_calls = []
        frontend_files = list(Path("src/frontend").rglob("*.jsx")) + list(Path("src/frontend").rglob("*.js"))
        
        api_patterns = [
            "fetch(",
            "axios.",
            "/api/",
            "API_BASE_URL",
            "localhost:8000",
            "localhost:8001"
        ]
        
        for file in frontend_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in api_patterns:
                        if pattern in content:
                            # Extract API endpoints
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if pattern in line:
                                    frontend_api_calls.append({
                                        "file": str(file),
                                        "line": i + 1,
                                        "pattern": pattern,
                                        "content": line.strip()
                                    })
            except:
                pass
                
        # Check if backend has corresponding endpoints
        backend_endpoints = []
        main_py = Path("main.py")
        if main_py.exists():
            with open(main_py, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '@app.' in line and ('get' in line or 'post' in line or 'put' in line or 'delete' in line):
                        # Get the next few lines to find the path
                        for j in range(i, min(i+5, len(lines))):
                            if '("/' in lines[j] or '("/' in lines[j]:
                                backend_endpoints.append(lines[j].strip())
                                
        self.audit_results["components"][component] = {
            "status": "completed",
            "frontend_api_calls": len(frontend_api_calls),
            "backend_endpoints": len(backend_endpoints),
            "sample_frontend_calls": frontend_api_calls[:5],
            "sample_backend_endpoints": backend_endpoints[:5]
        }
        
    async def check_websocket_implementation(self):
        """Check WebSocket implementation"""
        self.log("Checking WebSocket implementation...")
        component = "websocket"
        self.audit_results["components"][component] = {"status": "checking"}
        
        ws_files = []
        ws_patterns = ["WebSocket", "websocket", "ws://", "wss://", "@app.websocket"]
        
        for pattern in ws_patterns:
            # Check Python files
            for py_file in Path(".").rglob("*.py"):
                if "venv" in str(py_file) or "trading_env" in str(py_file):
                    continue
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        if pattern in f.read():
                            ws_files.append(str(py_file))
                except:
                    pass
                    
            # Check frontend files
            for ext in ["*.js", "*.jsx", "*.ts", "*.tsx"]:
                for file in Path("src/frontend").rglob(ext):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            if pattern in f.read():
                                ws_files.append(str(file))
                    except:
                        pass
                        
        ws_files = list(set(ws_files))  # Remove duplicates
        
        # Check WebSocket manager
        ws_manager_exists = Path("websocket_manager.py").exists()
        
        self.audit_results["components"][component] = {
            "status": "completed",
            "websocket_files": ws_files,
            "websocket_manager_exists": ws_manager_exists,
            "total_ws_files": len(ws_files)
        }
        
        if not ws_manager_exists:
            self.add_issue(component, "WebSocket manager file not found", "HIGH")
            
    async def check_database_integration(self):
        """Check database integration"""
        self.log("Checking database integration...")
        component = "database"
        self.audit_results["components"][component] = {"status": "checking"}
        
        # Check for database files
        db_files = {
            "database_manager.py": Path("database_manager.py").exists(),
            "models": Path("src/models").exists(),
            "migrations": Path("migrations").exists() or Path("alembic").exists()
        }
        
        # Check for ORM usage
        orm_patterns = ["SQLAlchemy", "Base.metadata", "create_engine", "sessionmaker"]
        orm_usage = []
        
        for py_file in Path(".").rglob("*.py"):
            if "venv" in str(py_file) or "trading_env" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in orm_patterns:
                        if pattern in content:
                            orm_usage.append({
                                "file": str(py_file),
                                "pattern": pattern
                            })
            except:
                pass
                
        self.audit_results["components"][component] = {
            "status": "completed",
            "database_files": db_files,
            "orm_usage_count": len(orm_usage),
            "sample_orm_usage": orm_usage[:5]
        }
        
        if not db_files["database_manager.py"]:
            self.add_warning(component, "database_manager.py not found")
            
    async def check_authentication(self):
        """Check authentication implementation"""
        self.log("Checking authentication system...")
        component = "authentication"
        self.audit_results["components"][component] = {"status": "checking"}
        
        auth_files = []
        auth_patterns = ["JWT", "login", "authenticate", "Bearer", "token", "@router.post"]
        
        for pattern in auth_patterns:
            for py_file in Path(".").rglob("*.py"):
                if "venv" in str(py_file) or "trading_env" in str(py_file):
                    continue
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        if pattern in f.read():
                            auth_files.append(str(py_file))
                except:
                    pass
                    
        auth_files = list(set(auth_files))
        
        # Check specific auth files
        auth_components = {
            "auth_router": Path("src/api/auth.py").exists(),
            "auth_middleware": any("middleware" in f and "auth" in f for f in auth_files),
            "jwt_implementation": any("jwt" in f.lower() for f in auth_files)
        }
        
        self.audit_results["components"][component] = {
            "status": "completed",
            "auth_files": auth_files[:10],
            "auth_components": auth_components,
            "total_auth_files": len(auth_files)
        }
        
    async def check_unused_files(self):
        """Find potentially unused files"""
        self.log("Checking for unused files...")
        
        # Common patterns for potentially unused files
        unused_patterns = [
            "*_old.py",
            "*_backup.py",
            "*_test.py",
            "*.bak",
            "test_*.py",
            "old_*",
            "backup_*",
            "temp_*",
            "*.tmp"
        ]
        
        unused_files = []
        for pattern in unused_patterns:
            for file in Path(".").rglob(pattern):
                if "venv" not in str(file) and "trading_env" not in str(file):
                    unused_files.append(str(file))
                    
        # Check for duplicate functionality
        duplicate_patterns = {
            "deployment": ["deploy*.py", "deploy*.sh", "deploy*.bat"],
            "testing": ["test_*.py", "run_test*.py", "*_test.py"],
            "startup": ["start_*.py", "run_*.py", "main*.py"]
        }
        
        duplicates = {}
        for category, patterns in duplicate_patterns.items():
            files = []
            for pattern in patterns:
                files.extend([str(f) for f in Path(".").glob(pattern)])
            if len(files) > 2:
                duplicates[category] = files
                
        self.audit_results["unused_files"] = unused_files
        self.audit_results["duplicate_files"] = duplicates
        
        if len(unused_files) > 10:
            self.add_warning("file_cleanup", f"Found {len(unused_files)} potentially unused files")
            
    async def check_error_handling(self):
        """Check error handling implementation"""
        self.log("Checking error handling...")
        component = "error_handling"
        
        error_patterns = {
            "try_except": 0,
            "custom_exceptions": 0,
            "logging": 0,
            "error_responses": 0
        }
        
        for py_file in Path(".").rglob("*.py"):
            if "venv" in str(py_file) or "trading_env" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    error_patterns["try_except"] += content.count("try:")
                    error_patterns["custom_exceptions"] += content.count("class") and content.count("Exception)")
                    error_patterns["logging"] += content.count("logger.") + content.count("logging.")
                    error_patterns["error_responses"] += content.count("HTTPException")
            except:
                pass
                
        self.audit_results["components"][component] = {
            "status": "completed",
            "error_patterns": error_patterns
        }
        
        if error_patterns["try_except"] < 50:
            self.add_warning(component, "Low number of try-except blocks found")
            
    async def check_configuration(self):
        """Check configuration files"""
        self.log("Checking configuration...")
        component = "configuration"
        
        config_files = {
            ".env": Path(".env").exists(),
            ".env.local": Path(".env.local").exists(),
            "config.yaml": Path("config/config.yaml").exists(),
            "production.env": Path("config/production.env").exists(),
            "requirements.txt": Path("requirements.txt").exists(),
            "package.json": Path("src/frontend/package.json").exists()
        }
        
        # Check for sensitive data in configs
        sensitive_patterns = ["password", "secret", "key", "token"]
        exposed_secrets = []
        
        for config_file, exists in config_files.items():
            if exists and config_file != "requirements.txt":
                try:
                    with open(config_file, 'r') as f:
                        content = f.read().lower()
                        for pattern in sensitive_patterns:
                            if pattern in content and "example" not in content:
                                # Check if it's not a placeholder
                                lines = content.split('\n')
                                for line in lines:
                                    if pattern in line and '=' in line:
                                        value = line.split('=')[1].strip()
                                        if value and value not in ['', '""', "''", 'null', 'none']:
                                            exposed_secrets.append(f"{config_file}: {pattern}")
                except:
                    pass
                    
        self.audit_results["components"][component] = {
            "status": "completed",
            "config_files": config_files,
            "exposed_secrets_count": len(exposed_secrets)
        }
        
        if exposed_secrets:
            self.add_issue(component, f"Potential exposed secrets in config files", "CRITICAL")
            
    async def run_comprehensive_audit(self):
        """Run all audit checks"""
        self.log("Starting comprehensive system audit...")
        
        # Run all checks
        await self.check_python_imports()
        await self.check_frontend_backend_integration()
        await self.check_websocket_implementation()
        await self.check_database_integration()
        await self.check_authentication()
        await self.check_unused_files()
        await self.check_error_handling()
        await self.check_configuration()
        
        # Add recommendations based on findings
        if len(self.audit_results["issues"]) > 5:
            self.add_recommendation("Address critical issues before deployment")
            
        if len(self.audit_results["unused_files"]) > 20:
            self.add_recommendation("Clean up unused files to reduce project size")
            
        if not self.audit_results["components"].get("websocket", {}).get("websocket_manager_exists"):
            self.add_recommendation("Implement WebSocket manager for real-time features")
            
        # Generate summary
        self.audit_results["summary"] = {
            "total_issues": len(self.audit_results["issues"]),
            "total_warnings": len(self.audit_results["warnings"]),
            "critical_issues": len([i for i in self.audit_results["issues"] if i["severity"] == "CRITICAL"]),
            "components_checked": len(self.audit_results["components"]),
            "audit_completed": datetime.now().isoformat()
        }
        
        # Save audit results
        with open("comprehensive_audit_results.json", "w") as f:
            json.dump(self.audit_results, f, indent=2)
            
        self.log("Audit completed. Results saved to comprehensive_audit_results.json")
        
        # Print summary
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        print(f"Total Issues: {self.audit_results['summary']['total_issues']}")
        print(f"Critical Issues: {self.audit_results['summary']['critical_issues']}")
        print(f"Warnings: {self.audit_results['summary']['total_warnings']}")
        print(f"Unused Files: {len(self.audit_results['unused_files'])}")
        print(f"Components Checked: {self.audit_results['summary']['components_checked']}")
        
        if self.audit_results["issues"]:
            print("\nTop Issues:")
            for issue in self.audit_results["issues"][:5]:
                print(f"- [{issue['severity']}] {issue['component']}: {issue['issue']}")
                
        if self.audit_results["recommendations"]:
            print("\nRecommendations:")
            for rec in self.audit_results["recommendations"]:
                print(f"- {rec}")

async def main():
    auditor = SystemAuditor()
    await auditor.run_comprehensive_audit()

if __name__ == "__main__":
    asyncio.run(main()) 