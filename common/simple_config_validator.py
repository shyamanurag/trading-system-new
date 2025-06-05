#!/usr/bin/env python3
"""
Simple Configuration Validator for Trading System
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SimpleConfigValidator:
    """Simple configuration validator without complex dependencies"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
    
    def validate_config(self) -> bool:
        """Validate configuration file exists and has required fields"""
        try:
            # Check if config file exists
            if not self.config_path.exists():
                logger.info("Configuration file not found, creating sample config...")
                self.create_sample_config()
                return True
            
            # Load and validate basic structure
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise ValueError("Configuration file must contain a valid YAML dictionary")
            
            # Validate required sections
            required_sections = ['database', 'security', 'environment']
            missing_sections = []
            
            for section in required_sections:
                if section not in config:
                    missing_sections.append(section)
            
            if missing_sections:
                logger.warning(f"Missing configuration sections: {missing_sections}")
                logger.info("Consider updating your configuration file")
            
            # Validate database config
            if 'database' in config:
                db_config = config['database']
                required_db_fields = ['host', 'database', 'username', 'password']
                
                for field in required_db_fields:
                    if field not in db_config:
                        logger.warning(f"Missing database field: {field}")
            
            # Validate security config
            if 'security' in config:
                security_config = config['security']
                
                if 'jwt_secret' in security_config:
                    jwt_secret = security_config['jwt_secret']
                    if len(jwt_secret) < 32:
                        logger.warning("JWT secret should be at least 32 characters long")
                    
                    if jwt_secret == 'development-secret-key' and config.get('environment') == 'production':
                        raise ValueError("Development JWT secret cannot be used in production")
            
            # Validate environment
            if 'environment' in config:
                env = config['environment']
                valid_environments = ['development', 'staging', 'production', 'testing']
                if env not in valid_environments:
                    logger.warning(f"Environment '{env}' not in recommended list: {valid_environments}")
            
            logger.info("Configuration validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def create_sample_config(self, output_path: Optional[str] = None):
        """Create a sample configuration file"""
        if output_path is None:
            output_path = self.config_path
        else:
            output_path = Path(output_path)
        
        sample_config = {
            'environment': 'development',
            'debug': True,
            'version': '2.0.0',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'trading_system',
                'username': 'trading_user',
                'password': 'change_me_in_production',
                'ssl_mode': 'prefer',
                'pool_size': 10
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'password': None,
                'db': 0,
                'ssl': False
            },
            'security': {
                'jwt_secret': 'your-super-secret-jwt-key-change-in-production-minimum-32-chars',
                'jwt_algorithm': 'HS256',
                'jwt_expiration_hours': 24,
                'password_hash_rounds': 12,
                'max_login_attempts': 5,
                'require_2fa': False
            },
            'trading': {
                'max_daily_trades': 100,
                'max_position_size_percent': 10.0,
                'default_stop_loss_percent': 2.0,
                'max_drawdown_percent': 20.0,
                'risk_per_trade_percent': 1.0,
                'min_order_value': 1000.0,
                'max_order_value': 1000000.0
            },
            'monitoring': {
                'prometheus_enabled': True,
                'prometheus_port': 8001,
                'health_check_interval_seconds': 30,
                'log_level': 'INFO',
                'log_format': 'json',
                'metrics_retention_days': 30
            },
            'websocket': {
                'port': 8002,
                'max_connections': 1000,
                'ping_interval': 30,
                'compression_enabled': True
            },
            'compliance': {
                'sebi_reporting_enabled': True,
                'audit_trail_retention_days': 2555,
                'max_position_value': 50000000.0,
                'foreign_investment_limit_percent': 49.0
            },
            'brokers': {
                'zerodha': {
                    'name': 'zerodha',
                    'api_key': 'your_zerodha_api_key',
                    'api_secret': 'your_zerodha_api_secret',
                    'base_url': 'https://api.kite.trade',
                    'timeout_seconds': 30,
                    'rate_limit_per_minute': 60,
                    'sandbox_mode': False
                }
            },
            'timezone': 'Asia/Kolkata',
            'max_workers': 4
        }
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Sample configuration created at: {output_path}")

def main():
    """CLI interface"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            validator = SimpleConfigValidator()
            success = validator.validate_config()
            if success:
                print("✓ Configuration validation passed")
                sys.exit(0)
            else:
                print("✗ Configuration validation failed")
                sys.exit(1)
                
        elif command == "sample":
            output_path = sys.argv[2] if len(sys.argv) > 2 else "config/sample_config.yaml"
            validator = SimpleConfigValidator()
            validator.create_sample_config(output_path)
            print(f"✓ Sample configuration created at: {output_path}")
            sys.exit(0)
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, sample")
            sys.exit(1)
    else:
        print("Usage: python simple_config_validator.py [validate|sample] [output_path]")
        sys.exit(1)

if __name__ == "__main__":
    main() 