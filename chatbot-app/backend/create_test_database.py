#!/usr/bin/env python3
"""
Create a test SQLite database with sample address data for testing
"""

import sqlite3
import os
from pathlib import Path

def create_test_database():
    """Create a test SQLite database with sample address data"""
    
    # Create test database in the backend directory
    db_path = Path(__file__).parent / "test_addresses.db"
    
    # Remove existing database if it exists
    if db_path.exists():
        os.remove(db_path)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            full_address TEXT,
            street_address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            country TEXT,
            phone TEXT,
            created_date TEXT
        )
    ''')
    
    # Sample address data for testing
    sample_data = [
        (1, "John Smith", "john@email.com", "123 Main Street, New York, NY 10001", "123 Main Street", "New York", "NY", "10001", "USA", "555-0101", "2025-01-15"),
        (2, "Jane Doe", "jane@email.com", "456 Oak Avenue, Los Angeles, CA 90210", "456 Oak Avenue", "Los Angeles", "CA", "90210", "USA", "555-0102", "2025-01-16"),
        (3, "Bob Johnson", "bob@email.com", "789 Pine Rd, Chicago, IL 60601", "789 Pine Road", "Chicago", "IL", "60601", "USA", "555-0103", "2025-01-17"),
        (4, "Alice Brown", "alice@email.com", "321 Elm St, Houston, TX 77001", "321 Elm Street", "Houston", "TX", "77001", "USA", "555-0104", "2025-01-18"),
        (5, "Charlie Wilson", "charlie@email.com", "654 Maple Ave, Phoenix, AZ 85001", "654 Maple Avenue", "Phoenix", "AZ", "85001", "USA", "555-0105", "2025-01-19"),
        (6, "Diana Miller", "diana@email.com", "987 Cedar Lane, Philadelphia, PA 19101", "987 Cedar Lane", "Philadelphia", "PA", "19101", "USA", "555-0106", "2025-01-20"),
        (7, "Frank Davis", "frank@email.com", "147 Birch Street, San Antonio, TX 78201", "147 Birch Street", "San Antonio", "TX", "78201", "USA", "555-0107", "2025-01-21"),
        (8, "Grace Lee", "grace@email.com", "258 Walnut Drive, San Diego, CA 92101", "258 Walnut Drive", "San Diego", "CA", "92101", "USA", "555-0108", "2025-01-22"),
        (9, "Henry Clark", "henry@email.com", "369 Spruce Court, Dallas, TX 75201", "369 Spruce Court", "Dallas", "TX", "75201", "USA", "555-0109", "2025-01-23"),
        (10, "Ivy Rodriguez", "ivy@email.com", "741 Redwood Blvd, San Jose, CA 95101", "741 Redwood Boulevard", "San Jose", "CA", "95101", "USA", "555-0110", "2025-01-24"),
        # Add some addresses with variations/errors for testing
        (11, "Jack Taylor", "jack@email.com", "852 Broadway St, NYC, New York 10003", "852 Broadway Street", "New York City", "NY", "10003", "USA", "555-0111", "2025-01-25"),
        (12, "Kate Anderson", "kate@email.com", "963 Fifth Ave, Manhattan, NY", "963 Fifth Avenue", "Manhattan", "NY", "", "USA", "555-0112", "2025-01-26"),
        (13, "Leo Martinez", "leo@email.com", "159 Hollywood Blvd, LA, California", "159 Hollywood Boulevard", "Los Angeles", "CA", "", "USA", "555-0113", "2025-01-27"),
        (14, "Maya Patel", "maya@email.com", "357 Michigan Ave, Chicago Illinois 60611", "357 Michigan Avenue", "Chicago", "IL", "60611", "USA", "555-0114", "2025-01-28"),
        (15, "Noah Kim", "noah@email.com", "486 Market Street, San Francisco CA 94102", "486 Market Street", "San Francisco", "CA", "94102", "USA", "555-0115", "2025-01-29")
    ]
    
    cursor.executemany('''
        INSERT INTO customers (id, name, email, full_address, street_address, city, state, zip_code, country, phone, created_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    # Create a second table for additional testing
    cursor.execute('''
        CREATE TABLE properties (
            property_id INTEGER PRIMARY KEY,
            property_type TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city_name TEXT,
            state_code TEXT,
            postal_code TEXT,
            country_name TEXT,
            listing_price REAL,
            square_feet INTEGER
        )
    ''')
    
    property_data = [
        (1, "House", "1001 Residential Lane", "", "Austin", "TX", "73301", "United States", 450000, 2500),
        (2, "Condo", "2002 Downtown Plaza", "Unit 5B", "Miami", "FL", "33101", "United States", 350000, 1200),
        (3, "Apartment", "3003 University Drive", "Apt 12", "Seattle", "WA", "98101", "United States", 280000, 900),
        (4, "House", "4004 Suburban Circle", "", "Denver", "CO", "80201", "United States", 520000, 3200),
        (5, "Townhouse", "5005 Historic Street", "", "Boston", "MA", "02101", "United States", 680000, 1800)
    ]
    
    cursor.executemany('''
        INSERT INTO properties (property_id, property_type, address_line1, address_line2, city_name, state_code, postal_code, country_name, listing_price, square_feet)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', property_data)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"✅ Test database created: {db_path}")
    print(f"📊 Created 2 tables:")
    print(f"   • customers (15 records) - mixed address formats")
    print(f"   • properties (5 records) - real estate data")
    print(f"\n🧪 Ready for testing!")
    
    return str(db_path)

if __name__ == "__main__":
    create_test_database()
