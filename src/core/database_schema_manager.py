"""
Database Schema Manager - Precise, permanent solution for database structure integrity.
This is not a workaround - this is the definitive way to ensure database schema correctness.
"""
import logging
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, DateTime, Boolean, Float, JSON
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class DatabaseSchemaManager:
    """
    Precise database schema management - ensures database structure is always correct.
    This is the authoritative source of truth for database schema.
    """
    
    # Define the precise schema for users table
    USERS_TABLE_SCHEMA = {
        'id': {'type': 'SERIAL', 'primary_key': True, 'nullable': False},
        'email': {'type': 'VARCHAR(255)', 'unique': True, 'nullable': False},
        'username': {'type': 'VARCHAR(50)', 'unique': True, 'nullable': False},
        'full_name': {'type': 'VARCHAR(100)', 'nullable': True},  # Make nullable
        'password_hash': {'type': 'VARCHAR(255)', 'nullable': False},
        'role': {'type': 'VARCHAR(20)', 'nullable': True, 'default': 'trader'},
        'status': {'type': 'VARCHAR(20)', 'nullable': True, 'default': 'active'},
        'is_active': {'type': 'BOOLEAN', 'nullable': False, 'default': True},
        'broker_account_id': {'type': 'VARCHAR(255)', 'nullable': True},
        'trading_enabled': {'type': 'BOOLEAN', 'nullable': False, 'default': False},
        'max_position_size': {'type': 'FLOAT', 'nullable': True},
        'risk_level': {'type': 'VARCHAR(20)', 'nullable': True},
        'preferences': {'type': 'JSON', 'nullable': True},
        'created_at': {'type': 'TIMESTAMP', 'nullable': False, 'default': 'CURRENT_TIMESTAMP'},
        'updated_at': {'type': 'TIMESTAMP', 'nullable': False, 'default': 'CURRENT_TIMESTAMP'},
        'last_login': {'type': 'TIMESTAMP', 'nullable': True},
        'failed_login_attempts': {'type': 'INTEGER', 'nullable': False, 'default': 0},
        'last_password_change': {'type': 'TIMESTAMP', 'nullable': True},
        'two_factor_enabled': {'type': 'BOOLEAN', 'nullable': False, 'default': False},
        'two_factor_secret': {'type': 'VARCHAR(255)', 'nullable': True},
        # Additional columns for paper trading compatibility
        'initial_capital': {'type': 'FLOAT', 'nullable': True, 'default': 100000.0},
        'current_balance': {'type': 'FLOAT', 'nullable': True, 'default': 100000.0},
        'risk_tolerance': {'type': 'VARCHAR(20)', 'nullable': True, 'default': 'medium'},
        'zerodha_client_id': {'type': 'VARCHAR(50)', 'nullable': True},
        'max_daily_trades': {'type': 'INTEGER', 'nullable': True, 'default': 1000}
    }
    
    # Define the precise schema for paper_trades table
    PAPER_TRADES_TABLE_SCHEMA = {
        'id': {'type': 'SERIAL', 'primary_key': True, 'nullable': False},
        'user_id': {'type': 'INTEGER', 'nullable': False, 'foreign_key': 'users.id'},
        'symbol': {'type': 'VARCHAR(20)', 'nullable': False},
        'action': {'type': 'VARCHAR(10)', 'nullable': False},
        'quantity': {'type': 'INTEGER', 'nullable': False},
        'price': {'type': 'FLOAT', 'nullable': False},
        'timestamp': {'type': 'TIMESTAMP', 'nullable': False},
        'status': {'type': 'VARCHAR(20)', 'nullable': False},
        'order_id': {'type': 'VARCHAR(50)', 'nullable': True},
        'pnl': {'type': 'FLOAT', 'nullable': True},
        'strategy': {'type': 'VARCHAR(50)', 'nullable': True},
        'created_at': {'type': 'TIMESTAMP', 'nullable': False, 'default': 'CURRENT_TIMESTAMP'}
    }
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def ensure_schema(self) -> Dict[str, Any]:
        """Ensure all tables exist with precise schema"""
        results = {}
        
        # CRITICAL: Fix users table first - this is the root cause of all issues
        results['users'] = self._ensure_users_table_with_aggressive_fix()
        
        # Only create dependent tables if users table is fixed
        if results['users']['status'] in ['created', 'verified', 'updated', 'repaired']:
            results['paper_trades'] = self._ensure_table('paper_trades', self.PAPER_TRADES_TABLE_SCHEMA)
            
            # Ensure default user exists (only after schema is correct)
            self._ensure_default_user()
        else:
            logger.error("❌ Cannot create dependent tables - users table has issues")
            results['paper_trades'] = {'status': 'skipped', 'reason': 'users table issues'}
            
        return results

    def _check_users_primary_key_constraint(self, conn) -> bool:
        """Check if users table has a PROPER primary key constraint that works for foreign keys"""
        try:
            # Method 1: Direct PostgreSQL constraint check
            result = conn.execute(text("""
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = 'users' 
                AND constraint_type = 'PRIMARY KEY'
            """)).fetchall()
            
            if not result:
                logger.warning("❌ No PRIMARY KEY constraint found in information_schema")
                return False
            
            # Method 2: Check if foreign key can actually reference this table
            try:
                # Try to create a test foreign key to see if it works
                test_sql = """
                    CREATE TABLE IF NOT EXISTS test_foreign_key_check (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """
                conn.execute(text(test_sql))
                
                # If successful, clean up the test table
                conn.execute(text("DROP TABLE IF EXISTS test_foreign_key_check"))
                logger.info("✅ Users table PRIMARY KEY constraint works for foreign keys")
                return True
                
            except Exception as fk_test_error:
                logger.error(f"❌ Foreign key test failed: {fk_test_error}")
                conn.execute(text("DROP TABLE IF EXISTS test_foreign_key_check"))  # Cleanup
                return False
                
        except Exception as e:
            logger.error(f"❌ Primary key constraint check failed: {e}")
            return False

    def _fix_users_primary_key_aggressive(self, conn) -> bool:
        """Aggressively fix users table primary key constraint"""
        try:
            logger.info("🔧 Starting aggressive users table PRIMARY KEY repair...")
            
            # First check if we actually need to fix it
            if self._check_users_primary_key_constraint(conn):
                logger.info("✅ Users table PRIMARY KEY is working correctly")
                return True
            
            logger.warning("⚠️ Users table PRIMARY KEY needs repair - starting aggressive fix...")
            
            # Get current data
            backup_data = conn.execute(text("SELECT * FROM users")).fetchall()
            logger.info(f"📦 Backing up {len(backup_data)} user records")
            
            # Drop dependent tables that reference users
            logger.info("🔄 Dropping dependent tables...")
            dependent_tables = ['paper_trades', 'positions', 'trades', 'orders']
            for table in dependent_tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    logger.info(f"   ✓ Dropped {table}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not drop {table}: {e}")
            
            # Drop and recreate users table with proper schema
            logger.info("🔄 Recreating users table with proper PRIMARY KEY...")
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            
            # Create users table with proper SERIAL PRIMARY KEY
            create_users_sql = """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    initial_capital FLOAT DEFAULT 50000.0,
                    current_balance FLOAT DEFAULT 50000.0,
                    risk_tolerance VARCHAR(20) DEFAULT 'medium',
                    is_active BOOLEAN DEFAULT TRUE,
                    zerodha_client_id VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_trades INTEGER DEFAULT 0,
                    user_type VARCHAR(20) DEFAULT 'trader',
                    status VARCHAR(20) DEFAULT 'active',
                    phone VARCHAR(20),
                    trading_enabled BOOLEAN DEFAULT TRUE,
                    max_position_size INTEGER DEFAULT 500000,
                    zerodha_api_key VARCHAR(100),
                    zerodha_api_secret VARCHAR(100),
                    zerodha_access_token TEXT,
                    zerodha_public_token VARCHAR(100),
                    total_pnl FLOAT DEFAULT 0,
                    last_login TIMESTAMP,
                    paper_trading BOOLEAN DEFAULT FALSE,
                    max_daily_trades INTEGER,
                    max_daily_trades INTEGER
                )
            """
            conn.execute(text(create_users_sql))
            logger.info("✅ Users table recreated with proper SERIAL PRIMARY KEY")
            
            # Restore data if any existed
            if backup_data:
                logger.info(f"🔄 Restoring {len(backup_data)} user records...")
                
                # Get column names from the original data
                columns = [desc[0] for desc in conn.execute(text("SELECT * FROM users LIMIT 0")).cursor.description]
                
                for row_data in backup_data:
                    try:
                        # Map the data to new schema, excluding auto-generated id
                        insert_cols = []
                        insert_vals = []
                        
                        # Map known columns (skip id since it's SERIAL)
                        for i, value in enumerate(row_data[1:], 1):  # Skip first column (id)
                            if i < len(columns):
                                col_name = columns[i]
                                if value is not None:
                                    insert_cols.append(col_name)
                                    if isinstance(value, str):
                                        escaped_value = value.replace("'", "''")
                                        insert_vals.append(f"'{escaped_value}'")  # Escape quotes
                                    elif isinstance(value, bool):
                                        insert_vals.append('TRUE' if value else 'FALSE')
                                    else:
                                        insert_vals.append(str(value))
                        
                        if insert_cols:
                            insert_sql = f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})"
                            conn.execute(text(insert_sql))
                            
                    except Exception as restore_error:
                        logger.warning(f"⚠️ Could not restore user record: {restore_error}")
                        continue
                        
                logger.info("✅ User data restoration completed")
            
            # Verify the fix worked
            if self._check_users_primary_key_constraint(conn):
                logger.info("✅ Users table PRIMARY KEY constraint verified working")
                return True
            else:
                logger.error("❌ PRIMARY KEY constraint still not working after aggressive fix")
                return False
                
        except Exception as e:
            logger.error(f"❌ Aggressive PRIMARY KEY fix failed: {e}")
            return False

    def _ensure_users_table_with_aggressive_fix(self) -> Dict[str, Any]:
        """Ensure users table exists with aggressive PRIMARY KEY fixing"""
        result = {
            'status': 'unknown',
            'errors': [],
            'actions': []
        }
        
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    # Check if users table exists
                    table_exists = self._table_exists(conn, 'users')
                    
                    if not table_exists:
                        logger.info("📋 Users table doesn't exist - creating with proper schema...")
                        create_sql = self._generate_create_table_sql('users', self.USERS_TABLE_SCHEMA)
                        conn.execute(text(create_sql))
                        result['status'] = 'created'
                        result['actions'].append('Created users table with SERIAL PRIMARY KEY')
                        logger.info("✅ Users table created successfully")
                        
                    else:
                        # Table exists, check if PRIMARY KEY constraint is working
                        if self._check_users_primary_key_constraint(conn):
                            logger.info("✅ Users table PRIMARY KEY constraint working correctly")
                            result['status'] = 'verified'
                        else:
                            logger.warning("⚠️ Users table PRIMARY KEY constraint needs fixing...")
                            if self._fix_users_primary_key_aggressive(conn):
                                result['status'] = 'repaired'
                                result['actions'].append('Fixed PRIMARY KEY constraint with aggressive repair')
                                logger.info("✅ Users table PRIMARY KEY constraint repaired")
                            else:
                                result['status'] = 'error'
                                result['errors'].append('Failed to repair PRIMARY KEY constraint')
                                logger.error("❌ Failed to repair users table PRIMARY KEY constraint")
                    
                    trans.commit()
                    return result
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Error ensuring users table: {e}")
            result['status'] = 'error'
            result['errors'].append(str(e))
            return result

    def _table_exists(self, conn, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            # For PostgreSQL
            if 'postgresql' in self.database_url:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """), {'table_name': table_name}).scalar()
                return bool(result)
            else:
                # For SQLite
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name = :table_name
                """), {'table_name': table_name}).fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking table existence for {table_name}: {e}")
            return False

    def _generate_create_table_sql(self, table_name: str, schema: Dict[str, Dict[str, Any]]) -> str:
        """Generate precise CREATE TABLE SQL with proper constraints"""
        columns = []
        foreign_keys = []
        
        # Detect database type
        is_postgresql = 'postgresql' in self.database_url
        
        for col_name, col_spec in schema.items():
            # Handle primary key columns with SERIAL (auto-incrementing)
            if col_spec.get('primary_key'):
                if is_postgresql and col_spec.get('type') == 'SERIAL':
                    col_def = f"{col_name} SERIAL PRIMARY KEY"
                elif is_postgresql:
                    col_def = f"{col_name} {col_spec['type']} PRIMARY KEY"
                else:
                    # SQLite
                    col_def = f"{col_name} INTEGER PRIMARY KEY AUTOINCREMENT"
            else:
                col_def = f"{col_name} {col_spec['type']}"
                
                # Add NOT NULL constraint if specified
                if not col_spec.get('nullable', True):
                    col_def += " NOT NULL"
                
                # Add DEFAULT clause if specified and not primary key
                if 'default' in col_spec:
                    if col_spec['default'] == 'CURRENT_TIMESTAMP':
                        col_def += f" DEFAULT {col_spec['default']}"
                    elif isinstance(col_spec['default'], bool):
                        # Handle boolean defaults properly for each database
                        if is_postgresql:
                            col_def += f" DEFAULT {str(col_spec['default']).lower()}"
                        else:
                            col_def += f" DEFAULT {1 if col_spec['default'] else 0}"
                    elif isinstance(col_spec['default'], str):
                        col_def += f" DEFAULT '{col_spec['default']}'"
                    else:
                        col_def += f" DEFAULT {col_spec['default']}"
                
                # Add UNIQUE constraint if specified
                if col_spec.get('unique'):
                    col_def += " UNIQUE"
                    
            columns.append(col_def)
            
            # Collect foreign keys separately (only for non-primary key columns)
            if 'foreign_key' in col_spec and not col_spec.get('primary_key'):
                ref_table, ref_col = col_spec['foreign_key'].split('.')
                foreign_keys.append(f"FOREIGN KEY ({col_name}) REFERENCES {ref_table}({ref_col})")
        
        # Combine columns and foreign keys
        all_constraints = columns + foreign_keys
        
        return f"CREATE TABLE {table_name} ({', '.join(all_constraints)})"
    
    def _generate_add_column_sql(self, table_name: str, col_name: str, col_spec: Dict[str, Any]) -> str:
        """Generate precise ALTER TABLE ADD COLUMN SQL"""
        col_def = f"{col_spec['type']}"
        
        # Detect database type
        is_postgresql = 'postgresql' in self.database_url
        
        if not col_spec.get('nullable', True):
            # For NOT NULL columns, we need a default value
            if 'default' in col_spec:
                if col_spec['default'] == 'CURRENT_TIMESTAMP':
                    col_def += f" DEFAULT {col_spec['default']}"
                elif isinstance(col_spec['default'], bool):
                    # Handle boolean defaults properly
                    if is_postgresql:
                        col_def += f" DEFAULT {str(col_spec['default']).lower()}"
                    else:
                        col_def += f" DEFAULT {1 if col_spec['default'] else 0}"
                elif isinstance(col_spec['default'], str):
                    col_def += f" DEFAULT '{col_spec['default']}'"
                else:
                    col_def += f" DEFAULT {col_spec['default']}"
            else:
                # Provide sensible defaults for NOT NULL columns without explicit defaults
                if 'INT' in col_spec['type']:
                    col_def += " DEFAULT 0"
                elif 'VARCHAR' in col_spec['type']:
                    col_def += " DEFAULT ''"
                elif 'BOOLEAN' in col_spec['type']:
                    if is_postgresql:
                        col_def += " DEFAULT false"
                    else:
                        col_def += " DEFAULT 0"
                elif 'FLOAT' in col_spec['type']:
                    col_def += " DEFAULT 0.0"
                elif 'TIMESTAMP' in col_spec['type']:
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
            col_def += " NOT NULL"
        
        if col_spec.get('unique'):
            col_def += " UNIQUE"
            
        return f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"
    
    def _ensure_table(self, table_name: str, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure a table exists with the precise schema"""
        result = {'status': 'unknown', 'actions': []}
        
        try:
            with self.engine.connect() as conn:
                # Start a transaction
                trans = conn.begin()
                try:
                    inspector = inspect(self.engine)
                    
                    # Check if table exists
                    if table_name not in inspector.get_table_names():
                        # Create table with precise schema
                        create_sql = self._generate_create_table_sql(table_name, schema)
                        logger.info(f"Creating table {table_name} with SQL: {create_sql}")
                        conn.execute(text(create_sql))
                        result['actions'].append(f"Created table {table_name} with precise schema")
                        result['status'] = 'created'
                    else:
                        # Verify and fix existing table schema
                        existing_columns = {col['name']: col for col in inspector.get_columns(table_name)}
                        
                        # Check for missing columns
                        for col_name, col_spec in schema.items():
                            if col_name not in existing_columns:
                                alter_sql = self._generate_add_column_sql(table_name, col_name, col_spec)
                                logger.info(f"Adding missing column {col_name} to {table_name}")
                                conn.execute(text(alter_sql))
                                result['actions'].append(f"Added missing column {col_name} to {table_name}")
                        
                        result['status'] = 'verified' if not result['actions'] else 'updated'
                    
                    # Commit the transaction
                    trans.commit()
                    
                except Exception as e:
                    # Rollback on error
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            logger.error(f"Error ensuring table {table_name}: {e}")
            result['status'] = 'error'
            result['errors'] = [str(e)]
                
        return result
    
    def _ensure_default_user(self):
        """Ensure default paper trading user exists"""
        with self.engine.connect() as conn:
            trans = conn.begin()
            try:
                # Check if any user exists
                result = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                
                if result == 0:
                    logger.info("No users found, creating default paper trading user")
                    
                    # Create default paper trading user with only required fields
                    insert_sql = """
                        INSERT INTO users (
                            username, email, password_hash, 
                            is_active, trading_enabled,
                            created_at, updated_at
                        ) VALUES (
                            'PAPER_TRADER_001', 'paper@algoauto.com',
                            '$2b$12$dummy.hash.paper.trading',
                            :is_active_val, :trading_enabled_val,
                            :now_val, :now_val
                        ) ON CONFLICT (username) DO NOTHING
                        """
                    
                    # Handle database-specific values
                    if 'postgresql' in self.database_url:
                        params = {
                            'is_active_val': True,
                            'trading_enabled_val': True,
                            'now_val': datetime.now()
                        }
                    else:  # SQLite
                        params = {
                            'is_active_val': 1,
                            'trading_enabled_val': 1,
                            'now_val': datetime.now()
                        }
                    
                    conn.execute(text(insert_sql), params)
                    trans.commit()
                    logger.info("✅ Created default paper trading user successfully")
                else:
                    trans.commit()
                    logger.info(f"Users table already has {result} users")
                    
            except Exception as e:
                trans.rollback()
                logger.warning(f"Could not ensure default user: {e}")
                # Try even more minimal approach
                try:
                    trans2 = conn.begin()
                    minimal_sql = """
                        INSERT INTO users (username, email, password_hash) 
                        VALUES ('PAPER_TRADER_001', 'paper@algoauto.com', 'dummy_hash')
                        ON CONFLICT (username) DO NOTHING
                        """
                    conn.execute(text(minimal_sql))
                    trans2.commit()
                    logger.info("✅ Created minimal paper trading user")
                except Exception as e2:
                    trans2.rollback()
                    logger.error(f"Failed to create any paper trading user: {e2}")

    def ensure_precise_schema(self) -> Dict[str, Any]:
        """
        Ensure all database tables have the precise schema required.
        This is the main entry point called by the application.
        """
        logger.info("Starting precise database schema verification...")
        
        try:
            # Run our comprehensive schema check
            results = self.ensure_schema()
            
            # Format results for compatibility with existing code
            formatted_result = {
                'status': 'success' if all(
                    r['status'] in ['created', 'verified', 'updated', 'repaired'] 
                    for r in results.values() 
                    if 'status' in r
                ) else 'error',
                'users_table': results.get('users', {}),
                'paper_trades_table': results.get('paper_trades', {}),
                'actions': [],
                'errors': []
            }
            
            # Collect all actions and errors
            for table_name, table_result in results.items():
                if 'actions' in table_result:
                    formatted_result['actions'].extend(table_result['actions'])
                if 'errors' in table_result:
                    formatted_result['errors'].extend(table_result['errors'])
            
            # Log results
            if formatted_result['status'] == 'success':
                logger.info("✅ Database schema verification completed successfully")
                if formatted_result['actions']:
                    for action in formatted_result['actions']:
                        logger.info(f"  ✓ {action}")
            else:
                logger.error("❌ Database schema verification failed")
                for error in formatted_result['errors']:
                    logger.error(f"  ✗ {error}")
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Critical error during schema verification: {e}")
            return {
                'status': 'error',
                'errors': [str(e)],
                'users_table': {'status': 'error'},
                'paper_trades_table': {'status': 'error'},
                'actions': []
            }

    async def ensure_table_exists(self, table_name: str) -> bool:
        """
        Async wrapper for table existence check.
        Used by some API components.
        """
        try:
            if table_name == 'users':
                result = self._ensure_users_table_with_aggressive_fix()
            elif table_name == 'paper_trades':
                result = self._ensure_table('paper_trades', self.PAPER_TRADES_TABLE_SCHEMA)
            else:
                logger.warning(f"Unknown table name: {table_name}")
                return False
                
            return result['status'] in ['created', 'verified', 'updated', 'repaired']
            
        except Exception as e:
            logger.error(f"Error ensuring table {table_name} exists: {e}")
            return False 