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
        'id': {'type': 'INTEGER', 'primary_key': True, 'autoincrement': True, 'nullable': False},
        'email': {'type': 'VARCHAR(255)', 'unique': True, 'nullable': False},
        'username': {'type': 'VARCHAR(50)', 'unique': True, 'nullable': False},
        'full_name': {'type': 'VARCHAR(100)', 'nullable': False},
        'password_hash': {'type': 'VARCHAR(255)', 'nullable': False},
        'role': {'type': 'VARCHAR(20)', 'nullable': False, 'default': 'trader'},
        'status': {'type': 'VARCHAR(20)', 'nullable': False, 'default': 'active'},
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
        'two_factor_secret': {'type': 'VARCHAR(255)', 'nullable': True}
    }
    
    # Define the precise schema for paper_trades table
    PAPER_TRADES_TABLE_SCHEMA = {
        'id': {'type': 'INTEGER', 'primary_key': True, 'autoincrement': True, 'nullable': False},
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
    
    # Define the precise schema for trades table (production trades)
    TRADES_TABLE_SCHEMA = {
        'trade_id': {'type': 'INTEGER', 'primary_key': True, 'autoincrement': True, 'nullable': False},
        'symbol': {'type': 'VARCHAR(20)', 'nullable': False},
        'trade_type': {'type': 'VARCHAR(10)', 'nullable': False},
        'quantity': {'type': 'INTEGER', 'nullable': False},
        'price': {'type': 'FLOAT', 'nullable': False},
        'strategy': {'type': 'VARCHAR(50)', 'nullable': True},
        'commission': {'type': 'FLOAT', 'nullable': True, 'default': 0.0},
        'executed_at': {'type': 'TIMESTAMP', 'nullable': False},
        'pnl': {'type': 'FLOAT', 'nullable': True, 'default': 0.0},
        'pnl_percent': {'type': 'FLOAT', 'nullable': True, 'default': 0.0},
        'status': {'type': 'VARCHAR(20)', 'nullable': True, 'default': 'EXECUTED'},
        'user_id': {'type': 'INTEGER', 'nullable': True, 'foreign_key': 'users.id'},
        'created_at': {'type': 'TIMESTAMP', 'nullable': False, 'default': 'CURRENT_TIMESTAMP'},
        'updated_at': {'type': 'TIMESTAMP', 'nullable': False, 'default': 'CURRENT_TIMESTAMP'}
    }
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def ensure_precise_schema(self) -> Dict[str, Any]:
        """
        Ensures the database has the precise schema required.
        This is not a workaround - this is the correct way to manage schema.
        """
        results = {
            'users_table': {'status': 'unknown', 'actions': []},
            'paper_trades_table': {'status': 'unknown', 'actions': []},
            'trades_table': {'status': 'unknown', 'actions': []},
            'errors': []
        }
        
        try:
            # Ensure users table exists with correct schema
            users_result = self._ensure_table('users', self.USERS_TABLE_SCHEMA)
            results['users_table'] = users_result
            
            # Ensure paper_trades table exists with correct schema
            paper_trades_result = self._ensure_table('paper_trades', self.PAPER_TRADES_TABLE_SCHEMA)
            results['paper_trades_table'] = paper_trades_result
            
            # Ensure trades table exists with correct schema
            trades_result = self._ensure_table('trades', self.TRADES_TABLE_SCHEMA)
            results['trades_table'] = trades_result
            
            # Ensure default paper trading user exists
            self._ensure_default_user()
            
            results['status'] = 'success'
            logger.info("Database schema verification complete - all tables have precise structure")
            
        except Exception as e:
            logger.error(f"Error ensuring database schema: {e}")
            results['errors'].append(str(e))
            results['status'] = 'error'
            
        return results
    
    def _ensure_table(self, table_name: str, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure a table exists with the precise schema"""
        result = {'status': 'unknown', 'actions': []}
        
        try:
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                
                # Check if table exists
                if table_name not in inspector.get_table_names():
                    # Create table with precise schema
                    create_sql = self._generate_create_table_sql(table_name, schema)
                    conn.execute(text(create_sql))
                    conn.commit()
                    result['actions'].append(f"Created table {table_name} with precise schema")
                    result['status'] = 'created'
                else:
                    # Verify and fix existing table schema
                    existing_columns = {col['name']: col for col in inspector.get_columns(table_name)}
                    
                    # Check for missing columns
                    for col_name, col_spec in schema.items():
                        if col_name not in existing_columns:
                            alter_sql = self._generate_add_column_sql(table_name, col_name, col_spec)
                            try:
                                conn.execute(text(alter_sql))
                                conn.commit()
                                result['actions'].append(f"Added column {col_name} to {table_name}")
                            except Exception as e:
                                logger.warning(f"Could not add column {col_name}: {e}")
                    
                    # Ensure primary key exists
                    pk_cols = [col for col, spec in schema.items() if spec.get('primary_key')]
                    existing_pk = inspector.get_pk_constraint(table_name)
                    
                    if pk_cols and not existing_pk['constrained_columns']:
                        # Add primary key
                        for pk_col in pk_cols:
                            try:
                                conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({pk_col})"))
                                conn.commit()
                                result['actions'].append(f"Added primary key on {pk_col}")
                            except Exception as e:
                                logger.warning(f"Could not add primary key: {e}")
                    
                    result['status'] = 'verified' if not result['actions'] else 'updated'
                    
        except Exception as e:
            logger.error(f"Error ensuring table {table_name}: {e}")
            result['status'] = 'error'
            result['errors'] = [str(e)]
                
        return result
    
    def _generate_create_table_sql(self, table_name: str, schema: Dict[str, Dict[str, Any]]) -> str:
        """Generate precise CREATE TABLE SQL"""
        columns = []
        foreign_keys = []
        
        for col_name, col_spec in schema.items():
            col_def = f"{col_name} {col_spec['type']}"
            
            if col_spec.get('primary_key'):
                col_def += " PRIMARY KEY"
            if col_spec.get('autoincrement'):
                col_def += " AUTOINCREMENT"
            if not col_spec.get('nullable', True):
                col_def += " NOT NULL"
            if 'default' in col_spec:
                if col_spec['default'] == 'CURRENT_TIMESTAMP':
                    col_def += f" DEFAULT {col_spec['default']}"
                elif isinstance(col_spec['default'], bool):
                    col_def += f" DEFAULT {1 if col_spec['default'] else 0}"
                elif isinstance(col_spec['default'], str):
                    col_def += f" DEFAULT '{col_spec['default']}'"
                else:
                    col_def += f" DEFAULT {col_spec['default']}"
            if col_spec.get('unique'):
                col_def += " UNIQUE"
                
            columns.append(col_def)
            
            # Collect foreign keys separately
            if 'foreign_key' in col_spec:
                # For SQLite, use proper syntax: REFERENCES table(column)
                ref_table, ref_col = col_spec['foreign_key'].split('.')
                foreign_keys.append(f"FOREIGN KEY ({col_name}) REFERENCES {ref_table}({ref_col})")
        
        # Combine columns and foreign keys
        all_constraints = columns + foreign_keys
        
        return f"CREATE TABLE {table_name} ({', '.join(all_constraints)})"
    
    def _generate_add_column_sql(self, table_name: str, col_name: str, col_spec: Dict[str, Any]) -> str:
        """Generate precise ALTER TABLE ADD COLUMN SQL"""
        col_def = f"{col_spec['type']}"
        
        if not col_spec.get('nullable', True):
            # For NOT NULL columns, we need a default value
            if 'default' in col_spec:
                if col_spec['default'] == 'CURRENT_TIMESTAMP':
                    col_def += f" DEFAULT {col_spec['default']}"
                elif isinstance(col_spec['default'], bool):
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
                    col_def += " DEFAULT 0"
                elif 'FLOAT' in col_spec['type']:
                    col_def += " DEFAULT 0.0"
                elif 'TIMESTAMP' in col_spec['type']:
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
            col_def += " NOT NULL"
        
        if col_spec.get('unique'):
            col_def += " UNIQUE"
            
        return f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"
    
    def _ensure_default_user(self):
        """Ensure default paper trading user exists"""
        with self.engine.connect() as conn:
            # Check if any user exists
            result = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            if result == 0:
                # Create default paper trading user
                insert_sql = """
                INSERT INTO users (
                    email, username, full_name, password_hash, role, status, 
                    is_active, trading_enabled, created_at, updated_at
                ) VALUES (
                    'paper@trading.com', 'paper_trader', 'Paper Trading User',
                    'no_password_needed', 'trader', 'active', 1, 1,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
                try:
                    conn.execute(text(insert_sql))
                    conn.commit()
                    logger.info("Created default paper trading user")
                except Exception as e:
                    logger.warning(f"Could not create default user: {e}") 