#!/usr/bin/env python3
"""
Database Connector Service for AddressIQ
Supports multiple database types for pulling address data directly into the processing pipeline
"""

import pandas as pd
import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

class DatabaseConnector:
    """
    Universal database connector supporting multiple database types:
    - SQL Server (pyodbc)
    - MySQL (mysql-connector-python)
    - PostgreSQL (psycopg2)
    - Oracle (cx_Oracle)
    - SQLite (sqlite3)
    - Azure SQL Database
    """
    
    def __init__(self):
        self.supported_databases = {
            'sqlserver': self._connect_sqlserver,
            'mysql': self._connect_mysql,
            'postgresql': self._connect_postgresql,
            'oracle': self._connect_oracle,
            'sqlite': self._connect_sqlite,
            'azure_sql': self._connect_azure_sql
        }
        
        # Track available drivers
        self.available_drivers = self._check_available_drivers()
        
    def _parse_connection_string(self, connection_string: str, db_type: str) -> Dict[str, Any]:
        """Parse connection string into individual parameters"""
        params = {}
        
        if db_type in ['sqlserver', 'azure_sql']:
            # Parse SQL Server/Azure SQL connection string
            # Format: Server=server;Database=database;User Id=username;Password=password;
            # Or: Data Source=server;Initial Catalog=database;User ID=username;Password=password;
            pairs = connection_string.split(';')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key in ['server', 'data source']:
                        params['server'] = value
                    elif key in ['database', 'initial catalog']:
                        params['database'] = value
                    elif key in ['user id', 'uid', 'username']:
                        params['username'] = value
                    elif key in ['password', 'pwd']:
                        params['password'] = value
                        
        elif db_type == 'mysql':
            # Parse MySQL connection string
            # Format: server=host;database=db;uid=user;pwd=password;port=3306
            pairs = connection_string.split(';')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key in ['server', 'host']:
                        params['host'] = value
                    elif key == 'database':
                        params['database'] = value
                    elif key in ['uid', 'user', 'username']:
                        params['username'] = value
                    elif key in ['pwd', 'password']:
                        params['password'] = value
                    elif key == 'port':
                        params['port'] = int(value)
                        
        elif db_type == 'postgresql':
            # Parse PostgreSQL connection string
            # Format: host=localhost;database=mydb;username=user;password=pass;port=5432
            # Or PostgreSQL URI: postgresql://user:password@host:port/database
            if connection_string.startswith('postgresql://'):
                # Parse URI format
                from urllib.parse import urlparse
                parsed = urlparse(connection_string)
                params['host'] = parsed.hostname
                params['database'] = parsed.path.lstrip('/')
                params['username'] = parsed.username
                params['password'] = parsed.password
                if parsed.port:
                    params['port'] = parsed.port
            else:
                # Parse key=value format
                pairs = connection_string.split(';')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == 'host':
                            params['host'] = value
                        elif key == 'database':
                            params['database'] = value
                        elif key in ['username', 'user']:
                            params['username'] = value
                        elif key == 'password':
                            params['password'] = value
                        elif key == 'port':
                            params['port'] = int(value)
                            
        elif db_type == 'sqlite':
            # SQLite connection string is just the file path
            params['database_path'] = connection_string
            
        return params
        
    def _check_available_drivers(self) -> Dict[str, bool]:
        """Check which database drivers are available"""
        drivers = {}
        
        # SQL Server / Azure SQL
        try:
            import pyodbc
            drivers['sqlserver'] = True
            drivers['azure_sql'] = True
        except ImportError:
            drivers['sqlserver'] = False
            drivers['azure_sql'] = False
            
        # MySQL
        try:
            import mysql.connector
            drivers['mysql'] = True
        except ImportError:
            drivers['mysql'] = False
            
        # PostgreSQL
        try:
            import psycopg2
            drivers['postgresql'] = True
        except ImportError:
            drivers['postgresql'] = False
            
        # Oracle
        try:
            import cx_Oracle
            drivers['oracle'] = True
        except ImportError:
            drivers['oracle'] = False
            
        # SQLite (built-in)
        drivers['sqlite'] = True
        
        return drivers
    
    def get_supported_databases(self) -> List[str]:
        """Get list of supported database types based on available drivers"""
        return [db for db, available in self.available_drivers.items() if available]
    
    def validate_connection_params(self, db_type: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate connection parameters for specific database type"""
        result = {
            'valid': False,
            'missing_params': [],
            'errors': []
        }
        
        if db_type not in self.supported_databases:
            result['errors'].append(f"Unsupported database type: {db_type}")
            return result
            
        if not self.available_drivers.get(db_type):
            result['errors'].append(f"Driver not available for {db_type}")
            return result
        
        # Check if connection string is provided
        if 'connection_string' in connection_params and connection_params['connection_string']:
            # Parse connection string to validate it has required components
            try:
                parsed_params = self._parse_connection_string(connection_params['connection_string'], db_type)
                
                # Required parameters for each database type
                required_fields = {
                    'sqlserver': ['server', 'database'],
                    'azure_sql': ['server', 'database', 'username', 'password'],
                    'mysql': ['host', 'database', 'username', 'password'],
                    'postgresql': ['host', 'database', 'username', 'password'],
                    'oracle': ['host', 'database', 'username', 'password'],
                    'sqlite': ['database_path']
                }
                
                missing = []
                for field in required_fields.get(db_type, []):
                    if field not in parsed_params or not parsed_params[field]:
                        missing.append(field)
                
                if missing:
                    result['missing_params'] = missing
                    result['errors'].append(f"Connection string missing required fields: {missing}")
                    return result
                    
                result['valid'] = True
                return result
                
            except Exception as e:
                result['errors'].append(f"Invalid connection string format: {str(e)}")
                return result
        
        # Original individual parameter validation
        required_params = {
            'sqlserver': ['server', 'database'],
            'azure_sql': ['server', 'database', 'username', 'password'],
            'mysql': ['host', 'database', 'username', 'password'],
            'postgresql': ['host', 'database', 'username', 'password'],
            'oracle': ['host', 'database', 'username', 'password'],
            'sqlite': ['database_path']
        }
        
        missing = []
        for param in required_params.get(db_type, []):
            if param not in connection_params or not connection_params[param]:
                missing.append(param)
        
        if missing:
            result['missing_params'] = missing
            return result
            
        result['valid'] = True
        return result
    
    def test_connection(self, db_type: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection"""
        validation = self.validate_connection_params(db_type, connection_params)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid parameters: {validation.get('errors', [])} {validation.get('missing_params', [])}"
            }
        
        try:
            connector_func = self.supported_databases[db_type]
            conn = connector_func(connection_params)
            
            # Test with a simple query
            cursor = conn.cursor()
            if db_type == 'sqlite':
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1 as test")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'message': f"Successfully connected to {db_type} database"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection failed: {str(e)}"
            }
    
    def preview_table_structure(self, 
                               db_type: str, 
                               connection_params: Dict[str, Any],
                               table_name: str = None,
                               sample_rows: int = 5) -> Dict[str, Any]:
        """
        Preview table structure and sample data to help users identify address columns
        
        Args:
            db_type: Database type
            connection_params: Database connection parameters  
            table_name: Table name to preview
            sample_rows: Number of sample rows to return
            
        Returns:
            Dict with table structure and sample data
        """
        
        validation = self.validate_connection_params(db_type, connection_params)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid connection parameters: {validation}"
            }
        
        try:
            connector_func = self.supported_databases[db_type]
            conn = connector_func(connection_params)
            
            result = {
                'success': True,
                'table_name': table_name,
                'columns': [],
                'sample_data': [],
                'detected_address_columns': [],
                'row_count_estimate': None
            }
            
            if table_name:
                # Get column information
                if db_type in ['sqlserver', 'azure_sql']:
                    column_query = f"""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = '{table_name}'
                        ORDER BY ORDINAL_POSITION
                    """
                elif db_type in ['mysql', 'postgresql']:
                    column_query = f"""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = '{table_name}'
                        ORDER BY ORDINAL_POSITION
                    """
                elif db_type == 'sqlite':
                    column_query = f"PRAGMA table_info({table_name})"
                else:
                    # Fallback: just get sample data and derive columns
                    column_query = None
                
                if column_query:
                    cursor = conn.cursor()
                    cursor.execute(column_query)
                    
                    if db_type == 'sqlite':
                        # SQLite pragma returns: cid, name, type, notnull, dflt_value, pk
                        for row in cursor.fetchall():
                            result['columns'].append({
                                'name': row[1],
                                'type': row[2],
                                'nullable': not bool(row[3])
                            })
                    else:
                        # Standard INFORMATION_SCHEMA
                        for row in cursor.fetchall():
                            result['columns'].append({
                                'name': row[0],
                                'type': row[1],
                                'nullable': row[2] == 'YES',
                                'max_length': row[3]
                            })
                    cursor.close()
                
                # Get sample data
                sample_query = f"SELECT * FROM {table_name}"
                if db_type in ['mysql', 'postgresql', 'sqlite']:
                    sample_query += f" LIMIT {sample_rows}"
                elif db_type in ['sqlserver', 'azure_sql']:
                    sample_query = f"SELECT TOP {sample_rows} * FROM {table_name}"
                elif db_type == 'oracle':
                    sample_query = f"SELECT * FROM {table_name} WHERE ROWNUM <= {sample_rows}"
                
                # Use pandas to get sample data
                import pandas as pd
                df_sample = pd.read_sql(sample_query, conn)
                
                # Convert to list of dictionaries
                result['sample_data'] = df_sample.to_dict('records')
                
                # If we couldn't get columns from schema, derive from sample data
                if not result['columns'] and not df_sample.empty:
                    result['columns'] = [{'name': col, 'type': str(df_sample[col].dtype)} 
                                       for col in df_sample.columns]
                
                # Detect potential address columns
                result['detected_address_columns'] = self._detect_address_columns(df_sample)
                
                # Get approximate row count
                try:
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    cursor = conn.cursor()
                    cursor.execute(count_query)
                    result['row_count_estimate'] = cursor.fetchone()[0]
                    cursor.close()
                except:
                    result['row_count_estimate'] = "Unknown"
                
            else:
                # List available tables
                if db_type in ['sqlserver', 'azure_sql']:
                    tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                elif db_type in ['mysql', 'postgresql']:
                    tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = DATABASE()" if db_type == 'mysql' else "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                elif db_type == 'sqlite':
                    tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                else:
                    tables_query = None
                
                if tables_query:
                    cursor = conn.cursor()
                    cursor.execute(tables_query)
                    result['available_tables'] = [row[0] for row in cursor.fetchall()]
                    cursor.close()
            
            conn.close()
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Table preview failed: {str(e)}"
            }
    
    def extract_data_to_csv(self, 
                           db_type: str, 
                           connection_params: Dict[str, Any],
                           query: str = None,
                           table_name: str = None,
                           address_columns: List[str] = None,
                           output_csv_path: str = None,
                           limit: int = None) -> Dict[str, Any]:
        """
        Extract data from database and save to CSV in inbound directory
        
        Args:
            db_type: Database type (sqlserver, mysql, postgresql, etc.)
            connection_params: Database connection parameters
            query: Custom SQL query (optional)
            table_name: Table name to extract from (if no query provided)
            address_columns: List of columns containing address data
            output_csv_path: Path to save CSV file
            limit: Limit number of records
            
        Returns:
            Dict with success status, file path, and metadata
        """
        
        # Validate connection
        validation = self.validate_connection_params(db_type, connection_params)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid connection parameters: {validation}"
            }
        
        try:
            # Build query if not provided
            if not query:
                if not table_name:
                    return {
                        'success': False,
                        'error': "Either 'query' or 'table_name' must be provided"
                    }
                
                # Build basic SELECT query
                if address_columns:
                    columns = ', '.join(address_columns)
                else:
                    columns = '*'
                
                query = f"SELECT {columns} FROM {table_name}"
                
                if limit:
                    # Add LIMIT clause based on database type
                    if db_type in ['mysql', 'postgresql', 'sqlite']:
                        query += f" LIMIT {limit}"
                    elif db_type in ['sqlserver', 'azure_sql']:
                        query = f"SELECT TOP {limit} {columns} FROM {table_name}"
                    elif db_type == 'oracle':
                        query = f"SELECT {columns} FROM {table_name} WHERE ROWNUM <= {limit}"
            else:
                # User provided custom query - need to add limit to it
                if limit:
                    if db_type in ['mysql', 'postgresql', 'sqlite']:
                        # Check if LIMIT already exists
                        if 'LIMIT' not in query.upper():
                            query += f" LIMIT {limit}"
                    elif db_type in ['sqlserver', 'azure_sql']:
                        # Check if TOP already exists
                        if 'TOP ' not in query.upper():
                            # Insert TOP after SELECT
                            query = query.replace('SELECT', f'SELECT TOP {limit}', 1)
                    elif db_type == 'oracle':
                        # Add WHERE ROWNUM condition
                        if 'ROWNUM' not in query.upper():
                            if 'WHERE' in query.upper():
                                query += f" AND ROWNUM <= {limit}"
                            else:
                                query += f" WHERE ROWNUM <= {limit}"
            
            # Connect and execute query
            connector_func = self.supported_databases[db_type]
            conn = connector_func(connection_params)
            
            # Use pandas to read SQL
            df = pd.read_sql(query, conn)
            conn.close()
            
            if df.empty:
                return {
                    'success': False,
                    'error': "Query returned no results"
                }
            
            # Generate output file path if not provided
            if not output_csv_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"database_extract_{timestamp}.csv"
                
                # Use inbound directory
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                inbound_dir = os.path.join(base_dir, 'inbound')
                os.makedirs(inbound_dir, exist_ok=True)
                output_csv_path = os.path.join(inbound_dir, filename)
            
            # Save to CSV
            df.to_csv(output_csv_path, index=False, encoding='utf-8')
            
            # Detect potential address columns if not specified
            detected_address_columns = self._detect_address_columns(df)
            
            return {
                'success': True,
                'csv_file_path': output_csv_path,
                'records_extracted': len(df),
                'columns': df.columns.tolist(),
                'detected_address_columns': detected_address_columns,
                'query_used': query,
                'database_type': db_type,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Data extraction failed: {str(e)}"
            }
    
    def _detect_address_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect columns that likely contain address data"""
        address_keywords = [
            'address', 'addr', 'street', 'road', 'avenue', 'lane', 'drive',
            'city', 'town', 'state', 'province', 'zip', 'postal', 'country',
            'location', 'place', 'site', 'building'
        ]
        
        detected_columns = []
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in address_keywords):
                detected_columns.append(col)
        
        return detected_columns
    
    # Database-specific connection methods
    def _connect_sqlserver(self, params: Dict[str, Any]):
        """Connect to SQL Server"""
        import pyodbc
        
        # Build connection string
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={params['server']};"
        
        if params.get('database'):
            conn_str += f"DATABASE={params['database']};"
            
        if params.get('username') and params.get('password'):
            conn_str += f"UID={params['username']};PWD={params['password']};"
        else:
            conn_str += "Trusted_Connection=yes;"
            
        return pyodbc.connect(conn_str)
    
    def _connect_azure_sql(self, params: Dict[str, Any]):
        """Connect to Azure SQL Database"""
        import pyodbc
        
        # Check if connection string is provided
        if 'connection_string' in params and params['connection_string']:
            # Use connection string directly or parse it for pyodbc format
            conn_str = params['connection_string']
            
            # If it's not already in pyodbc format, parse and rebuild
            if not conn_str.upper().startswith('DRIVER='):
                parsed = self._parse_connection_string(conn_str, 'azure_sql')
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={parsed['server']};"
                    f"DATABASE={parsed['database']};"
                    f"UID={parsed['username']};"
                    f"PWD={parsed['password']};"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=no;"
                    f"Connection Timeout=30;"
                )
        else:
            # Build connection string from individual parameters
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={params['server']};"
                f"DATABASE={params['database']};"
                f"UID={params['username']};"
                f"PWD={params['password']};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
        
        return pyodbc.connect(conn_str)
    
    def _connect_mysql(self, params: Dict[str, Any]):
        """Connect to MySQL"""
        import mysql.connector
        
        return mysql.connector.connect(
            host=params['host'],
            port=params.get('port', 3306),
            database=params['database'],
            user=params['username'],
            password=params['password']
        )
    
    def _connect_postgresql(self, params: Dict[str, Any]):
        """Connect to PostgreSQL"""
        import psycopg2
        
        return psycopg2.connect(
            host=params['host'],
            port=params.get('port', 5432),
            database=params['database'],
            user=params['username'],
            password=params['password']
        )
    
    def _connect_oracle(self, params: Dict[str, Any]):
        """Connect to Oracle"""
        import cx_Oracle
        
        dsn = cx_Oracle.makedsn(
            params['host'], 
            params.get('port', 1521), 
            service_name=params['database']
        )
        
        return cx_Oracle.connect(
            params['username'],
            params['password'],
            dsn
        )
    
    def _connect_sqlite(self, params: Dict[str, Any]):
        """Connect to SQLite"""
        import sqlite3
        
        return sqlite3.connect(params['database_path'])

# Example usage configurations
DATABASE_CONFIG_EXAMPLES = {
    'sqlserver': {
        'server': 'localhost\\SQLEXPRESS',
        'database': 'AddressDB',
        'username': 'sa',  # Optional for Windows Auth
        'password': 'password'  # Optional for Windows Auth
    },
    'azure_sql': {
        'server': 'your-server.database.windows.net',
        'database': 'your-database',
        'username': 'your-username',
        'password': 'your-password'
    },
    'mysql': {
        'host': 'localhost',
        'port': 3306,
        'database': 'address_db',
        'username': 'root',
        'password': 'password'
    },
    'postgresql': {
        'host': 'localhost',
        'port': 5432,
        'database': 'address_db',
        'username': 'postgres',
        'password': 'password'
    },
    'sqlite': {
        'database_path': '/path/to/database.db'
    }
}
