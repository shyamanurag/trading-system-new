"""
Database manager for the trading system
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        """Initialize database manager"""
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection"""
        try:
            # Try to create engine with the configured URL
            database_url = settings.database_url
            connect_args = settings.DATABASE_CONNECT_ARGS
            
            logger.info(f"Attempting to connect to database...")
            logger.info(f"Database URL (masked): {database_url.split('@')[0]}@[MASKED]")
            logger.info(f"Using connect_args: {connect_args}")
            
            # Create engine with proper SSL configuration
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args=connect_args
            )
            
            # Test the connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database connection initialized successfully")
            
            # CRITICAL FIX: Apply migrations automatically
            self._apply_migrations()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to initialize database: {error_msg}")
            
            # If it's an SSL error, provide helpful information
            if "sslmode" in error_msg.lower():
                logger.error("SSL mode error detected. Check your DATABASE_URL format.")
                logger.error("For DigitalOcean, the sslmode parameter should be handled via connect_args.")
            
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
                logger.info("🔄 Production environment detected - applying critical migrations...")
                
                # Apply migration 009 specifically to fix users table
                migration_009_path = Path("database/migrations/009_fix_users_table_id_column.sql")
                if migration_009_path.exists():
                    logger.info("🔧 Applying migration 009 to fix users table schema...")
                    
                    with open(migration_009_path, 'r') as f:
                        migration_sql = f.read()
                    
                    # Execute the migration
                    with self.engine.connect() as conn:
                        # Execute in a transaction
                        with conn.begin():
                            conn.execute(text(migration_sql))
                    
                    logger.info("✅ Migration 009 applied successfully!")
                    
                    # Verify the fix
                    with self.engine.connect() as conn:
                        result = conn.execute(text("SELECT id FROM users LIMIT 1"))
                        logger.info("✅ Verified: users table now has id column")
                
                else:
                    logger.warning("⚠️ Migration 009 file not found, skipping")
            else:
                logger.info("📝 Development environment - skipping auto-migrations")
                
        except Exception as e:
            logger.error(f"❌ Migration application failed: {e}")
            logger.info("🔄 Continuing without migration - check schema manually")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Check your database configuration.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        if not self.engine:
            logger.warning("Cannot create tables - database not initialized")
            return
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.engine is not None

# Create database manager instance - but don't fail if database is not available
try:
    db_manager = DatabaseManager()
except Exception as e:
    logger.warning(f"Database manager initialization failed: {e}")
    db_manager = None

# Dependency for FastAPI
def get_db():
    """Get database session for dependency injection"""
    if db_manager and db_manager.is_connected():
        with db_manager.get_session() as session:
            yield session
    else:
        # Return None if database is not available
        yield None 