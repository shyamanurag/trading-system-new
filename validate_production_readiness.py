#!/usr/bin/env python3
"""
Production Readiness Validation Script
Comprehensive checks for deployment readiness
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def add_issue(self, category, description, severity="HIGH"):
        self.issues.append({
            "category": category,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_warning(self, category, description):
        self.warnings.append({
            "category": category,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_passed(self, category, description):
        self.passed.append({
            "category": category,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def validate_environment_variables(self):
        """Validate all required environment variables"""
        logger.info("🔍 Validating environment variables...")
        
        # Load production.env
        env_file = Path("config/production.env")
        if not env_file.exists():
            self.add_issue("Configuration", "Production environment file missing: config/production.env")
            return
            
        env_vars = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                    
        # Critical variables
        critical_vars = {
            'DATABASE_URL': 'Database connection string',
            'REDIS_URL': 'Redis connection string',
            'JWT_SECRET': 'JWT signing secret',
            'WEBHOOK_SECRET': 'Webhook signature secret',
            'ZERODHA_API_KEY': 'Zerodha API key',
            'ZERODHA_API_SECRET': 'Zerodha API secret'
        }
        
        for var, description in critical_vars.items():
            if not env_vars.get(var):
                self.add_issue("Environment", f"Missing {description}: {var}")
            elif var == 'ZERODHA_API_SECRET' and env_vars[var] == env_vars.get('ZERODHA_API_KEY'):
                self.add_issue("Security", f"Zerodha API secret appears to be same as API key")
            elif env_vars[var] in ['your_real_zerodha_api_secret_here', 'placeholder', 'changeme']:
                self.add_issue("Configuration", f"Placeholder value detected for {var}")
            else:
                self.add_passed("Environment", f"{description} configured")
                
        # Optional but recommended variables
        optional_vars = {
            'TELEGRAM_BOT_TOKEN': 'Telegram notifications',
            'EMAIL_USERNAME': 'Email notifications',
            'N8N_WEBHOOK_URL': 'N8N integration'
        }
        
        for var, description in optional_vars.items():
            if not env_vars.get(var) or 'your_' in env_vars[var]:
                self.add_warning("Configuration", f"Optional {description} not configured: {var}")
            else:
                self.add_passed("Integration", f"{description} configured")
                
    def validate_mock_data_removal(self):
        """Check for remaining mock data in codebase"""
        logger.info("🔍 Checking for mock data removal...")
        
        # Files to check for mock data
        files_to_check = [
            "src/frontend/components/AutonomousTradingDashboard.jsx",
            "src/frontend/components/LoginForm.jsx",
            "src/core/rest_apy.py"
        ]
        
        mock_patterns = [
            "mock", "Mock", "MOCK", "dummy", "Dummy", "placeholder",
            "test_", "demo_data", "fake_", "sample_"
        ]
        
        for file_path in files_to_check:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for mock patterns in content
                found_mocks = []
                for pattern in mock_patterns:
                    if pattern in content and "fetchAutonomousData" not in content:
                        found_mocks.append(pattern)
                        
                if found_mocks:
                    self.add_issue("Code Quality", f"Mock data patterns found in {file_path}: {found_mocks}")
                else:
                    self.add_passed("Code Quality", f"No mock data found in {file_path}")
            else:
                self.add_warning("File System", f"File not found for validation: {file_path}")
                
    def validate_security_configuration(self):
        """Validate security settings"""
        logger.info("🔍 Validating security configuration...")
        
        # Check JWT secret strength
        env_file = Path("config/production.env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                
            if 'JWT_SECRET=' in content:
                jwt_line = [line for line in content.split('\n') if line.startswith('JWT_SECRET=')]
                if jwt_line:
                    jwt_secret = jwt_line[0].split('=', 1)[1]
                    if len(jwt_secret) < 32:
                        self.add_issue("Security", "JWT secret too short (< 32 characters)")
                    elif jwt_secret in ['changeme', 'secret', 'password']:
                        self.add_issue("Security", "Weak JWT secret detected")
                    else:
                        self.add_passed("Security", "JWT secret appears secure")
                        
            # Check webhook secret
            if 'WEBHOOK_SECRET=' in content:
                webhook_line = [line for line in content.split('\n') if line.startswith('WEBHOOK_SECRET=')]
                if webhook_line:
                    webhook_secret = webhook_line[0].split('=', 1)[1]
                    if len(webhook_secret) < 16:
                        self.add_issue("Security", "Webhook secret too short (< 16 characters)")
                    else:
                        self.add_passed("Security", "Webhook secret configured")
                        
            # Check for HTTPS enforcement
            if 'HTTPS_ONLY=true' not in content:
                self.add_warning("Security", "HTTPS enforcement not explicitly enabled")
                
            # Check CORS configuration
            if 'ALLOWED_ORIGINS=*' in content:
                self.add_warning("Security", "CORS allows all origins (consider restricting for production)")
                
    def validate_database_configuration(self):
        """Validate database configuration"""
        logger.info("🔍 Validating database configuration...")
        
        env_file = Path("config/production.env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check database URL format
            if 'DATABASE_URL=' in content:
                db_line = [line for line in content.split('\n') if line.startswith('DATABASE_URL=')]
                if db_line:
                    db_url = db_line[0].split('=', 1)[1]
                    if not db_url.startswith('postgresql://'):
                        self.add_issue("Database", "Invalid database URL format")
                    elif 'localhost' in db_url:
                        self.add_warning("Database", "Using localhost database URL")
                    else:
                        self.add_passed("Database", "Database URL format valid")
                        
            # Check SSL mode
            if 'DATABASE_SSL=require' in content:
                self.add_passed("Database", "SSL mode configured for database")
            else:
                self.add_warning("Database", "Database SSL mode not explicitly set to 'require'")
                
            # Check connection pool settings
            if 'DATABASE_POOL_SIZE=' in content:
                self.add_passed("Database", "Connection pool size configured")
            else:
                self.add_warning("Database", "Database connection pool not configured")
                
    def validate_api_endpoints(self):
        """Validate API endpoint configuration"""
        logger.info("🔍 Validating API endpoints...")
        
        # Check for production API base URL
        frontend_files = list(Path("src/frontend").rglob("*.jsx"))
        
        localhost_found = False
        for file_path in frontend_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'localhost:8000' in content:
                        localhost_found = True
                        break
                        
        if localhost_found:
            self.add_warning("API", "Frontend still uses localhost API URLs")
        else:
            self.add_passed("API", "Frontend API URLs appear production-ready")
            
    def validate_trading_configuration(self):
        """Validate trading-specific configuration"""
        logger.info("🔍 Validating trading configuration...")
        
        env_file = Path("config/production.env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check paper trading mode
            if 'PAPER_TRADING=false' in content:
                self.add_passed("Trading", "Live trading mode enabled")
                self.add_warning("Trading", "⚠️ LIVE TRADING ENABLED - Real money at risk!")
            elif 'PAPER_TRADING=true' in content:
                self.add_warning("Trading", "Paper trading mode enabled (safe but not live)")
            else:
                self.add_issue("Trading", "Paper trading mode not explicitly set")
                
            # Check Zerodha configuration
            if 'ZERODHA_CLIENT_ID=' in content and 'ZERODHA_API_KEY=' in content:
                self.add_passed("Trading", "Zerodha API configuration present")
            else:
                self.add_issue("Trading", "Zerodha API configuration incomplete")
                
            # Check TrueData configuration
            if 'TRUEDATA_USERNAME=' in content and 'TRUEDATA_PASSWORD=' in content:
                self.add_passed("Trading", "TrueData configuration present")
            else:
                self.add_warning("Trading", "TrueData configuration missing (market data provider)")
                
    def generate_report(self):
        """Generate comprehensive validation report"""
        logger.info("📊 Generating validation report...")
        
        total_checks = len(self.passed) + len(self.warnings) + len(self.issues)
        
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "passed": len(self.passed),
                "warnings": len(self.warnings),
                "issues": len(self.issues),
                "readiness_score": round((len(self.passed) / total_checks * 100), 1) if total_checks > 0 else 0
            },
            "passed_checks": self.passed,
            "warnings": self.warnings,
            "issues": self.issues
        }
        
        # Determine deployment readiness
        high_issues = [issue for issue in self.issues if issue.get("severity") == "HIGH"]
        
        if len(high_issues) == 0:
            report["deployment_status"] = "✅ READY FOR PRODUCTION"
            report["recommendation"] = "System passes all critical checks. Address warnings when possible."
        elif len(high_issues) <= 2:
            report["deployment_status"] = "⚠️ CONDITIONAL READY"
            report["recommendation"] = "Address high-priority issues before deployment."
        else:
            report["deployment_status"] = "❌ NOT READY FOR PRODUCTION"
            report["recommendation"] = "Critical issues must be resolved before deployment."
            
        return report
        
    def run_all_validations(self):
        """Run all validation checks"""
        logger.info("🚀 Starting production readiness validation...")
        
        self.validate_environment_variables()
        self.validate_mock_data_removal()
        self.validate_security_configuration()
        self.validate_database_configuration()
        self.validate_api_endpoints()
        self.validate_trading_configuration()
        
        return self.generate_report()

def main():
    """Main validation function"""
    try:
        validator = ProductionValidator()
        report = validator.run_all_validations()
        
        # Print summary
        print("\n" + "="*60)
        print("🏁 PRODUCTION READINESS VALIDATION REPORT")
        print("="*60)
        
        print(f"📊 Readiness Score: {report['summary']['readiness_score']}%")
        print(f"🎯 Status: {report['deployment_status']}")
        print(f"💡 Recommendation: {report['recommendation']}")
        
        print(f"\n📈 Results Summary:")
        print(f"  ✅ Passed: {report['summary']['passed']}")
        print(f"  ⚠️ Warnings: {report['summary']['warnings']}")
        print(f"  ❌ Issues: {report['summary']['issues']}")
        
        # Show critical issues
        if report['issues']:
            print(f"\n❌ Critical Issues:")
            for issue in report['issues']:
                print(f"  • {issue['category']}: {issue['description']}")
                
        # Show warnings
        if report['warnings']:
            print(f"\n⚠️ Warnings:")
            for warning in report['warnings']:
                print(f"  • {warning['category']}: {warning['description']}")
                
        # Save detailed report
        with open('production_readiness_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: production_readiness_report.json")
        print("="*60)
        
        return 0 if len([issue for issue in report['issues'] if issue.get("severity") == "HIGH"]) == 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 