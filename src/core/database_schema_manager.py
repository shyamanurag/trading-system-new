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
        
        # Ensure tables in dependency order (users first, then tables that reference it)
        results['users'] = self._ensure_table('users', self.USERS_TABLE_SCHEMA)
        results['paper_trades'] = self._ensure_table('paper_trades', self.PAPER_TRADES_TABLE_SCHEMA)
        
        # Ensure default user exists (only after schema is correct)
        if results['users']['status'] in ['created', 'verified', 'updated']:
            self._ensure_default_user()
            
        return results
    
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

    def _fix_users_primary_key(self, conn, inspector) -> bool:
        """Fix users table primary key if it's missing"""
        try:
            # Check if users table has a primary key
            pk_constraints = inspector.get_pk_constraint('users')
            
            if not pk_constraints or not pk_constraints.get('constrained_columns'):
                logger.info("❌ Users table missing primary key - attempting repair...")
                
                # Check if id column exists and has data
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE id IS NOT NULL")).scalar()
                
                if result > 0:
                    # Users exist with id values - need to add primary key constraint
                    logger.info("🔧 Adding primary key constraint to existing users table...")
                    
                    # First ensure id is unique and not null
                    conn.execute(text("DELETE FROM users WHERE id IS NULL"))
                    
                    # Remove duplicates keeping the first occurrence
                    conn.execute(text("""
                        DELETE FROM users WHERE id NOT IN (
                            SELECT DISTINCT ON (username) id FROM users ORDER BY username, created_at
                        )
                    """))
                    
                    # Add primary key constraint
                    conn.execute(text("ALTER TABLE users ADD PRIMARY KEY (id)"))
                    logger.info("✅ Added primary key constraint to users.id")
                    return True
                else:
                    # No users exist - add sequence and primary key
                    logger.info("🔧 Setting up primary key for empty users table...")
                    conn.execute(text("ALTER TABLE users ADD PRIMARY KEY (id)"))
                    
                    # Ensure id has proper sequence
                    conn.execute(text("CREATE SEQUENCE IF NOT EXISTS users_id_seq"))
                    conn.execute(text("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq')"))
                    conn.execute(text("ALTER SEQUENCE users_id_seq OWNED BY users.id"))
                    
                    logger.info("✅ Set up primary key for users table")
                    return True
            else:
                logger.info("✅ Users table already has primary key")
                return False
                
        except Exception as e:
            logger.error(f"Failed to fix users primary key: {e}")
            return False
    
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
                        # Special handling for users table primary key issues
                        if table_name == 'users':
                            pk_fixed = self._fix_users_primary_key(conn, inspector)
                            if pk_fixed:
                                result['actions'].append("Fixed users table primary key constraint")
                        
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
                    r['status'] in ['created', 'verified', 'updated'] 
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
                result = self._ensure_table('users', self.USERS_TABLE_SCHEMA)
            elif table_name == 'paper_trades':
                result = self._ensure_table('paper_trades', self.PAPER_TRADES_TABLE_SCHEMA)
            else:
                logger.warning(f"Unknown table name: {table_name}")
                return False
                
            return result['status'] in ['created', 'verified', 'updated']
            
        except Exception as e:
            logger.error(f"Error ensuring table {table_name} exists: {e}")
            return False 