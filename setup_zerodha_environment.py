#!/usr/bin/env python3
"""
🔧 ZERODHA ENVIRONMENT SETUP SCRIPT
==================================

This script helps you set up your Zerodha authentication environment properly.
It guides you through the configuration process and validates your setup.

Usage: python setup_zerodha_environment.py
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZerodhaEnvironmentSetup:
    """Helps set up Zerodha environment configuration"""
    
    def __init__(self):
        self.env_file = Path('.env')
        self.config = {}
    
    def print_header(self):
        """Print setup header"""
        print("\n" + "=" * 60)
        print("🔧 ZERODHA AUTHENTICATION ENVIRONMENT SETUP")
        print("=" * 60)
        print("This script will help you configure your Zerodha authentication.")
        print("You'll need:")
        print("1. Zerodha API Key and Secret")
        print("2. Your Zerodha User ID")
        print("3. Redis server (we'll help you set this up)")
        print("=" * 60 + "\n")
    
    def get_zerodha_credentials(self):
        """Get Zerodha API credentials from user"""
        print("📊 ZERODHA API CREDENTIALS")
        print("-" * 30)
        print("Get these from: https://developers.zerodha.com/")
        print("1. Login to Zerodha Developer Console")
        print("2. Create a new app or use existing one")
        print("3. Copy the API Key and Secret")
        print()
        
        api_key = input("Enter your Zerodha API Key: ").strip()
        api_secret = input("Enter your Zerodha API Secret: ").strip()
        user_id = input("Enter your Zerodha User ID: ").strip()
        
        if not all([api_key, api_secret, user_id]):
            print("❌ All fields are required!")
            return self.get_zerodha_credentials()
        
        self.config['ZERODHA_API_KEY'] = api_key
        self.config['ZERODHA_API_SECRET'] = api_secret
        self.config['ZERODHA_USER_ID'] = user_id
        
        print("✅ Zerodha credentials configured")
    
    def setup_redis(self):
        """Help user set up Redis"""
        print("\n🗄️ REDIS CONFIGURATION")
        print("-" * 25)
        print("Redis is required for storing authentication tokens.")
        print("Choose an option:")
        print("1. Use local Redis (recommended for development)")
        print("2. Use Docker Redis")
        print("3. Use cloud Redis service")
        print("4. I already have Redis configured")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            self.setup_local_redis()
        elif choice == "2":
            self.setup_docker_redis()
        elif choice == "3":
            self.setup_cloud_redis()
        elif choice == "4":
            redis_url = input("Enter your Redis URL: ").strip()
            self.config['REDIS_URL'] = redis_url or 'redis://localhost:6379'
        else:
            print("Invalid choice, using default local Redis")
            self.config['REDIS_URL'] = 'redis://localhost:6379'
    
    def setup_local_redis(self):
        """Setup local Redis"""
        print("\n📝 LOCAL REDIS SETUP")
        print("To install Redis locally:")
        print("Windows: Download from https://redis.io/download")
        print("macOS: brew install redis")
        print("Linux: sudo apt-get install redis-server")
        print()
        
        self.config['REDIS_URL'] = 'redis://localhost:6379'
        print("✅ Local Redis URL configured: redis://localhost:6379")
    
    def setup_docker_redis(self):
        """Setup Docker Redis"""
        print("\n🐳 DOCKER REDIS SETUP")
        print("Run this command to start Redis with Docker:")
        print("docker run -d -p 6379:6379 --name trading-redis redis:alpine")
        print()
        
        self.config['REDIS_URL'] = 'redis://localhost:6379'
        print("✅ Docker Redis URL configured: redis://localhost:6379")
    
    def setup_cloud_redis(self):
        """Setup cloud Redis"""
        print("\n☁️ CLOUD REDIS SETUP")
        print("Popular cloud Redis providers:")
        print("- Redis Cloud (redis.com)")
        print("- AWS ElastiCache")
        print("- DigitalOcean Managed Redis")
        print()
        
        redis_url = input("Enter your cloud Redis URL: ").strip()
        self.config['REDIS_URL'] = redis_url or 'redis://localhost:6379'
        print(f"✅ Cloud Redis configured: {self.config['REDIS_URL']}")
    
    def configure_trading_settings(self):
        """Configure trading settings"""
        print("\n💰 TRADING CONFIGURATION")
        print("-" * 28)
        
        paper_trading = input("Enable paper trading? (recommended for testing) [Y/n]: ").strip().lower()
        self.config['PAPER_TRADING'] = 'false' if paper_trading == 'n' else 'true'
        
        if self.config['PAPER_TRADING'] == 'true':
            print("✅ Paper trading enabled - no real money will be used")
        else:
            print("⚠️ Real trading enabled - real money will be used!")
            max_loss = input("Enter max daily loss limit (INR) [50000]: ").strip()
            self.config['MAX_DAILY_LOSS'] = max_loss or '50000'
    
    def set_other_settings(self):
        """Set other configuration settings"""
        print("\n⚙️ OTHER SETTINGS")
        print("-" * 17)
        
        self.config['ENVIRONMENT'] = 'development'
        self.config['DEBUG'] = 'true'
        self.config['LOG_LEVEL'] = 'INFO'
        self.config['JWT_SECRET'] = 'your_super_secret_jwt_key_change_this_in_production'
        self.config['EMAIL_NOTIFICATIONS_ENABLED'] = 'false'
        self.config['SMS_NOTIFICATIONS_ENABLED'] = 'false'
        self.config['ALLOWED_ORIGINS'] = '["http://localhost:3000", "http://localhost:8000"]'
        self.config['CORS_ENABLED'] = 'true'
        
        print("✅ Default settings configured")
    
    def write_env_file(self):
        """Write .env file"""
        print(f"\n📝 WRITING CONFIGURATION")
        print("-" * 25)
        
        # Backup existing .env if it exists
        if self.env_file.exists():
            backup_path = Path(f'.env.backup.{int(os.time())}')
            self.env_file.rename(backup_path)
            print(f"📋 Existing .env backed up to: {backup_path}")
        
        # Write new .env file
        with open(self.env_file, 'w') as f:
            f.write("# Zerodha Trading System Environment Configuration\n")
            f.write(f"# Generated on: {os.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in self.config.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Configuration written to: {self.env_file}")
    
    async def test_configuration(self):
        """Test the configuration"""
        print(f"\n🧪 TESTING CONFIGURATION")
        print("-" * 26)
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        errors = []
        
        # Test kiteconnect import
        try:
            from kiteconnect import KiteConnect
            print("✅ kiteconnect library available")
        except ImportError:
            errors.append("kiteconnect library not installed")
            print("❌ kiteconnect library not found")
        
        # Test Zerodha credentials
        api_key = os.getenv('ZERODHA_API_KEY')
        if api_key:
            try:
                kite = KiteConnect(api_key=api_key)
                login_url = kite.login_url()
                if "kite.zerodha.com" in login_url:
                    print("✅ Zerodha API Key valid")
                else:
                    errors.append("Invalid Zerodha API Key")
                    print("❌ Invalid Zerodha API Key")
            except Exception as e:
                errors.append(f"Zerodha API error: {e}")
                print(f"❌ Zerodha API error: {e}")
        
        # Test Redis connection
        try:
            import redis.asyncio as redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            redis_client = await redis.from_url(redis_url, socket_connect_timeout=5)
            await redis_client.ping()
            await redis_client.close()
            print("✅ Redis connection successful")
        except Exception as e:
            errors.append(f"Redis connection failed: {e}")
            print(f"❌ Redis connection failed: {e}")
        
        return errors
    
    def print_next_steps(self, test_errors):
        """Print next steps for user"""
        print(f"\n🎯 NEXT STEPS")
        print("-" * 12)
        
        if not test_errors:
            print("✅ Your Zerodha authentication is configured correctly!")
            print("\nTo start using the system:")
            print("1. Start your Redis server")
            print("2. Run: python -m src.main")
            print("3. Visit: http://localhost:8000/zerodha")
            print("4. Complete the daily authentication process")
        else:
            print("⚠️ Some issues need to be resolved:")
            for error in test_errors:
                print(f"   - {error}")
            print("\nAfter fixing these issues, re-run this setup script.")
        
        print(f"\n📚 HELPFUL LINKS")
        print("- Zerodha API Docs: https://kite.trade/docs/")
        print("- Redis Documentation: https://redis.io/documentation")
        print("- Project Documentation: README.md")
    
    async def run_setup(self):
        """Run the complete setup process"""
        try:
            self.print_header()
            self.get_zerodha_credentials()
            self.setup_redis()
            self.configure_trading_settings()
            self.set_other_settings()
            self.write_env_file()
            
            # Test configuration
            test_errors = await self.test_configuration()
            self.print_next_steps(test_errors)
            
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE!")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            logger.error(f"Setup error: {e}", exc_info=True)
            sys.exit(1)

async def main():
    """Main setup function"""
    setup = ZerodhaEnvironmentSetup()
    await setup.run_setup()

if __name__ == "__main__":
    # Install required packages if missing
    try:
        import dotenv
    except ImportError:
        print("Installing required packages...")
        os.system("pip install python-dotenv")
    
    asyncio.run(main()) 