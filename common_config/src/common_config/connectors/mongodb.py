"""MongoDB connector with standardized connection handling."""
import os
from contextlib import contextmanager
from typing import Generator, Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from common_config.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBConnector:
    """Standardized MongoDB connector with environment-aware configuration.
    
    Handles connection lifecycle, retry logic, and environment-specific URI resolution.
    
    Example:
        >>> connector = MongoDBConnector(env="PROD")
        >>> with connector.connect() as client:
        ...     db = client[connector.database_name]
        ...     collections = db.list_collection_names()
    """
    
    def __init__(
        self,
        env: str = "DEV",
        mongodb_uri: Optional[str] = None,
        database_name: Optional[str] = None,
        timeout_ms: int = 5000,
        max_pool_size: int = 100,
    ):
        """Initialize MongoDB connector.
        
        Args:
            env: Environment name (DEV, STG, PROD, etc.). Used to lookup MONGODB_URI_<ENV>
            mongodb_uri: Explicit MongoDB URI. If None, reads from MONGODB_URI_<ENV> in .env
            database_name: Database name. If None, reads from DATABASE_NAME_<ENV> in .env
            timeout_ms: Server selection timeout in milliseconds
            max_pool_size: Maximum connection pool size
        """
        self.env = env.upper()
        
        # Resolve MongoDB URI
        if mongodb_uri:
            self.mongodb_uri: str = mongodb_uri
        else:
            uri_var = f"MONGODB_URI_{self.env}"
            uri_value = os.getenv(uri_var)
            if not uri_value:
                # Fallback to generic MONGODB_URI
                uri_value = os.getenv("MONGODB_URI")
            if not uri_value:
                raise ValueError(
                    f"MongoDB URI not found. Set {uri_var} or MONGODB_URI in shared_config/.env"
                )
            self.mongodb_uri = uri_value
        
        # Resolve database name
        if database_name:
            self.database_name: str = database_name
        else:
            db_var = f"DATABASE_NAME_{self.env}"
            db_value = os.getenv(db_var)
            if not db_value:
                # Fallback to generic DATABASE_NAME
                db_value = os.getenv("DATABASE_NAME")
            if not db_value:
                raise ValueError(
                    f"Database name not found. Set {db_var} or DATABASE_NAME in shared_config/.env"
                )
            self.database_name = db_value
        
        self.timeout_ms = timeout_ms
        self.max_pool_size = max_pool_size
        self._client: Optional[MongoClient] = None
        
        logger.info(f"MongoDB connector initialized for environment: {self.env}")
        logger.debug(f"Database: {self.database_name}")
    
    @contextmanager
    def connect(self) -> Generator[MongoClient, None, None]:
        """Context manager for MongoDB connection.
        
        Automatically handles connection cleanup and error logging.
        
        Yields:
            MongoClient instance
            
        Raises:
            ConnectionFailure: If connection to MongoDB fails
            
        Example:
            >>> connector = MongoDBConnector(env="PROD")
            >>> with connector.connect() as client:
            ...     db = client["my_database"]
            ...     result = db.my_collection.find_one()
        """
        client = None
        try:
            client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=self.timeout_ms,
                maxPoolSize=self.max_pool_size,
            )
            
            # Test connection
            client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB ({self.env})")
            
            yield client
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection timeout ({self.env}): {e}")
            raise ConnectionFailure(f"Could not connect to MongoDB ({self.env})") from e
        except Exception as e:
            logger.error(f"❌ MongoDB connection error ({self.env}): {e}")
            raise
        finally:
            if client:
                client.close()
                logger.info(f"🔒 MongoDB connection closed ({self.env})")
    
    def get_database(self) -> Database:
        """Get database instance (requires active connection via connect()).
        
        Returns:
            Database instance
            
        Note:
            This method should be called within a connect() context manager.
            
        Example:
            >>> connector = MongoDBConnector(env="PROD")
            >>> with connector.connect() as client:
            ...     db = connector.get_database()
            ...     # Use db here
        """
        if not self._client:
            raise RuntimeError("No active connection. Use within connect() context manager.")
        return self._client[self.database_name]
    
    def test_connection(self) -> bool:
        """Test MongoDB connection.
        
        Returns:
            True if connection successful, False otherwise
            
        Example:
            >>> connector = MongoDBConnector(env="DEV")
            >>> if connector.test_connection():
            ...     print("Connection OK")
        """
        try:
            with self.connect() as client:
                client.admin.command('ping')
                logger.info(f"✅ MongoDB connection test successful ({self.env})")
                return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection test failed ({self.env}): {e}")
            return False


@contextmanager
def get_mongo_client(
    env: str = "DEV",
    mongodb_uri: Optional[str] = None,
    **kwargs
) -> Generator[MongoClient, None, None]:
    """Convenience function to get MongoDB client as context manager.
    
    Args:
        env: Environment name (DEV, STG, PROD, etc.)
        mongodb_uri: Explicit MongoDB URI (optional)
        **kwargs: Additional arguments passed to MongoDBConnector
        
    Yields:
        MongoClient instance
        
    Example:
        >>> with get_mongo_client(env="PROD") as client:
        ...     db = client["UbiquityProduction"]
        ...     collections = db.list_collection_names()
    """
    connector = MongoDBConnector(env=env, mongodb_uri=mongodb_uri, **kwargs)
    with connector.connect() as client:
        yield client
