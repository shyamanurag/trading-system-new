import os
import psycopg2
from urllib.parse import urlparse

def check_database_schema():
    """Check the database schema to identify issues"""
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL environment variable found")
        return
    
    try:
        # Parse the database URL
        parsed = urlparse(db_url)
        print(f"Connecting to database: {parsed.hostname}:{parsed.port}/{parsed.path[1:]}")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("\n=== CHECKING USERS TABLE ===")
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        users_exists = cursor.fetchone()[0]
        print(f"Users table exists: {users_exists}")
        
        if users_exists:
            # Check users table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default, 
                       character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """)
            
            print("\n=== USERS TABLE COLUMNS ===")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Check for primary key on users table
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'users' 
                AND tc.constraint_type = 'PRIMARY KEY'
            """)
            
            pk_columns = cursor.fetchall()
            print(f"\n=== USERS PRIMARY KEY ===")
            if pk_columns:
                for pk in pk_columns:
                    print(f"  Primary key: {pk[0]}")
            else:
                print("  NO PRIMARY KEY FOUND!")
            
            # Check unique constraints on users table
            cursor.execute("""
                SELECT kcu.column_name, tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'users' 
                AND tc.constraint_type = 'UNIQUE'
            """)
            
            unique_constraints = cursor.fetchall()
            print(f"\n=== USERS UNIQUE CONSTRAINTS ===")
            for uc in unique_constraints:
                print(f"  Unique: {uc[0]} (constraint: {uc[1]})")
        
        print("\n=== CHECKING PAPER_TRADES TABLE ===")
        # Check if paper_trades table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'paper_trades'
            )
        """)
        paper_trades_exists = cursor.fetchone()[0]
        print(f"Paper_trades table exists: {paper_trades_exists}")
        
        if paper_trades_exists:
            # Check paper_trades foreign keys
            cursor.execute("""
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
            """)
            
            print("\n=== PAPER_TRADES FOREIGN KEYS ===")
            fks = cursor.fetchall()
            for fk in fks:
                print(f"  FK: {fk[1]} -> {fk[2]}.{fk[3]} (constraint: {fk[0]})")
        
        # Check for any existing data in users table
        if users_exists:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"\n=== USERS TABLE DATA ===")
            print(f"  Total users: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT id, username, email FROM users LIMIT 5")
                users = cursor.fetchall()
                print("  Sample users:")
                for user in users:
                    print(f"    ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
        
        cursor.close()
        conn.close()
        print("\n✅ Database schema check completed successfully")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_schema() 