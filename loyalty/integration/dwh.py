"""
DWH Connector for segmentation and ML feature extraction.
Supports multiple DWH backends: Oracle, PostgreSQL, Snowflake, SQL Server.
"""

from typing import Dict, List, Optional, Any
from django.conf import settings
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DWHConnector(ABC):
    """Abstract base class for DWH connectors"""
    
    @abstractmethod
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute SQL query and return results"""
        pass
    
    @abstractmethod
    def get_customer_features(self, customer_id: str) -> Dict[str, Any]:
        """Extract customer features from DWH"""
        pass


class OracleDWHConnector(DWHConnector):
    """Oracle DWH connector"""
    
    def __init__(self):
        try:
            import cx_Oracle
            self.cx_Oracle = cx_Oracle
        except ImportError:
            raise ImportError("cx_Oracle not installed. Install with: pip install cx_Oracle")
        
        self.connection_string = getattr(settings, 'DWH_ORACLE_CONNECTION_STRING', '')
        self.user = getattr(settings, 'DWH_USER', '')
        self.password = getattr(settings, 'DWH_PASSWORD', '')
        
        # Create connection pool
        self.pool = self.cx_Oracle.create_pool(
            user=self.user,
            password=self.password,
            dsn=self.connection_string,
            min=2,
            max=10
        )
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query against Oracle DWH"""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_customer_features(self, customer_id: str) -> Dict[str, Any]:
        """Get customer features from Oracle DWH
        
        Uses configurable query from settings. You must configure:
        - DWH_CUSTOMER_FEATURES_QUERY: SQL query with :customer_id placeholder
        - DWH_CUSTOMER_FEATURES_TABLE: Table/view name (alternative to query)
        """
        from django.conf import settings
        
        # Option 1: Use custom query from settings
        custom_query = getattr(settings, 'DWH_CUSTOMER_FEATURES_QUERY', None)
        if custom_query:
            query = custom_query
        else:
            # Option 2: Use table/view name from settings
            table_name = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
            query = f"SELECT * FROM {table_name} WHERE customer_id = :customer_id"
        
        try:
            results = self.execute_query(query, {'customer_id': customer_id})
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error fetching customer features from Oracle DWH: {e}")
            return {}


class PostgreSQLDWHConnector(DWHConnector):
    """PostgreSQL DWH connector"""
    
    def __init__(self):
        try:
            from sqlalchemy import create_engine
            self.create_engine = create_engine
        except ImportError:
            raise ImportError("SQLAlchemy not installed. Install with: pip install sqlalchemy")
        
        connection_string = getattr(settings, 'DWH_POSTGRES_CONNECTION_STRING', '')
        self.engine = self.create_engine(
            connection_string,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query against PostgreSQL DWH"""
        from sqlalchemy import text
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
    
    def get_customer_features(self, customer_id: str) -> Dict[str, Any]:
        """Get customer features from PostgreSQL DWH
        
        Uses configurable query from settings. You must configure:
        - DWH_CUSTOMER_FEATURES_QUERY: SQL query with :customer_id placeholder
        - DWH_CUSTOMER_FEATURES_TABLE: Table/view name (alternative to query)
        """
        from django.conf import settings
        import uuid
        
        # Convert customer_id to string (handle UUID objects)
        if isinstance(customer_id, uuid.UUID):
            customer_id_str = str(customer_id)
        else:
            customer_id_str = str(customer_id)
        
        # Option 1: Use custom query from settings
        custom_query = getattr(settings, 'DWH_CUSTOMER_FEATURES_QUERY', None)
        if custom_query:
            query = custom_query
            # Replace :customer_id with SQLAlchemy format if needed
            if ':customer_id' in query:
                # Already in SQLAlchemy format
                params = {'customer_id': customer_id_str}
            elif '%(customer_id)s' in query:
                # Convert psycopg2 format to SQLAlchemy format
                query = query.replace('%(customer_id)s', ':customer_id')
                params = {'customer_id': customer_id_str}
            else:
                params = {'customer_id': customer_id_str}
        else:
            # Option 2: Use table/view name from settings
            table_name = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
            # Cast customer_id to text to handle UUID/VARCHAR mismatch in PostgreSQL
            # Use SQLAlchemy parameter format (:param) not psycopg2 format (%(param)s)
            query = f"SELECT * FROM {table_name} WHERE customer_id::text = :customer_id"
            params = {'customer_id': customer_id_str}
        
        try:
            results = self.execute_query(query, params)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error fetching customer features from PostgreSQL DWH: {e}")
            return {}


class SnowflakeDWHConnector(DWHConnector):
    """Snowflake DWH connector"""
    
    def __init__(self):
        try:
            import snowflake.connector
            self.snowflake = snowflake.connector
        except ImportError:
            raise ImportError("snowflake-connector-python not installed. Install with: pip install snowflake-connector-python")
        
        self.conn = self.snowflake.connector.connect(
            user=getattr(settings, 'DWH_SNOWFLAKE_USER', ''),
            password=getattr(settings, 'DWH_SNOWFLAKE_PASSWORD', ''),
            account=getattr(settings, 'DWH_SNOWFLAKE_ACCOUNT', ''),
            warehouse=getattr(settings, 'DWH_SNOWFLAKE_WAREHOUSE', ''),
            database=getattr(settings, 'DWH_SNOWFLAKE_DATABASE', ''),
            schema=getattr(settings, 'DWH_SNOWFLAKE_SCHEMA', '')
        )
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query against Snowflake DWH"""
        cursor = self.conn.cursor()
        cursor.execute(query, params or {})
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_customer_features(self, customer_id: str) -> Dict[str, Any]:
        """Get customer features from Snowflake DWH
        
        Uses configurable query from settings. You must configure:
        - DWH_CUSTOMER_FEATURES_QUERY: SQL query with %(customer_id)s placeholder
        - DWH_CUSTOMER_FEATURES_TABLE: Table/view name (alternative to query)
        """
        from django.conf import settings
        
        # Option 1: Use custom query from settings
        custom_query = getattr(settings, 'DWH_CUSTOMER_FEATURES_QUERY', None)
        if custom_query:
            query = custom_query
        else:
            # Option 2: Use table/view name from settings
            table_name = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'ANALYTICS.CUSTOMER_FEATURES')
            query = f"SELECT * FROM {table_name} WHERE CUSTOMER_ID = %(customer_id)s"
        
        try:
            results = self.execute_query(query, {'customer_id': customer_id})
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error fetching customer features from Snowflake DWH: {e}")
            return {}


def get_dwh_connector() -> DWHConnector:
    """Factory function to get DWH connector based on settings"""
    dwh_type = getattr(settings, 'DWH_TYPE', 'postgresql').lower()
    
    if dwh_type == 'oracle':
        return OracleDWHConnector()
    elif dwh_type == 'postgresql':
        return PostgreSQLDWHConnector()
    elif dwh_type == 'snowflake':
        return SnowflakeDWHConnector()
    else:
        raise ValueError(f"Unsupported DWH type: {dwh_type}. Supported: oracle, postgresql, snowflake")

