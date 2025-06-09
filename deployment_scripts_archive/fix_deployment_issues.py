#!/usr/bin/env python3
"""
Fix deployment issues before pushing to production
"""
import os
import re
import json
from pathlib import Path

def fix_health_check_localhost():
    """Fix health check falling back to localhost"""
    print("🔧 Fixing health check localhost issues...")
    
    # Fix health_check.py
    health_check_file = Path("health_check.py")
    if health_check_file.exists():
        content = health_check_file.read_text()
        # Replace localhost with 0.0.0.0 for production
        content = content.replace(
            'health_url = f"http://localhost:{port}/health/ready"',
            'health_url = f"http://0.0.0.0:{port}/health/ready"'
        )
        health_check_file.write_text(content)
        print("✅ Fixed health_check.py")
    
    # Fix any hardcoded localhost in main.py CORS
    main_file = Path("main.py")
    if main_file.exists():
        content = main_file.read_text()
        # Update CORS to use environment variable
        old_cors = '''allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative development port
        "http://localhost:8001",  # Current backend server
        "https://yourdomain.com", # Production domain - replace with actual domain
        "https://algoauto-ua2iq.ondigitalocean.app",  # Production domain
        "*"  # Allow all origins temporarily for debugging
    ],'''
        
        new_cors = '''allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative development port
        "http://localhost:8001",  # Current backend server
        "https://algoauto-ua2iq.ondigitalocean.app",  # Production domain
        os.getenv("FRONTEND_URL", "https://algoauto-ua2iq.ondigitalocean.app"),  # Dynamic frontend URL
        "*" if os.getenv("ENVIRONMENT") == "development" else None  # Allow all in dev only
    ],'''
        
        content = content.replace(old_cors, new_cors)
        main_file.write_text(content)
        print("✅ Fixed CORS configuration")

def fix_authentication():
    """Fix authentication issues"""
    print("🔧 Fixing authentication issues...")
    
    # Check if JWT_SECRET is properly set
    env_file = Path(".env.local")
    if env_file.exists():
        content = env_file.read_text()
        if "JWT_SECRET" not in content:
            content += "\nJWT_SECRET=your-secret-key-here-change-in-production\n"
            env_file.write_text(content)
            print("✅ Added JWT_SECRET to .env.local")
    
    # Ensure auth.py has proper error handling
    auth_file = Path("src/api/auth.py")
    if auth_file.exists():
        content = auth_file.read_text()
        
        # Fix the login endpoint to handle missing fields properly
        if "username = credentials.get" not in content:
            old_login = '''@router.post("/login")
async def login(credentials: dict):
    """Login endpoint"""
    username = credentials["username"]
    password = credentials["password"]'''
            
            new_login = '''@router.post("/login")
async def login(credentials: dict):
    """Login endpoint"""
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password are required"
        )'''
            
            content = content.replace(old_login, new_login)
            auth_file.write_text(content)
            print("✅ Fixed auth.py error handling")

def fix_redis_connection():
    """Fix Redis connection issues"""
    print("🔧 Fixing Redis connection issues...")
    
    # Update main.py to handle Redis connection properly
    main_file = Path("main.py")
    if main_file.exists():
        content = main_file.read_text()
        
        # Add better Redis error handling
        if "redis_client = None" not in content:
            # Find the Redis initialization section
            redis_section = re.search(r'async def init_redis\(\):(.*?)(?=\nasync def|\Z)', content, re.DOTALL)
            if redis_section:
                old_init = redis_section.group(0)
                new_init = '''async def init_redis():
    """Initialize Redis connection with proper error handling"""
    global redis_client
    
    redis_url = os.getenv('REDIS_URL', os.getenv('REDIS_TLS_URL'))
    
    if not redis_url:
        logger.warning("No Redis URL configured - running without Redis")
        redis_client = None
        return
    
    try:
        # Parse Redis URL
        if redis_url.startswith('rediss://'):
            # SSL connection
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                ssl_cert_reqs='none'  # For self-signed certs
            )
        else:
            # Non-SSL connection
            redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        await redis_client.ping()
        logger.info("✅ Redis connected successfully")
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("Continuing without Redis - some features may be limited")
        redis_client = None'''
                
                content = content.replace(old_init, new_init)
                main_file.write_text(content)
                print("✅ Fixed Redis connection handling")

def create_production_env():
    """Create production environment template"""
    print("🔧 Creating production environment template...")
    
    prod_env = Path("config/production.env.template")
    prod_env.parent.mkdir(exist_ok=True)
    
    content = '''# Production Environment Variables Template
# Copy this to .env and fill in the actual values

# Application
ENVIRONMENT=production
APP_NAME=Trading System
APP_VERSION=2.0.0
APP_PORT=8000

# Security
JWT_SECRET=your-production-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Database
DATABASE_URL=${DATABASE_URL}

# Redis
REDIS_URL=${REDIS_URL}
REDIS_TLS_URL=${REDIS_TLS_URL}

# Frontend
FRONTEND_URL=https://algoauto-ua2iq.ondigitalocean.app

# Trading APIs
ZERODHA_API_KEY=${ZERODHA_API_KEY}
ZERODHA_API_SECRET=${ZERODHA_API_SECRET}
ZERODHA_USER_ID=${ZERODHA_USER_ID}
ZERODHA_PASSWORD=${ZERODHA_PASSWORD}
ZERODHA_PIN=${ZERODHA_PIN}

TRUEDATA_USER=${TRUEDATA_USER}
TRUEDATA_PASSWORD=${TRUEDATA_PASSWORD}

# Webhooks
WEBHOOK_SECRET=${WEBHOOK_SECRET}
N8N_WEBHOOK_URL=${N8N_WEBHOOK_URL}

# Monitoring
SENTRY_DSN=${SENTRY_DSN}
LOG_LEVEL=INFO

# Feature Flags
PAPER_TRADING=true
ENABLE_WEBSOCKET=true
ENABLE_ML=true
'''
    
    prod_env.write_text(content)
    print("✅ Created production.env.template")

def update_package_json():
    """Update package.json to fix build issues"""
    print("🔧 Updating package.json...")
    
    package_file = Path("src/frontend/package.json")
    if package_file.exists():
        with open(package_file, 'r') as f:
            package_data = json.load(f)
        
        # Update build command to handle environment
        package_data["scripts"]["build"] = "vite build --mode production"
        
        # Ensure proxy is set for development
        if "proxy" not in package_data:
            package_data["proxy"] = "http://localhost:8000"
        
        with open(package_file, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        print("✅ Updated package.json")

def main():
    """Run all fixes"""
    print("🚀 Starting deployment fixes...\n")
    
    fix_health_check_localhost()
    fix_authentication()
    fix_redis_connection()
    create_production_env()
    update_package_json()
    
    print("\n✅ All fixes applied!")
    print("\n📝 Next steps:")
    print("1. Review the changes")
    print("2. Test locally with: python main.py")
    print("3. Commit and push to git")
    print("4. Deploy to DigitalOcean")

if __name__ == "__main__":
    main() 