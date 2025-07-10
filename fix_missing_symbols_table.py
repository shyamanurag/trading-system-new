#!/usr/bin/env python3
"""
Fix Missing Symbols Table
Recreate the symbols table that was lost during git rollback
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_symbols_table():
    """Create the missing symbols table"""
    try:
        # Try psycopg2 first (production)
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Get database URL from environment
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL not found in environment")
                return False
            
            logger.info(f"Connecting to database...")
            
            # Connect to database
            conn = psycopg2.connect(db_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Read SQL script
            with open('create_symbols_table.sql', 'r') as f:
                sql_script = f.read()
            
            logger.info("Executing symbols table creation script...")
            
            # Execute the SQL script
            cursor.execute(sql_script)
            
            # Verify table was created
            cursor.execute("SELECT COUNT(*) FROM symbols")
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            logger.info(f"✅ Symbols table created successfully with {count} symbols")
            
            # Close connection
            cursor.close()
            conn.close()
            
            return True
            
        except ImportError:
            logger.warning("psycopg2 not available, trying sqlite3...")
            
            # Fallback to sqlite3 for development
            import sqlite3
            
            # Connect to database
            conn = sqlite3.connect('trading.db')
            cursor = conn.cursor()
            
            # Read and modify SQL script for SQLite compatibility
            with open('create_symbols_table.sql', 'r') as f:
                sql_script = f.read()
            
            # SQLite modifications
            sql_script = sql_script.replace('TIMESTAMP WITH TIME ZONE', 'TIMESTAMP')
            sql_script = sql_script.replace('ON CONFLICT (symbol) DO NOTHING', 'OR IGNORE')
            
            logger.info("Executing symbols table creation script (SQLite)...")
            
            # Execute the SQL script
            cursor.executescript(sql_script)
            
            # Verify table was created
            cursor.execute("SELECT COUNT(*) FROM symbols")
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            logger.info(f"✅ Symbols table created successfully with {count} symbols")
            
            # Close connection
            conn.close()
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to create symbols table: {e}")
        return False

def test_search_functionality():
    """Test the search functionality after creating table"""
    try:
        import requests
        
        # Test the search endpoint
        url = "https://algoauto-9gx56.ondigitalocean.app/api/v1/search/autocomplete"
        params = {
            'query': 'NIFTY',
            'category': 'symbols',
            'limit': 5
        }
        
        logger.info("Testing search functionality...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Search working! Found {len(data.get('suggestions', []))} results")
            return True
        else:
            logger.error(f"❌ Search test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Search test error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Fixing missing symbols table...")
    
    # Create the symbols table
    if fix_symbols_table():
        logger.info("✅ Symbols table fix completed")
        
        # Test search functionality
        logger.info("🧪 Testing search functionality...")
        if test_search_functionality():
            logger.info("🎉 Search functionality working!")
        else:
            logger.warning("⚠️ Search test failed - table may need time to sync")
    else:
        logger.error("❌ Failed to fix symbols table") 