#!/usr/bin/env python3
"""
Database Connection Examples for AddressIQ
Demonstrates both individual parameters and connection strings
"""

import subprocess
import sys

def run_command(description, command):
    """Run a command and display results"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    print()
    
    # Uncomment to actually run the commands
    # result = subprocess.run(command, capture_output=True, text=True)
    # print(result.stdout)
    # if result.stderr:
    #     print("Errors:", result.stderr)

def main():
    """Demo different connection methods"""
    
    print("📊 AddressIQ Database Connection Examples")
    print("=" * 60)
    print("This script shows examples of both connection methods.")
    print("Uncomment the subprocess.run() calls to actually execute.")
    
    # Azure SQL Examples
    print("\n🔵 AZURE SQL DATABASE EXAMPLES")
    
    # Method 1: Individual Parameters
    run_command(
        "Azure SQL with Individual Parameters",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "azure_sql",
            "--db-server", "dev-server-sqldb.database.windows.net",
            "--db-name", "dev-aurora-sqldb", 
            "--db-username", "aurora",
            "--db-password", "rcqM4?nTZH+hpfX7",
            "--db-query", "SELECT TOP 3 Site_Address_1 as address FROM Mast_Site",
            "--db-limit", "3"
        ]
    )
    
    # Method 2: Connection String
    run_command(
        "Azure SQL with Connection String (Recommended)",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "azure_sql",
            "--db-connection-string", "Server=dev-server-sqldb.database.windows.net;Database=dev-aurora-sqldb;User Id=aurora;Password=rcqM4?nTZH+hpfX7",
            "--db-query", "SELECT TOP 3 Site_Address_1 as address FROM Mast_Site",
            "--db-limit", "3"
        ]
    )
    
    # SQL Server Examples
    print("\n🟢 SQL SERVER EXAMPLES")
    
    run_command(
        "SQL Server with Windows Authentication",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "sqlserver",
            "--db-connection-string", "Server=localhost\\SQLEXPRESS;Database=AddressDB;Trusted_Connection=yes",
            "--db-table", "customers",
            "--db-limit", "5"
        ]
    )
    
    # MySQL Examples  
    print("\n🟡 MYSQL EXAMPLES")
    
    run_command(
        "MySQL with Connection String",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "mysql",
            "--db-connection-string", "server=localhost;database=address_db;uid=root;pwd=password;port=3306",
            "--db-table", "locations",
            "--db-limit", "10"
        ]
    )
    
    # PostgreSQL Examples
    print("\n🔵 POSTGRESQL EXAMPLES")
    
    run_command(
        "PostgreSQL with URI Connection String",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "postgresql", 
            "--db-connection-string", "postgresql://postgres:password@localhost:5432/addressdb",
            "--db-table", "addresses",
            "--db-limit", "5"
        ]
    )
    
    # SQLite Examples
    print("\n🟠 SQLITE EXAMPLES")
    
    run_command(
        "SQLite with Connection String",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "sqlite",
            "--db-connection-string", "C:\\data\\addresses.db",
            "--db-table", "locations",
            "--db-limit", "10"
        ]
    )
    
    # Preview Examples
    print("\n🔍 PREVIEW EXAMPLES")
    
    run_command(
        "Preview Database Tables",
        [
            "python", "csv_address_processor.py",
            "--database",
            "--db-type", "azure_sql",
            "--db-connection-string", "Server=dev-server-sqldb.database.windows.net;Database=dev-aurora-sqldb;User Id=aurora;Password=rcqM4?nTZH+hpfX7",
            "--db-preview"
        ]
    )
    
    run_command(
        "Preview Specific Table Structure",
        [
            "python", "csv_address_processor.py", 
            "--database",
            "--db-type", "azure_sql",
            "--db-connection-string", "Server=dev-server-sqldb.database.windows.net;Database=dev-aurora-sqldb;User Id=aurora;Password=rcqM4?nTZH+hpfX7",
            "--db-table", "Mast_Site",
            "--db-preview"
        ]
    )
    
    print("\n" + "="*60)
    print("✅ Examples complete!")
    print("💡 To run these commands, uncomment the subprocess.run() calls in this script")
    print("💡 Or copy-paste any of the commands above into your terminal")

if __name__ == "__main__":
    main()
