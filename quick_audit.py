#!/usr/bin/env python3
"""
Quick System Audit - Focus on key integration issues
"""
import os
import json
from pathlib import Path
from datetime import datetime

class QuickAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "critical_issues": [],
            "integrations": {},
            "recommendations": []
        }
        
    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        
    def check_websocket_integration(self):
        """Check WebSocket setup"""
        self.log("Checking WebSocket integration...")
        
        ws_backend = Path("websocket_manager.py").exists()
        ws_frontend = False
        
        # Check frontend WebSocket usage
        if Path("src/frontend/services/websocket.ts").exists():
            ws_frontend = True
            
        # Check if WebSocket endpoint exists in main.py
        ws_endpoint = False
        if Path("main.py").exists():
            with open("main.py", 'r', encoding='utf-8') as f:
                if "@app.websocket" in f.read():
                    ws_endpoint = True
                    
        self.results["integrations"]["websocket"] = {
            "backend_manager": ws_backend,
            "frontend_service": ws_frontend,
            "endpoint_defined": ws_endpoint,
            "status": "OK" if all([ws_backend, ws_frontend, ws_endpoint]) else "INCOMPLETE"
        }
        
        if not all([ws_backend, ws_frontend, ws_endpoint]):
            self.results["critical_issues"].append("WebSocket integration incomplete")
            
    def check_frontend_backend_communication(self):
        """Check if frontend can communicate with backend"""
        self.log("Checking frontend-backend communication...")
        
        # Check API endpoints
        api_endpoints = {
            "auth": False,
            "users": False,
            "trading": False,
            "market_data": False
        }
        
        if Path("main.py").exists():
            with open("main.py", 'r', encoding='utf-8') as f:
                content = f.read()
                if "/api/v1/auth" in content:
                    api_endpoints["auth"] = True
                if "/api/users" in content:
                    api_endpoints["users"] = True
                if "/api/trading" in content or "/api/autonomous" in content:
                    api_endpoints["trading"] = True
                if "/api/market-data" in content:
                    api_endpoints["market_data"] = True
                    
        # Check frontend API calls
        frontend_calls = {
            "auth": False,
            "fetch_configured": False
        }
        
        login_form = Path("src/frontend/components/LoginForm.jsx")
        if login_form.exists():
            with open(login_form, 'r', encoding='utf-8') as f:
                content = f.read()
                if "/api/v1/auth/login" in content:
                    frontend_calls["auth"] = True
                if "API_BASE_URL" in content or "import.meta.env" in content:
                    frontend_calls["fetch_configured"] = True
                    
        self.results["integrations"]["frontend_backend"] = {
            "api_endpoints": api_endpoints,
            "frontend_calls": frontend_calls,
            "status": "OK" if all(api_endpoints.values()) and all(frontend_calls.values()) else "ISSUES"
        }
        
    def check_database_setup(self):
        """Check database configuration"""
        self.log("Checking database setup...")
        
        db_manager = Path("database_manager.py").exists()
        models_dir = Path("src/models").exists()
        
        # Check if database is being used in main.py
        db_initialized = False
        if Path("main.py").exists():
            with open("main.py", 'r', encoding='utf-8') as f:
                content = f.read()
                if "database_manager" in content and "init_database_manager" in content:
                    db_initialized = True
                    
        self.results["integrations"]["database"] = {
            "manager_exists": db_manager,
            "models_defined": models_dir,
            "initialized_in_main": db_initialized,
            "status": "OK" if all([db_manager, models_dir, db_initialized]) else "NEEDS_SETUP"
        }
        
    def check_authentication_flow(self):
        """Check complete auth flow"""
        self.log("Checking authentication flow...")
        
        auth_backend = Path("src/api/auth.py").exists()
        auth_frontend = Path("src/frontend/components/LoginForm.jsx").exists()
        
        # Check JWT configuration
        jwt_configured = False
        if Path(".env.local").exists():
            with open(".env.local", 'r', encoding='utf-8') as f:
                if "JWT_SECRET" in f.read():
                    jwt_configured = True
                    
        self.results["integrations"]["authentication"] = {
            "backend_api": auth_backend,
            "frontend_form": auth_frontend,
            "jwt_configured": jwt_configured,
            "status": "OK" if all([auth_backend, auth_frontend, jwt_configured]) else "INCOMPLETE"
        }
        
    def check_deployment_readiness(self):
        """Check if app is ready for local deployment"""
        self.log("Checking deployment readiness...")
        
        required_files = {
            "main.py": Path("main.py").exists(),
            "requirements.txt": Path("requirements.txt").exists(),
            "frontend_package.json": Path("src/frontend/package.json").exists(),
            ".env.local": Path(".env.local").exists()
        }
        
        self.results["integrations"]["deployment"] = {
            "required_files": required_files,
            "status": "READY" if all(required_files.values()) else "NOT_READY"
        }
        
    def check_unused_files(self):
        """Quick check for obvious unused files"""
        self.log("Checking for unused files...")
        
        unused_patterns = ["*_old.*", "*_backup.*", "test_*.py", "*.bak"]
        unused_count = 0
        
        for pattern in unused_patterns:
            unused_count += len(list(Path(".").glob(pattern)))
            
        if unused_count > 10:
            self.results["critical_issues"].append(f"Found {unused_count} potentially unused files")
            
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        
        if not self.results["integrations"]["websocket"]["status"] == "OK":
            self.results["recommendations"].append(
                "WebSocket not fully integrated - frontend and backend WebSocket services need to be connected"
            )
            
        if not self.results["integrations"]["authentication"]["status"] == "OK":
            self.results["recommendations"].append(
                "Complete authentication setup - ensure JWT_SECRET is configured in .env.local"
            )
            
        if not self.results["integrations"]["database"]["status"] == "OK":
            self.results["recommendations"].append(
                "Database setup incomplete - ensure database_manager is properly initialized"
            )
            
        if self.results["integrations"]["frontend_backend"]["status"] != "OK":
            self.results["recommendations"].append(
                "Frontend-backend integration issues - verify API endpoints match frontend calls"
            )
            
    def run_audit(self):
        """Run quick audit"""
        print("\n" + "="*60)
        print("QUICK SYSTEM AUDIT")
        print("="*60 + "\n")
        
        self.check_websocket_integration()
        self.check_frontend_backend_communication()
        self.check_database_setup()
        self.check_authentication_flow()
        self.check_deployment_readiness()
        self.check_unused_files()
        self.generate_recommendations()
        
        # Save results
        with open("quick_audit_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        
        print("\nIntegration Status:")
        for component, details in self.results["integrations"].items():
            status = details.get("status", "UNKNOWN")
            symbol = "✅" if status == "OK" or status == "READY" else "❌"
            print(f"{symbol} {component}: {status}")
            
        if self.results["critical_issues"]:
            print("\nCritical Issues:")
            for issue in self.results["critical_issues"]:
                print(f"❌ {issue}")
                
        if self.results["recommendations"]:
            print("\nRecommendations:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"{i}. {rec}")
                
        print(f"\nDetailed results saved to: quick_audit_results.json")

if __name__ == "__main__":
    auditor = QuickAuditor()
    auditor.run_audit() 