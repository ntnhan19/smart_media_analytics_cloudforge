"""
Database Client — Connection Management and Transaction Support

Provides:
- Database connection pooling
- Transaction management
- Query execution
- Error handling and retry logic
"""

import os
import logging
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from contextlib import contextmanager
from datetime import datetime
import uuid

# Placeholder for actual DB imports (SQLAlchemy, psycopg, sqlite)
# In production, these would be actual database drivers

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self,
                 url: Optional[str] = None,
                 driver: str = "postgresql",
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "smartmedia_db",
                 username: str = "postgres",
                 password: str = "postgres",
                 pool_size: int = 10,
                 max_overflow: int = 20,
                 echo: bool = False):
        """
        Initialize database configuration
        
        Args:
            url: Full database URL (takes precedence over other params)
            driver: Database driver (postgresql, sqlite, mysql, etc.)
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            echo: Log SQL statements
        """
        self.url = url or self._build_url(driver, host, port, database, username, password)
        self.driver = driver
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo
    
    @staticmethod
    def from_env() -> 'DatabaseConfig':
        """Load configuration from environment variables"""
        return DatabaseConfig(
            url=os.getenv("DATABASE_URL"),
            driver=os.getenv("DB_DRIVER", "postgresql"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "smartmedia_db"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            pool_size=int(os.getenv("DB_POOL_SIZE", 10)),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 20)),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    
    def _build_url(self, driver: str, host: str, port: int, database: str, username: str, password: str) -> str:
        """Build database URL"""
        if driver == "sqlite":
            return f"sqlite:///{database}"
        elif driver == "postgresql":
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif driver == "mysql":
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported driver: {driver}")


class DatabaseConnection:
    """Represents a single database connection"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
        self._transaction = None
        self.is_connected = False
    
    def connect(self):
        """Establish connection to database"""
        try:
            # In production, use actual database driver
            # from sqlalchemy import create_engine
            # self._connection = create_engine(self.config.url, ...)
            
            logger.info(f"Connecting to database: {self.config.database}")
            self.is_connected = True
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.is_connected = False
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self._connection:
            try:
                # In production: self._connection.dispose()
                logger.info("Disconnecting from database")
                self.is_connected = False
            except Exception as e:
                logger.error(f"Error disconnecting from database: {e}")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        if not self.is_connected:
            self.connect()
        
        try:
            # In production: use actual transaction context
            logger.debug("Starting transaction")
            yield self
            logger.debug("Committing transaction")
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            logger.debug("Rolling back transaction")
            raise
    
    def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute a query"""
        if not self.is_connected:
            self.connect()
        
        try:
            logger.debug(f"Executing query: {query[:100]}...")
            # In production: actual query execution
            result = self._execute_query(query, params)
            return result
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def _execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Internal method for query execution"""
        # Placeholder for actual implementation
        return None


class DatabaseClient:
    """Main database client with connection pooling"""
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database client
        
        Args:
            config: DatabaseConfig instance
        """
        self.config = config
        self._connections: List[DatabaseConnection] = []
        self._primary_connection = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        logger.info(f"Initializing connection pool (size={self.config.pool_size})")
        
        for _ in range(self.config.pool_size):
            conn = DatabaseConnection(self.config)
            self._connections.append(conn)
        
        self._primary_connection = self._connections[0]
        self._primary_connection.connect()
    
    def get_connection(self) -> DatabaseConnection:
        """Get available connection from pool"""
        for conn in self._connections:
            if not conn._transaction:
                return conn
        
        # If no connection available, use primary
        return self._primary_connection
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        conn = self.get_connection()
        with conn.transaction():
            yield conn
    
    def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute query on primary connection"""
        conn = self.get_connection()
        return conn.execute(query, params)
    
    def close(self):
        """Close all connections in pool"""
        for conn in self._connections:
            conn.disconnect()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class Repository(Generic[T]):
    """Generic repository base class for CRUD operations"""
    
    def __init__(self, db_client: DatabaseClient, table_name: str):
        """
        Initialize repository
        
        Args:
            db_client: DatabaseClient instance
            table_name: Name of database table
        """
        self.db = db_client
        self.table_name = table_name
    
    def create(self, entity: T) -> T:
        """Create new entity"""
        raise NotImplementedError
    
    def read(self, entity_id: str) -> Optional[T]:
        """Read entity by ID"""
        raise NotImplementedError
    
    def update(self, entity: T) -> T:
        """Update existing entity"""
        raise NotImplementedError
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        raise NotImplementedError
    
    def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List entities with pagination"""
        raise NotImplementedError
    
    def count(self) -> int:
        """Count total entities"""
        raise NotImplementedError


class QueryBuilder:
    """SQL query builder for safe query construction"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._select_fields: List[str] = ["*"]
        self._where_clauses: List[str] = []
        self._where_params: Dict[str, Any] = {}
        self._joins: List[str] = []
        self._order_by: List[str] = []
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """Specify SELECT fields"""
        self._select_fields = list(fields) if fields else ["*"]
        return self
    
    def where(self, clause: str, **params) -> 'QueryBuilder':
        """Add WHERE clause"""
        self._where_clauses.append(clause)
        self._where_params.update(params)
        return self
    
    def join(self, join_clause: str) -> 'QueryBuilder':
        """Add JOIN clause"""
        self._joins.append(join_clause)
        return self
    
    def order_by(self, *fields: str, desc: bool = False) -> 'QueryBuilder':
        """Add ORDER BY clause"""
        for field in fields:
            order = "DESC" if desc else "ASC"
            self._order_by.append(f"{field} {order}")
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """Add LIMIT clause"""
        self._limit_val = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """Add OFFSET clause"""
        self._offset_val = offset
        return self
    
    def build(self) -> tuple[str, Dict[str, Any]]:
        """Build query and return (query, params)"""
        select_str = ", ".join(self._select_fields)
        query = f"SELECT {select_str} FROM {self.table_name}"
        
        # Add joins
        if self._joins:
            query += " " + " ".join(self._joins)
        
        # Add where clauses
        if self._where_clauses:
            where_str = " AND ".join(self._where_clauses)
            query += f" WHERE {where_str}"
        
        # Add order by
        if self._order_by:
            query += " ORDER BY " + ", ".join(self._order_by)
        
        # Add limit/offset
        if self._limit_val is not None:
            query += f" LIMIT {self._limit_val}"
        if self._offset_val is not None:
            query += f" OFFSET {self._offset_val}"
        
        return query, self._where_params
    
    def __str__(self) -> str:
        query, _ = self.build()
        return query


class BatchInsertBuilder:
    """Builder for efficient batch inserts"""
    
    def __init__(self, table_name: str, batch_size: int = 1000):
        self.table_name = table_name
        self.batch_size = batch_size
        self._rows: List[Dict[str, Any]] = []
    
    def add_row(self, row: Dict[str, Any]) -> 'BatchInsertBuilder':
        """Add row to batch"""
        self._rows.append(row)
        return self
    
    def add_rows(self, rows: List[Dict[str, Any]]) -> 'BatchInsertBuilder':
        """Add multiple rows to batch"""
        self._rows.extend(rows)
        return self
    
    def build_batches(self) -> List[tuple[str, List[Dict[str, Any]]]]:
        """Build batch insert queries"""
        batches = []
        
        for i in range(0, len(self._rows), self.batch_size):
            batch = self._rows[i:i + self.batch_size]
            
            if not batch:
                continue
            
            # Get columns from first row
            columns = list(batch[0].keys())
            cols_str = ", ".join(columns)
            
            # Create multi-row insert query
            placeholders = ", ".join([f"(:{col})" for col in columns])
            query = f"INSERT INTO {self.table_name} ({cols_str}) VALUES {placeholders}"
            
            batches.append((query, batch))
        
        return batches


class TransactionContext:
    """Context manager for transaction handling with retry logic"""
    
    def __init__(self, db_client: DatabaseClient, max_retries: int = 3):
        self.db = db_client
        self.max_retries = max_retries
        self.retry_count = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.retry_count += 1
            if self.retry_count < self.max_retries:
                logger.warning(f"Transaction failed, retry {self.retry_count}/{self.max_retries}")
                return True  # Suppress exception and retry
        return False


# ── Helper Functions ──────────────────────────────────────────────────────

def get_db_client() -> DatabaseClient:
    """Factory function to create database client"""
    config = DatabaseConfig.from_env()
    return DatabaseClient(config)


def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())


def get_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()
