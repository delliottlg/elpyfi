"""
Database Writer Module

Handles all database operations and pg_notify events for the engine.
Uses synchronous psycopg2 to fit with existing codebase.
"""

import psycopg2
from psycopg2 import errors as pg_errors
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import asdict
import time

logger = logging.getLogger(__name__)


class SchemaMismatchError(Exception):
    """Raised when database schema doesn't match expected structure"""
    def __init__(self, message: str, missing_columns: List[str] = None, missing_tables: List[str] = None,
                 schema_issues: Dict[str, List[str]] = None):
        super().__init__(message)
        self.missing_columns = missing_columns or []
        self.missing_tables = missing_tables or []
        self.schema_issues = schema_issues or {}
    
    def get_fix_sql(self) -> str:
        """Generate SQL to fix the schema mismatch"""
        sql_statements = []
        
        # Generate CREATE TABLE statements for missing tables
        if self.missing_tables:
            temp_writer = DatabaseWriter.__new__(DatabaseWriter)
            full_schema = temp_writer.get_schema_creation_sql()
            
            # Extract CREATE TABLE statements for missing tables
            for table in self.missing_tables:
                if table == 'positions':
                    sql_statements.append("""CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(18,8) NOT NULL,
    entry_price DECIMAL(18,8) NOT NULL,
    current_price DECIMAL(18,8) NOT NULL,
    unrealized_pl DECIMAL(18,8) DEFAULT 0,
    realized_pl DECIMAL(18,8) DEFAULT 0,
    strategy VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    order_id VARCHAR(100) NOT NULL,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")
                elif table == 'signals':
                    sql_statements.append("""CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    expected_profit DECIMAL(18,8),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")
        
        # Generate ALTER TABLE statements for missing columns
        if self.schema_issues:
            column_types = {
                'order_id': 'VARCHAR(100) NOT NULL',
                'closed_at': 'TIMESTAMP',
                'metadata': 'JSONB',
                'expected_profit': 'DECIMAL(18,8)'
            }
            
            for table, missing_cols in self.schema_issues.items():
                for col in missing_cols:
                    col_type = column_types.get(col, 'VARCHAR(255)')
                    # Handle NOT NULL columns more gracefully
                    if 'NOT NULL' in col_type and col != 'order_id':
                        sql_statements.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type.replace(' NOT NULL', '')};")
                    elif col == 'order_id':
                        # Special handling for order_id to provide default value
                        sql_statements.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} VARCHAR(100);")
                        sql_statements.append(f"UPDATE {table} SET {col} = 'LEGACY_' || id::text WHERE {col} IS NULL;")
                        sql_statements.append(f"ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL;")
                    else:
                        sql_statements.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type};")
        
        return '\n'.join(sql_statements) if sql_statements else ''


class DatabaseWriter:
    """Handles database writes and notifications"""
    
    # Expected schema definition
    EXPECTED_SCHEMA = {
        'positions': [
            'id', 'symbol', 'quantity', 'entry_price', 'current_price',
            'unrealized_pl', 'realized_pl', 'strategy', 'status', 'order_id', 'closed_at'
        ],
        'signals': [
            'id', 'strategy', 'symbol', 'action', 'confidence',
            'expected_profit', 'metadata', 'created_at'
        ]
    }
    
    def __init__(self, connection_string: str = "postgresql://d@localhost/elpyfi"):
        self.connection_string = connection_string
        self.conn = None
        self.cur = None
        self.schema_validated = False
        self.last_schema_error = None
        self._schema_retry_count = 0
        self._max_schema_retries = 3
        self.available_columns = {}  # Track which columns actually exist
        self._connect()
        
        # Validate schema but don't fail initialization
        try:
            self._validate_schema()
        except SchemaMismatchError as e:
            self.last_schema_error = e
            logger.warning("Schema validation failed on initialization - continuing with degraded mode")
            # Re-raise to be handled by initialize_db_writer
            raise
    
    def _connect(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Establish database connection with retry logic"""
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(self.connection_string)
                self.conn.autocommit = True  # Required for NOTIFY to work
                self.cur = self.conn.cursor()
                logger.info("Connected to PostgreSQL database")
                return
            except psycopg2.OperationalError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error connecting to database: {e}")
                raise
    
    def _validate_schema(self):
        """Validate that database tables exist with expected columns"""
        if not self.conn:
            logger.warning("Cannot validate schema - no database connection")
            return
        
        missing_tables = []
        schema_issues = {}
        
        try:
            for table_name, expected_columns in self.EXPECTED_SCHEMA.items():
                # Check if table exists
                self.cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                table_exists = self.cur.fetchone()[0]
                
                if not table_exists:
                    missing_tables.append(table_name)
                    logger.error(f"Required table '{table_name}' does not exist")
                    continue
                
                # Check columns if table exists
                self.cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s;
                """, (table_name,))
                
                existing_columns = {row[0] for row in self.cur.fetchall()}
                missing_columns = [col for col in expected_columns if col not in existing_columns]
                
                # Track available columns for fallback behavior
                self.available_columns[table_name] = list(existing_columns)
                
                if missing_columns:
                    schema_issues[table_name] = missing_columns
                    logger.error(f"Table '{table_name}' is missing columns: {missing_columns}")
            
            # If there are schema issues, raise detailed error
            if missing_tables or schema_issues:
                error_msg = "Database schema mismatch detected:\n"
                if missing_tables:
                    error_msg += f"Missing tables: {missing_tables}\n"
                if schema_issues:
                    for table, cols in schema_issues.items():
                        error_msg += f"Table '{table}' missing columns: {cols}\n"
                
                raise SchemaMismatchError(
                    error_msg,
                    missing_columns=[col for cols in schema_issues.values() for col in cols],
                    missing_tables=missing_tables,
                    schema_issues=schema_issues
                )
            
            self.schema_validated = True
            logger.info("Database schema validation passed")
            
        except psycopg2.Error as e:
            logger.error(f"Error validating schema: {e}")
            raise
    
    def get_schema_creation_sql(self) -> str:
        """Generate SQL to create the expected schema"""
        sql = """-- ElPyFi Core Database Schema
-- Run this SQL to create the required tables

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(18,8) NOT NULL,
    entry_price DECIMAL(18,8) NOT NULL,
    current_price DECIMAL(18,8) NOT NULL,
    unrealized_pl DECIMAL(18,8) DEFAULT 0,
    realized_pl DECIMAL(18,8) DEFAULT 0,
    strategy VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    order_id VARCHAR(100) NOT NULL,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_strategy ON positions(strategy);

CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    expected_profit DECIMAL(18,8),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_strategy ON signals(strategy);
CREATE INDEX idx_signals_created_at ON signals(created_at);
"""
        return sql
    
    def attempt_schema_revalidation(self) -> bool:
        """Attempt to re-validate schema after potential fixes"""
        if not self.schema_validated and self._schema_retry_count < self._max_schema_retries:
            try:
                logger.info("Attempting to re-validate database schema...")
                self._validate_schema()
                self.last_schema_error = None
                self._schema_retry_count = 0
                logger.info("Schema validation successful after fix!")
                return True
            except SchemaMismatchError as e:
                self._schema_retry_count += 1
                self.last_schema_error = e
                logger.warning(f"Schema still invalid (attempt {self._schema_retry_count}/{self._max_schema_retries})")
                return False
            except Exception as e:
                logger.error(f"Error during schema re-validation: {e}")
                return False
        return self.schema_validated
    
    def _notify(self, event_type: str, data: Dict[str, Any]):
        """Send pg_notify event"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        try:
            self.cur.execute(
                "SELECT pg_notify('trading_events', %s)",
                (json.dumps(event),)
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _parse_db_error(self, error: Exception) -> Tuple[str, str, Optional[Dict]]:
        """Parse database error to identify specific issue type and extract details"""
        error_msg = str(error)
        details = {}
        
        if isinstance(error, pg_errors.UndefinedColumn):
            # Extract column name from error message
            import re
            match = re.search(r'column "([^"]+)" of relation "([^"]+)" does not exist', error_msg)
            if match:
                details['column'] = match.group(1)
                details['table'] = match.group(2)
            return "schema_mismatch", f"Column does not exist: {error_msg}", details
        elif isinstance(error, pg_errors.UndefinedTable):
            # Extract table name from error message
            import re
            match = re.search(r'relation "([^"]+)" does not exist', error_msg)
            if match:
                details['table'] = match.group(1)
            return "schema_mismatch", f"Table does not exist: {error_msg}", details
        elif isinstance(error, pg_errors.NotNullViolation):
            return "data_validation", f"Required field is null: {error_msg}", details
        elif isinstance(error, pg_errors.CheckViolation):
            return "data_validation", f"Check constraint violation: {error_msg}", details
        elif isinstance(error, pg_errors.UniqueViolation):
            return "data_validation", f"Unique constraint violation: {error_msg}", details
        elif isinstance(error, psycopg2.OperationalError):
            return "connection", f"Database connection error: {error_msg}", details
        else:
            return "unknown", error_msg, details
    
    def write_position_opened(self, symbol: str, quantity: float, entry_price: float, 
                            strategy: str, order_id: str):
        """Write new position to database and notify with graceful fallback"""
        try:
            # Always include core columns
            columns = ['symbol', 'quantity', 'entry_price', 'current_price', 'unrealized_pl', 'strategy', 'status']
            values = [symbol, quantity, entry_price, entry_price, 0.0, strategy, 'open']
            
            # Check if order_id column exists
            positions_columns = self.available_columns.get('positions', [])
            if 'order_id' in positions_columns or not positions_columns:
                # Include order_id if column exists or if we don't know (first attempt)
                columns.append('order_id')
                values.append(order_id)
            else:
                logger.warning(f"Column 'order_id' not available in positions table - skipping")
                logger.warning(f"Order ID '{order_id}' will not be recorded in database")
            
            # Build query
            placeholders = ['%s'] * len(values)
            query = f"""
                INSERT INTO positions 
                ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """
            
            self.cur.execute(query, values)
            position_id = self.cur.fetchone()[0]
            
            # Send notification (always include order_id in notification)
            self._notify("position.opened", {
                "id": position_id,
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": entry_price,
                "strategy": strategy,
                "order_id": order_id
            })
            
            logger.info(f"Recorded position opened: {symbol} x{quantity} @ ${entry_price}")
            return position_id
            
        except psycopg2.Error as e:
            error_type, error_msg, details = self._parse_db_error(e)
            
            if error_type == "schema_mismatch":
                # Check if it's specifically the order_id column
                if details.get('column') == 'order_id' and 'order_id' in columns:
                    logger.warning(f"Column 'order_id' does not exist - retrying without it")
                    
                    # Update our tracked columns
                    if 'positions' in self.available_columns:
                        self.available_columns['positions'] = [c for c in self.available_columns['positions'] if c != 'order_id']
                    
                    # Retry without order_id
                    try:
                        columns_retry = ['symbol', 'quantity', 'entry_price', 'current_price', 'unrealized_pl', 'strategy', 'status']
                        values_retry = [symbol, quantity, entry_price, entry_price, 0.0, strategy, 'open']
                        placeholders_retry = ['%s'] * len(values_retry)
                        
                        query_retry = f"""
                            INSERT INTO positions 
                            ({', '.join(columns_retry)})
                            VALUES ({', '.join(placeholders_retry)})
                            RETURNING id
                        """
                        
                        self.cur.execute(query_retry, values_retry)
                        position_id = self.cur.fetchone()[0]
                        
                        # Still send full notification
                        self._notify("position.opened", {
                            "id": position_id,
                            "symbol": symbol,
                            "quantity": quantity,
                            "entry_price": entry_price,
                            "strategy": strategy,
                            "order_id": order_id
                        })
                        
                        logger.warning(f"Position recorded successfully without order_id column")
                        logger.warning(f"Consider adding the column: ALTER TABLE positions ADD COLUMN order_id VARCHAR(100);")
                        return position_id
                        
                    except Exception as retry_error:
                        logger.error(f"Retry without order_id also failed: {retry_error}")
                
                # Log schema mismatch details
                logger.warning(f"Schema mismatch when writing position: {error_msg}")
                
                # Re-validate schema to update our column tracking
                try:
                    self._validate_schema()
                except SchemaMismatchError as schema_error:
                    self.last_schema_error = schema_error
                    logger.warning("Schema validation confirmed mismatch - see startup logs for fix instructions")
                except Exception:
                    pass  # Don't fail on validation errors
                    
            elif error_type == "connection":
                logger.error(f"Database connection lost: {error_msg}")
                # Try to reconnect
                try:
                    self._connect(max_retries=1)
                    logger.info("Reconnected to database")
                except Exception:
                    logger.error("Failed to reconnect to database")
            else:
                logger.error(f"Database error ({error_type}): {error_msg}")
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error writing position: {e}")
            return None
    
    def write_position_closed(self, position_id: int, exit_price: float, realized_pl: float):
        """Update position as closed and notify"""
        try:
            # Update position
            self.cur.execute("""
                UPDATE positions 
                SET status = 'closed',
                    current_price = %s,
                    realized_pl = %s,
                    closed_at = NOW()
                WHERE id = %s
                RETURNING symbol, quantity, strategy
            """, (exit_price, realized_pl, position_id))
            
            result = self.cur.fetchone()
            if result:
                symbol, quantity, strategy = result
                
                # Send notification
                self._notify("position.closed", {
                    "id": position_id,
                    "symbol": symbol,
                    "quantity": quantity,
                    "exit_price": exit_price,
                    "realized_pl": realized_pl,
                    "strategy": strategy
                })
                
                logger.info(f"Recorded position closed: {symbol} @ ${exit_price}, PL: ${realized_pl}")
            
        except psycopg2.Error as e:
            error_type, error_msg, details = self._parse_db_error(e)
            
            if error_type == "schema_mismatch":
                logger.critical(f"Schema mismatch when closing position: {error_msg}")
                # Re-validate schema to get detailed information
                try:
                    self._validate_schema()
                except SchemaMismatchError as schema_error:
                    logger.critical(f"Schema validation failed: {schema_error}")
                    fix_sql = schema_error.get_fix_sql()
                    if fix_sql:
                        logger.critical("\nTo fix this issue, run the following SQL:")
                        logger.critical("-" * 80)
                        logger.critical(fix_sql)
                        logger.critical("-" * 80)
            elif error_type == "connection":
                logger.error(f"Database connection lost: {error_msg}")
                try:
                    self._connect(max_retries=1)
                except Exception:
                    logger.error("Failed to reconnect to database")
            else:
                logger.error(f"Database error ({error_type}): {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error closing position: {e}")
    
    def write_signal(self, signal_event):
        """Write trading signal to database and notify with graceful fallback"""
        try:
            # Build dynamic query based on available columns
            columns = ['strategy', 'symbol', 'action', 'confidence']
            values = [signal_event.strategy, signal_event.symbol, signal_event.action, signal_event.confidence]
            
            # Check which optional columns exist
            signals_columns = self.available_columns.get('signals', [])
            
            # Add expected_profit if available
            if 'expected_profit' in signals_columns or not signals_columns:
                columns.append('expected_profit')
                values.append(getattr(signal_event, 'estimated_profit', None))
            
            # Add metadata if available
            if 'metadata' in signals_columns or not signals_columns:
                columns.append('metadata')
                metadata_value = json.dumps(signal_event.metadata) if hasattr(signal_event, 'metadata') else None
                values.append(metadata_value)
            
            # Build query
            placeholders = ['%s'] * len(values)
            query = f"""
                INSERT INTO signals 
                ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """
            
            self.cur.execute(query, values)
            signal_id = self.cur.fetchone()[0]
            
            # Send notification
            self._notify("signal.generated", {
                "id": signal_id,
                "strategy": signal_event.strategy,
                "symbol": signal_event.symbol,
                "action": signal_event.action,
                "confidence": signal_event.confidence,
                "expected_profit": getattr(signal_event, 'estimated_profit', None)
            })
            
            logger.info(f"Recorded signal: {signal_event.action} {signal_event.symbol} @ {signal_event.confidence:.2f}")
            return signal_id
            
        except psycopg2.Error as e:
            error_type, error_msg, details = self._parse_db_error(e)
            
            if error_type == "schema_mismatch":
                logger.critical(f"Schema mismatch when writing signal: {error_msg}")
                try:
                    self._validate_schema()
                except SchemaMismatchError as schema_error:
                    logger.critical(f"Schema validation failed: {schema_error}")
                    fix_sql = schema_error.get_fix_sql()
                    if fix_sql:
                        logger.critical("\nTo fix this issue, run the following SQL:")
                        logger.critical("-" * 80)
                        logger.critical(fix_sql)
                        logger.critical("-" * 80)
            elif error_type == "connection":
                logger.error(f"Database connection lost: {error_msg}")
                try:
                    self._connect(max_retries=1)
                except Exception:
                    logger.error("Failed to reconnect to database")
            else:
                logger.error(f"Database error ({error_type}): {error_msg}")
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error writing signal: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")


# Global database writer instance
db_writer = None

def initialize_db_writer(connection_string: Optional[str] = None):
    """Initialize the global database writer with improved error handling"""
    global db_writer
    try:
        if connection_string:
            db_writer = DatabaseWriter(connection_string)
        else:
            db_writer = DatabaseWriter()
        logger.info("Database writer initialized successfully")
        return db_writer
    except SchemaMismatchError as e:
        logger.warning(f"Database schema validation failed during initialization: {e}")
        if e.missing_tables:
            logger.warning(f"Missing tables: {e.missing_tables}")
        if e.missing_columns:
            logger.warning(f"Missing columns: {e.missing_columns}")
        logger.warning("Service will continue with degraded database functionality")
        # Still raise to let the engine handle it properly
        raise
    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to database during initialization: {e}")
        logger.error("Please check your database connection settings and ensure the database is running")
        raise
    except Exception as e:
        logger.error(f"Unexpected error initializing database writer: {e}")
        raise

def get_db_writer() -> DatabaseWriter:
    """Get the global database writer instance"""
    if db_writer is None:
        raise RuntimeError("Database writer not initialized. Call initialize_db_writer() first.")
    return db_writer