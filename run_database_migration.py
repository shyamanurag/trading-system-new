#!/usr/bin/env python3
"""
Run database migration to fix foreign key constraints and schema issues.
This script will fix the users table and paper_trades foreign key problems.
"""
import os
import sys
import psycopg2
from pathlib import Path

def run_migration():
    """Run the database migration to fix schema issues"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL environment variable found")
        print("Set DATABASE_URL and try again")
        return False
    
    # Read the migration file
    migration_file = Path(__file__).parent / 'database' / 'migrations' / '012_fix_foreign_key_constraints.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    try:
        print(f"🔄 Running migration: {migration_file.name}")
        print(f"🔗 Connecting to database...")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Enable autocommit for DDL operations
        cursor = conn.cursor()
        
        # Read and execute migration
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🚀 Executing migration...")
        cursor.execute(migration_sql)
        
        print("✅ Migration completed successfully!")
        
        # Verify the results
        print("\n🔍 Verifying migration results...")
        
        # Check users table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """)
        id_column = cursor.fetchone()
        
        if id_column:
            print(f"✅ Users table 'id' column: {id_column[1]} (nullable: {id_column[2]})")
        else:
            print("❌ Users table 'id' column not found")
            
        # Check primary key
        cursor.execute("""
            SELECT constraint_name, column_name
            FROM information_schema.key_column_usage 
            WHERE table_name = 'users' 
            AND constraint_name LIKE '%pkey%'
        """)
        pk_info = cursor.fetchone()
        
        if pk_info:
            print(f"✅ Users table primary key: {pk_info[1]}")
        else:
            print("❌ Users table primary key not found")
            
        # Check foreign key constraint
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints 
            WHERE table_name = 'paper_trades' 
            AND constraint_type = 'FOREIGN KEY'
        """)
        fk_constraints = cursor.fetchall()
        
        if fk_constraints:
            print(f"✅ Paper_trades foreign key constraints: {len(fk_constraints)} found")
            for fk in fk_constraints:
                print(f"   - {fk[0]}")
        else:
            print("❌ Paper_trades foreign key constraints not found")
            
        # Check user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Total users in database: {user_count}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database migration completed and verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 