"""
Database manager for the trading system
"""
import logging
import os
import sqlalchemy
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Optional

logger = logging.getLogger(__name__)

# Database base for models
Base = declarative_base()

class DatabaseManager:
    """Centralized database management"""
    
    def __init__(self):
        self.engine: Optional[sqlalchemy.Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
        
    def initialize(self):
        """Initialize database connection and ensure schema is ready"""
        if self._initialized:
            return
            
        try:
            logger.info("Attempting to connect to database...")
            
            # Get database URL from environment
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            # Log masked URL for debugging
            masked_url = database_url.replace(database_url.split('@')[0].split('//')[1], 'AVNS_LpaPpsdL4CtOii03MnN')
            masked_url = masked_url.replace(database_url.split('@')[1].split('/')[0], '[MASKED]')
            logger.info(f"Database URL (masked): {masked_url}")
            
            # Configure connection args
            connect_args = {}
            if 'sslmode=require' in database_url or database_url.startswith('postgresql'):
                connect_args['sslmode'] = 'require'
                
            logger.info(f"Using connect_args: {connect_args}")
            
            # Create engine with connection pooling optimized for DigitalOcean
            self.engine = create_engine(
                database_url,
                poolclass=NullPool,  # Disable connection pooling for serverless
                connect_args=connect_args,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database connection initialized successfully")
            
            # Ensure database is ready for paper trading (autonomous)
            self._ensure_database_ready()
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise the error - let the app continue without database
            self.engine = None
            self.SessionLocal = None

    def _ensure_database_ready(self):
        """Ensure database has required structure for paper trading"""
        try:
            environment = os.getenv('ENVIRONMENT', 'development')
            
            if environment == 'production':
                logger.info("🔄 Ensuring database is ready for paper trading...")
                
                with self.engine.begin() as conn:
                    # Check if users table has id column
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        AND column_name = 'id'
                    """))
                    
                    if not result.fetchone():
                        logger.info("📝 Adding id column to users table...")
                        conn.execute(text("""
                            ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY
                        """))
                        logger.info("✅ Added id column to users table")
                    
                    # Ensure at least one user exists for paper trading
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM users WHERE id = 1
                    """))
                    
                    if result.scalar() == 0:
                        logger.info("📝 Creating default paper trading user...")
                        conn.execute(text("""
                            INSERT INTO users (
                                id, username, email, password_hash, full_name,
                                initial_capital, current_balance, risk_tolerance,
                                is_active, zerodha_client_id, trading_enabled,
                                max_daily_trades, max_position_size, created_at, updated_at
                            ) VALUES (
                                1, 'PAPER_TRADER_001', 'paper@algoauto.com',
                                '$2b$12$dummy.hash.paper.trading', 'Paper Trading Account',
                                100000, 100000, 'medium',
                                true, 'PAPER', true,
                                1000, 500000, NOW(), NOW()
                            ) ON CONFLICT (id) DO NOTHING
                        """))
                        logger.info("✅ Created default paper trading user")
                    
                    logger.info("✅ Database is ready for paper trading!")
                    
        except Exception as e:
            logger.warning(f"⚠️ Could not ensure database readiness: {e}")
            logger.info("📊 System will continue - paper trading may have limited functionality")
    
    def _apply_migrations(self):
        """Apply database migrations if needed"""
        try:
            import os
            from pathlib import Path
            
            # Check if we're in production and should apply migrations
            environment = os.getenv('ENVIRONMENT', 'development')
            
            if environment == 'production':
                logger.info("🔄 Production environment detected - skipping auto-migrations")
                logger.info("📝 Database migrations should be applied manually via deployment scripts")
            else:
                logger.info("📝 Development environment - skipping auto-migrations")
                
        except Exception as e:
            logger.error(f"❌ Migration check failed: {e}")
            logger.info("🔄 Continuing without migration")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Check your database configuration.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_sql(self, sql: str):
        """Execute raw SQL"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        
        with self.engine.connect() as conn:
            with conn.begin():
                return conn.execute(text(sql))
    
    def get_engine(self):
        """Get SQLAlchemy engine"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        return self.engine
    
    def health_check(self) -> dict:
        """Check database health"""
        try:
            if not self.engine:
                return {"status": "error", "message": "Database not initialized"}
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
            return {
                "status": "healthy" if row and row[0] == 1 else "unhealthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Database health check failed: {str(e)}"
            }

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
def get_session():
    """Get database session - backward compatibility"""
    return db_manager.get_session()

def get_engine():
    """Get database engine - backward compatibility"""
    return db_manager.get_engine()

def get_db():
    """Get database session generator - FastAPI style"""
    with db_manager.get_session() as session:
        yield session

def initialize_database():
    """Initialize database - backward compatibility"""
    return db_manager.initialize()

def execute_sql(sql: str):
    """Execute SQL - backward compatibility"""
    return db_manager.execute_sql(sql) 