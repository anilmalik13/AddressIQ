#!/usr/bin/env python3
"""
Database Address Processor - Command Line Interface
Process addresses directly from database sources
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csv_address_processor import CSVAddressProcessor

def main():
    parser = argparse.ArgumentParser(
        description='Process addresses directly from database sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SQL Server with Windows Authentication
  python database_address_processor.py --db-type sqlserver --server "localhost\\SQLEXPRESS" --database "AddressDB" --table "Customers" --address-columns "FullAddress,City,State"

  # Azure SQL Database
  python database_address_processor.py --db-type azure_sql --server "yourserver.database.windows.net" --database "yourdb" --username "user" --password "pass" --query "SELECT Address, City FROM Customers WHERE City='Toronto'"

  # MySQL
  python database_address_processor.py --db-type mysql --host "localhost" --database "addresses" --username "root" --password "password" --table "locations" --limit 100

  # PostgreSQL
  python database_address_processor.py --db-type postgresql --host "localhost" --database "gis_data" --username "postgres" --password "password" --query "SELECT full_address FROM properties"

  # Test connection only
  python database_address_processor.py --db-type mysql --host "localhost" --database "test" --username "root" --password "password" --test-only
        """
    )
    
    # Database connection parameters
    parser.add_argument('--db-type', required=True, 
                       choices=['sqlserver', 'azure_sql', 'mysql', 'postgresql', 'oracle', 'sqlite'],
                       help='Database type')
    
    # Connection parameters
    parser.add_argument('--server', help='Server name (SQL Server/Azure SQL)')
    parser.add_argument('--host', help='Host name (MySQL/PostgreSQL/Oracle)')
    parser.add_argument('--port', type=int, help='Port number')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--username', help='Username')
    parser.add_argument('--password', help='Password')
    parser.add_argument('--database-path', help='Database file path (SQLite only)')
    
    # Query parameters
    parser.add_argument('--query', help='Custom SQL query')
    parser.add_argument('--table', help='Table name (if no custom query)')
    parser.add_argument('--address-columns', help='Comma-separated list of address columns')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    
    # Processing parameters
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing (default: 10)')
    parser.add_argument('--no-free-apis', action='store_true', help='Disable free API enhancement')
    
    # Other options
    parser.add_argument('--test-only', action='store_true', help='Test connection only, do not process')
    parser.add_argument('--list-supported', action='store_true', help='List supported database types')
    parser.add_argument('--config-file', help='JSON configuration file with connection parameters')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = CSVAddressProcessor()
    
    # List supported databases
    if args.list_supported:
        supported = processor.get_supported_databases()
        print("Supported database types:")
        for db_type in supported:
            print(f"  - {db_type}")
        return
    
    # Load configuration from file if provided
    if args.config_file:
        try:
            with open(args.config_file, 'r') as f:
                config = json.load(f)
            print(f"📁 Loaded configuration from {args.config_file}")
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            return
    else:
        # Build connection parameters from command line arguments
        config = {
            'db_type': args.db_type,
            'connection_params': {},
            'query': args.query,
            'table_name': args.table,
            'address_columns': args.address_columns.split(',') if args.address_columns else None,
            'limit': args.limit,
            'batch_size': args.batch_size,
            'use_free_apis': not args.no_free_apis
        }
        
        # Add connection parameters based on database type
        if args.db_type in ['sqlserver', 'azure_sql']:
            if not args.server:
                print("❌ --server is required for SQL Server/Azure SQL")
                return
            config['connection_params']['server'] = args.server
            config['connection_params']['database'] = args.database
            if args.username:
                config['connection_params']['username'] = args.username
            if args.password:
                config['connection_params']['password'] = args.password
                
        elif args.db_type in ['mysql', 'postgresql', 'oracle']:
            if not args.host:
                print(f"❌ --host is required for {args.db_type}")
                return
            config['connection_params']['host'] = args.host
            config['connection_params']['database'] = args.database
            if args.port:
                config['connection_params']['port'] = args.port
            if args.username:
                config['connection_params']['username'] = args.username
            if args.password:
                config['connection_params']['password'] = args.password
                
        elif args.db_type == 'sqlite':
            if not args.database_path:
                print("❌ --database-path is required for SQLite")
                return
            config['connection_params']['database_path'] = args.database_path
    
    # Validate connection parameters
    print("🔍 Validating connection parameters...")
    validation = processor.validate_database_params(
        config['db_type'], 
        config['connection_params']
    )
    
    if not validation.get('valid', False):
        print("❌ Invalid connection parameters:")
        for error in validation.get('errors', []):
            print(f"   - {error}")
        for param in validation.get('missing_params', []):
            print(f"   - Missing parameter: {param}")
        return
    
    # Test connection
    print("🔌 Testing database connection...")
    test_result = processor.test_database_connection(
        config['db_type'],
        config['connection_params']
    )
    
    if not test_result['success']:
        print(f"❌ Connection test failed: {test_result['error']}")
        return
    
    print(f"✅ {test_result['message']}")
    
    # If test-only mode, exit here
    if args.test_only:
        print("✅ Connection test successful. Exiting (test-only mode).")
        return
    
    # Process addresses from database
    print("\n🚀 Starting address processing from database...")
    
    result = processor.process_database_input(
        db_type=config['db_type'],
        connection_params=config['connection_params'],
        query=config.get('query'),
        table_name=config.get('table_name'),
        address_columns=config.get('address_columns'),
        limit=config.get('limit'),
        batch_size=config.get('batch_size', 10),
        use_free_apis=config.get('use_free_apis', True)
    )
    
    if result['success']:
        print("\n🎉 Database address processing completed successfully!")
        print(f"📊 Processing Summary:")
        print(f"   📥 Records extracted: {result['records_processed']}")
        print(f"   📁 Input CSV: {result['input_csv_path']}")
        print(f"   📁 Output CSV: {result['output_csv_path']}")
        print(f"   🗃️ Database type: {result['database_type']}")
        
        # Show processing details if available
        if 'processing_summary' in result:
            summary = result['processing_summary']
            if isinstance(summary, dict):
                print(f"   ✅ Successful: {summary.get('success_count', 'N/A')}")
                print(f"   ❌ Errors: {summary.get('error_count', 'N/A')}")
        
    else:
        print(f"\n❌ Database address processing failed: {result['error']}")
        if 'input_csv_path' in result:
            print(f"   📁 Extracted CSV available at: {result['input_csv_path']}")

def create_sample_config():
    """Create sample configuration files for different database types"""
    
    configs = {
        'sqlserver_config.json': {
            "db_type": "sqlserver",
            "connection_params": {
                "server": "localhost\\SQLEXPRESS",
                "database": "AddressDB"
            },
            "table_name": "Customers",
            "address_columns": ["FullAddress", "City", "State"],
            "limit": 100,
            "batch_size": 10,
            "use_free_apis": True
        },
        'azure_sql_config.json': {
            "db_type": "azure_sql",
            "connection_params": {
                "server": "yourserver.database.windows.net",
                "database": "yourdb",
                "username": "yourusername",
                "password": "yourpassword"
            },
            "query": "SELECT Address, City, State FROM Customers WHERE Country = 'Canada'",
            "limit": 500,
            "batch_size": 15,
            "use_free_apis": True
        },
        'mysql_config.json': {
            "db_type": "mysql",
            "connection_params": {
                "host": "localhost",
                "port": 3306,
                "database": "address_db",
                "username": "root",
                "password": "password"
            },
            "table_name": "locations",
            "address_columns": ["full_address"],
            "limit": 200,
            "batch_size": 12,
            "use_free_apis": True
        }
    }
    
    for filename, config in configs.items():
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"📄 Created sample config: {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--create-sample-configs':
        create_sample_config()
    else:
        main()
