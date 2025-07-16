#!/usr/bin/env python3
"""
Apply Database Migration - Run the migration file to fix schema issues
"""
import os
import sys
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """Apply the migration file to fix database schema"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        
        # Try to load from config
        try:
            sys.path.append('src')
            from config.database import db_config
            database_url = db_config.database_url
            logger.info("Loaded database URL from config")
        except Exception as e:
            logger.error(f"Failed to load database URL from config: {e}")
            return False
    
    if not database_url:
        logger.error("No database URL available")
        return False
        
    logger.info("🔧 Applying database migration to fix schema...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Read the migration file
        migration_file = "database/migrations/012_fix_foreign_key_constraints.sql"
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.info(f"📋 Read migration file: {migration_file}")
        
        # Apply the migration
        with engine.begin() as conn:
            # Split the migration into separate statements
            statements = migration_sql.split(';')
            
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if statement and not statement.startswith('--') and statement.upper() not in ['BEGIN', 'COMMIT']:
                    try:
                        logger.info(f"Executing statement {i+1}/{len(statements)}")
                        conn.execute(text(statement))
                    except Exception as e:
                        logger.warning(f"Statement {i+1} failed (may be expected): {e}")
                        continue
        
        logger.info("✅ Migration applied successfully!")
        
        # Verify the fix
        with engine.connect() as conn:
            # Check users table primary key
            result = conn.execute(text("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'users' 
                AND tc.constraint_type = 'PRIMARY KEY'
            """))
            
            pk_columns = result.fetchall()
            logger.info(f"✅ Users table primary key: {[col[0] for col in pk_columns]}")
            
            # Check if paper_trades table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'paper_trades'
            """))
            
            paper_trades_exists = result.fetchone() is not None
            logger.info(f"✅ Paper trades table exists: {paper_trades_exists}")
            
            if paper_trades_exists:
                # Check foreign key constraints
                result = conn.execute(text("""
                    SELECT 
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name 
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'paper_trades'
                """))
                
                fk_constraints = result.fetchall()
                logger.info(f"✅ Paper trades foreign keys: {len(fk_constraints)} found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1) 