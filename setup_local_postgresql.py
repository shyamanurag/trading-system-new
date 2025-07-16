#!/usr/bin/env python3
"""
Local PostgreSQL Setup Script
Sets up PostgreSQL locally to match production environment exactly
"""
import os
import sys
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Docker found: {result.stdout.strip()}")
            return True
        else:
            logger.error("❌ Docker not found")
            return False
    except FileNotFoundError:
        logger.error("❌ Docker not installed")
        return False

def setup_postgresql_with_docker():
    """Set up PostgreSQL using Docker"""
    logger.info("🐳 Setting up PostgreSQL with Docker...")
    
    # Stop any existing containers
    logger.info("🛑 Stopping existing containers...")
    subprocess.run(['docker', 'stop', 'trading-postgres', 'trading-redis'], 
                  capture_output=True)
    subprocess.run(['docker', 'rm', 'trading-postgres', 'trading-redis'], 
                  capture_output=True)
    
    # Start PostgreSQL
    logger.info("🚀 Starting PostgreSQL container...")
    postgres_cmd = [
        'docker', 'run', '-d',
        '--name', 'trading-postgres',
        '-e', 'POSTGRES_DB=trading_system',
        '-e', 'POSTGRES_USER=trading_user', 
        '-e', 'POSTGRES_PASSWORD=trading_password',
        '-p', '5432:5432',
        'postgres:15'
    ]
    
    result = subprocess.run(postgres_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"❌ Failed to start PostgreSQL: {result.stderr}")
        return False
    
    logger.info("✅ PostgreSQL container started")
    
    # Start Redis
    logger.info("🚀 Starting Redis container...")
    redis_cmd = [
        'docker', 'run', '-d',
        '--name', 'trading-redis',
        '-p', '6379:6379',
        'redis:7-alpine'
    ]
    
    result = subprocess.run(redis_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"❌ Failed to start Redis: {result.stderr}")
        return False
    
    logger.info("✅ Redis container started")
    
    # Wait for PostgreSQL to be ready
    import time
    logger.info("⏳ Waiting for PostgreSQL to be ready...")
    time.sleep(10)
    
    return True

def create_database_schema():
    """Create the database schema"""
    logger.info("📝 Creating database schema...")
    
    try:
        import psycopg2
    except ImportError:
        logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='trading_user',
            password='trading_password',
            dbname='trading_system'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create users table with proper schema
        logger.info("📝 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                role VARCHAR(20) DEFAULT 'trader',
                status VARCHAR(20) DEFAULT 'active',
                is_active BOOLEAN NOT NULL DEFAULT true,
                broker_account_id VARCHAR(255),
                trading_enabled BOOLEAN NOT NULL DEFAULT false,
                max_position_size FLOAT,
                risk_level VARCHAR(20),
                preferences JSON,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                last_password_change TIMESTAMP,
                two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
                two_factor_secret VARCHAR(255),
                initial_capital FLOAT DEFAULT 100000.0,
                current_balance FLOAT DEFAULT 100000.0,
                risk_tolerance VARCHAR(20) DEFAULT 'medium',
                zerodha_client_id VARCHAR(50),
                max_daily_trades INTEGER DEFAULT 1000
            );
        """)
        
        # Create paper_trades table
        logger.info("📝 Creating paper_trades table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                action VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                price FLOAT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                status VARCHAR(20) NOT NULL,
                order_id VARCHAR(50),
                pnl FLOAT,
                strategy VARCHAR(50),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        
        # Create default user
        logger.info("📝 Creating default user...")
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, full_name,
                is_active, trading_enabled, initial_capital,
                current_balance, risk_tolerance, zerodha_client_id
            ) VALUES (
                'PAPER_TRADER_001', 'paper@algoauto.com',
                '$2b$12$dummy.hash.paper.trading', 'Paper Trading Account',
                true, true, 100000, 100000, 'medium', 'PAPER'
            ) ON CONFLICT (username) DO NOTHING;
        """)
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        return False

def create_env_file():
    """Create local environment file"""
    logger.info("📝 Creating local environment file...")
    
    env_content = """# Local Development Environment - PostgreSQL
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_system
REDIS_URL=redis://localhost:6379/0

# Application Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Security (Development Only)
JWT_SECRET=local-jwt-secret-key-for-development-only
ENCRYPTION_KEY=local-32-byte-encryption-key-dev-only

# Trading Configuration
TRADING_MODE=paper
PAPER_TRADING=true
"""
    
    with open('.env.local', 'w') as f:
        f.write(env_content)
    
    logger.info("✅ Created .env.local file")

def main():
    """Main setup function"""
    logger.info("🚀 Setting up local PostgreSQL development environment...")
    
    # Check Docker
    if not check_docker():
        logger.error("❌ Docker is required for this setup")
        logger.info("💡 Please install Docker: https://docs.docker.com/get-docker/")
        return False
    
    # Setup PostgreSQL with Docker
    if not setup_postgresql_with_docker():
        return False
    
    # Create schema
    if not create_database_schema():
        return False
    
    # Create env file
    create_env_file()
    
    logger.info("🎉 Local PostgreSQL setup completed successfully!")
    logger.info("")
    logger.info("📋 Next Steps:")
    logger.info("1. Install psycopg2: pip install psycopg2-binary")
    logger.info("2. Load environment: set -a; source .env.local; set +a")
    logger.info("3. Run application: python -m src.main")
    logger.info("")
    logger.info("🔗 Database URLs:")
    logger.info("   PostgreSQL: postgresql://trading_user:trading_password@localhost:5432/trading_system")
    logger.info("   Redis: redis://localhost:6379/0")
    logger.info("")
    logger.info("🛠️ Management:")
    logger.info("   Stop containers: docker stop trading-postgres trading-redis")
    logger.info("   Start containers: docker start trading-postgres trading-redis")
    logger.info("   Remove containers: docker rm trading-postgres trading-redis")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 