# Database Input Method for AddressIQ

## Overview

AddressIQ now supports direct database connectivity as an input method, allowing you to process addresses directly from your existing databases without having to export data to CSV files first.

## Supported Database Types

### Currently Supported:
- **SQL Server** (with Windows Authentication or SQL Authentication)
- **Azure SQL Database** 
- **MySQL**
- **PostgreSQL**
- **Oracle** (requires Oracle client installation)
- **SQLite**

### Available Drivers Check:
```bash
python csv_address_processor.py --list-db-types
```

## Input Methods Summary

| Method | Description | Usage |
|--------|-------------|-------|
| **1. Direct Address** | Single address input | `--address "123 Main St, NYC"` |
| **2. Multiple Addresses** | Multiple addresses input | `--address "123 Main St" "456 Oak Ave"` |
| **3. CSV/Excel Files** | Files in inbound directory | `--batch-process` |
| **4. Database Connectivity** | ⭐ **NEW** - Direct database access | `--database --db-type mysql ...` |

## Database Input Usage

### Basic Command Structure:
```bash
python csv_address_processor.py --database --db-type <type> [connection params] [query params]
```

### Example Use Cases:

#### 1. SQL Server with Windows Authentication
```bash
python csv_address_processor.py --database \
  --db-type sqlserver \
  --db-server "localhost\SQLEXPRESS" \
  --db-name "CustomerDB" \
  --db-table "Customers" \
  --db-address-columns "FullAddress,City,State"
```

#### 2. Azure SQL Database (Improved Example)
```bash
# Basic usage with safety defaults
python csv_address_processor.py --database \
  --db-type azure_sql \
  --db-server "yourserver.database.windows.net" \
  --db-name "yourdb" \
  --db-username "user" \
  --db-password "pass" \
  --db-table "addresses" \
  --db-address-columns "street_address,city,state,postal_code"
  # Automatically uses 50 record limit for safety

# Preview table structure first (recommended)
python csv_address_processor.py --database \
  --db-type azure_sql \
  --db-server "yourserver.database.windows.net" \
  --db-name "yourdb" \
  --db-username "user" \
  --db-password "pass" \
  --db-table "customers" \
  --db-preview

# Process with custom limit and specific columns
python csv_address_processor.py --database \
  --db-type azure_sql \
  --db-server "yourserver.database.windows.net" \
  --db-name "yourdb" \
  --db-username "user" \
  --db-password "pass" \
  --db-query "SELECT customer_id, full_address, city FROM customers WHERE country='USA'" \
  --db-limit 200
```

#### 3. MySQL Database
```bash
python csv_address_processor.py --database \
  --db-type mysql \
  --db-host "localhost" \
  --db-name "address_db" \
  --db-username "root" \
  --db-password "password" \
  --db-table "locations" \
  --db-limit 500
```

#### 4. PostgreSQL Database
```bash
python csv_address_processor.py --database \
  --db-type postgresql \
  --db-host "localhost" \
  --db-port 5432 \
  --db-name "gis_data" \
  --db-username "postgres" \
  --db-password "password" \
  --db-query "SELECT full_address FROM properties WHERE city='Toronto'"
```

#### 5. SQLite Database
```bash
python csv_address_processor.py --database \
  --db-type sqlite \
  --db-path "/path/to/database.db" \
  --db-table "addresses" \
  --db-limit 100
```

## 🔗 Connection String Support (NEW!)

As an alternative to specifying individual connection parameters, you can now use connection strings for cleaner, more standard database connections.

### Connection String Examples:

#### Azure SQL Database
```bash
# Standard connection string format
python csv_address_processor.py --database \
  --db-type azure_sql \
  --db-connection-string "Server=dev-server-sqldb.database.windows.net;Database=dev-aurora-sqldb;User Id=aurora;Password=rcqM4?nTZH+hpfX7" \
  --db-query "SELECT Site_Address_1 as address_line1, Site_City as city FROM Mast_Site" \
  --db-limit 5

# Alternative format
python csv_address_processor.py --database \
  --db-type azure_sql \
  --db-connection-string "Data Source=server.database.windows.net;Initial Catalog=mydb;User ID=user;Password=pass" \
  --db-table "customers"
```

#### SQL Server
```bash
# Windows Authentication
python csv_address_processor.py --database \
  --db-type sqlserver \
  --db-connection-string "Server=localhost\\SQLEXPRESS;Database=AddressDB;Trusted_Connection=yes" \
  --db-table "addresses"

# SQL Server Authentication
python csv_address_processor.py --database \
  --db-type sqlserver \
  --db-connection-string "Server=myserver;Database=mydb;User Id=sa;Password=password" \
  --db-table "customers"
```

#### MySQL
```bash
python csv_address_processor.py --database \
  --db-type mysql \
  --db-connection-string "server=localhost;database=address_db;uid=root;pwd=password;port=3306" \
  --db-table "locations"
```

#### PostgreSQL
```bash
# Key-value format
python csv_address_processor.py --database \
  --db-type postgresql \
  --db-connection-string "host=localhost;database=addressdb;username=postgres;password=pass;port=5432" \
  --db-table "addresses"

# PostgreSQL URI format
python csv_address_processor.py --database \
  --db-type postgresql \
  --db-connection-string "postgresql://postgres:password@localhost:5432/addressdb" \
  --db-table "addresses"
```

#### SQLite
```bash
# For SQLite, the connection string is just the file path
python csv_address_processor.py --database \
  --db-type sqlite \
  --db-connection-string "C:\\data\\addresses.db" \
  --db-table "locations"
```

### Benefits of Connection Strings:
- ✅ **Cleaner commands** - Single parameter instead of 4-5 separate ones
- ✅ **Standard format** - Uses industry-standard connection string formats  
- ✅ **Easy copy-paste** - Can copy connection strings from other applications
- ✅ **Environment variables** - Easier to store in config files or environment variables
- ✅ **Tool compatibility** - Same format used by other database tools

## Safety Features & Best Practices

### 🛡️ **Built-in Safety Features:**

1. **Default 5 Record Limit** - Protects against accidentally processing huge tables
2. **Large Limit Warning** - Warns when processing >10,000 records  
3. **Connection Validation** - Tests connection before processing
4. **Address Column Detection** - Auto-detects likely address columns
5. **Table Preview** - Explore table structure before processing

### 🔍 **Recommended Workflow:**

```bash
# Step 1: List supported database types
python csv_address_processor.py --list-db-types

# Step 2: Preview table structure (see what's available)
python csv_address_processor.py --database \
  --db-type mysql \
  --db-host localhost \
  --db-name mydb \
  --db-username user \
  --db-password pass \
  --db-preview

# Step 3: Preview specific table
python csv_address_processor.py --database \
  --db-type mysql \
  --db-host localhost \
  --db-name mydb \
  --db-username user \
  --db-password pass \
  --db-table customers \
  --db-preview

# Step 4: Process with detected columns (or specify your own)
python csv_address_processor.py --database \
  --db-type mysql \
  --db-host localhost \
  --db-name mydb \
  --db-username user \
  --db-password pass \
  --db-table customers \
  --db-address-columns "street_address,city,state" \
  --db-limit 100
```

### Connection Parameters:

| Parameter | SQL Server | Azure SQL | MySQL | PostgreSQL | Oracle | SQLite |
|-----------|------------|-----------|-------|------------|--------|--------|
| `--db-server` | ✅ Required | ✅ Required | ❌ | ❌ | ❌ | ❌ |
| `--db-host` | ❌ | ❌ | ✅ Required | ✅ Required | ✅ Required | ❌ |
| `--db-port` | ❌ | ❌ | ⚪ Optional | ⚪ Optional | ⚪ Optional | ❌ |
| `--db-name` | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ |
| `--db-username` | ⚪ Optional* | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ |
| `--db-password` | ⚪ Optional* | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ |
| `--db-path` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Required |

*Optional for SQL Server when using Windows Authentication

### Query Parameters:

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--db-query` | Custom SQL query | None | `"SELECT address, city FROM customers"` |
| `--db-table` | Table name (if no custom query) | None | `"customers"` |
| `--db-address-columns` | Comma-separated address columns | Auto-detect | `"full_address,city,state"` |
| `--db-limit` | Limit number of records | **5** | `1000` |
| `--db-preview` | Preview table structure only | False | `--db-preview` |

### 💡 **Key Improvements:**
- **Default 5 record limit** prevents accidental large data pulls
- **Column specification recommended** for better accuracy
- **Preview mode** helps explore database structure
- **Auto-detection** as fallback when columns not specified

## Workflow

1. **Database Connection Test** - Validates connection parameters
2. **Data Extraction** - Executes query and saves to CSV in `inbound/` directory
3. **Address Detection** - Automatically detects potential address columns
4. **Address Processing** - Uses existing AddressIQ pipeline to standardize addresses
5. **Output Generation** - Saves results to `outbound/` directory

## Advanced Usage

### Custom Configuration Files

For complex database configurations, use JSON config files:

```bash
python database_address_processor.py --config-file azure_config.json
```

**Example config file (`azure_config.json`):**
```json
{
  "db_type": "azure_sql",
  "connection_params": {
    "server": "yourserver.database.windows.net",
    "database": "yourdb",
    "username": "yourusername",
    "password": "yourpassword"
  },
  "query": "SELECT CustomerID, FullAddress, City, State FROM Customers WHERE Country = 'Canada'",
  "limit": 1000,
  "batch_size": 15,
  "use_free_apis": true
}
```

### Create Sample Configuration Files
```bash
python database_address_processor.py --create-sample-configs
```

This creates sample configuration files for different database types.

## Error Handling

### Common Issues:

1. **Driver Not Available**
   ```
   ❌ Driver not available for mysql
   ```
   **Solution:** Install the required driver:
   ```bash
   pip install mysql-connector-python
   ```

2. **Connection Failed**
   ```
   ❌ Connection failed: Access denied for user 'root'@'localhost'
   ```
   **Solution:** Check username/password and database permissions

3. **Invalid Parameters**
   ```
   ❌ Invalid parameters: Missing parameter: host
   ```
   **Solution:** Provide all required connection parameters

### Testing Connections

Test database connection without processing:
```bash
python database_address_processor.py \
  --db-type mysql \
  --db-host localhost \
  --db-name test \
  --db-username root \
  --db-password password \
  --test-only
```

## Security Considerations

1. **Password Security**: Avoid hardcoding passwords in scripts
2. **Environment Variables**: Use environment variables for sensitive data
3. **Read-Only Access**: Use database users with read-only permissions
4. **Connection Encryption**: Use encrypted connections when available

## Installation Requirements

### Core Requirements (always needed):
```bash
pip install pandas pyodbc
```

### Database-Specific Drivers:
```bash
# MySQL
pip install mysql-connector-python

# PostgreSQL  
pip install psycopg2-binary

# Oracle (requires Oracle client)
pip install cx_Oracle
```

## Performance Tips

1. **Use LIMIT**: Always specify `--db-limit` for large tables
2. **Optimize Queries**: Use WHERE clauses to filter relevant records
3. **Batch Processing**: Adjust `--batch-size` based on your system
4. **Index Usage**: Ensure your database queries use appropriate indexes

## Integration with Existing Workflow

The database input method seamlessly integrates with your existing AddressIQ workflow:

1. **Database → CSV → Processing → Results**
2. Uses the same standardization algorithms
3. Outputs to the same `outbound/` directory structure
4. Compatible with all existing output formats
5. Supports the same caching and enhancement features

## Example Complete Workflow

```bash
# 1. List supported database types
python csv_address_processor.py --list-db-types

# 2. Test connection
python database_address_processor.py \
  --db-type mysql \
  --db-host localhost \
  --db-name customer_db \
  --db-username app_user \
  --db-password secure_password \
  --test-only

# 3. Process addresses
python csv_address_processor.py --database \
  --db-type mysql \
  --db-host localhost \
  --db-name customer_db \
  --db-username app_user \
  --db-password secure_password \
  --db-query "SELECT customer_id, street_address, city, state FROM customers WHERE state IN ('CA', 'NY')" \
  --db-limit 1000 \
  --batch-size 15

# 4. Results will be available in the outbound/ directory
```

This new database input method significantly enhances AddressIQ's capabilities by eliminating the need for manual data export/import processes, making it more suitable for enterprise environments and automated workflows.
