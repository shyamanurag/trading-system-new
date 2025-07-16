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
        """Initialize database connection"""
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
            
            # Apply migrations if needed
            self._apply_migrations()
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise the error - let the app continue without database
            self.engine = None
            self.SessionLocal = None
    
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