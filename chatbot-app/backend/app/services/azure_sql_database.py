import hashlib
import pyodbc
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables from the backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

class AzureSQLDatabaseService:
    def __init__(self):
        # Direct configuration for testing
        self.server = "dev-server-sqldb.database.windows.net"
        self.database = "dev-aurora-sqldb"
        self.username = "aurora"
        self.password = "rcqM4?nTZH+hpfX7"
        
        print(f"🔧 Database Configuration:")
        print(f"   Server: {self.server}")
        print(f"   Database: {self.database}")
        print(f"   Username: {self.username}")
        print(f"   Password: {'*' * len(self.password) if self.password else 'NOT SET'}")
        
        if not self.password:
            raise Exception("AZURE_SQL_PASSWORD not set")
        
        # Try different ODBC drivers in order of preference
        self.drivers = [
            "{ODBC Driver 17 for SQL Server}",
            "{ODBC Driver 18 for SQL Server}",
            "{ODBC Driver 13 for SQL Server}",
            "{SQL Server Native Client 11.0}",
            "{SQL Server}"
        ]
        
        self.connection_string = None
        self._find_working_driver()
        
        print(f"✅ Azure SQL Database service initialized")
    
    def _find_working_driver(self):
        """Find a working ODBC driver"""
        for driver in self.drivers:
            try:
                # Test connection string
                test_connection_string = (
                    f"DRIVER={driver};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=no;"
                    f"Connection Timeout=30;"
                )
                
                print(f"🔍 Testing driver: {driver}")
                
                # Try to connect
                conn = pyodbc.connect(test_connection_string)
                conn.close()
                
                # If successful, use this driver
                self.connection_string = test_connection_string
                print(f"✅ Using ODBC driver: {driver}")
                return
                
            except Exception as e:
                print(f"⚠️  Driver {driver} failed: {str(e)[:100]}...")
                continue
        
        # If no driver works, raise an error
        raise Exception("No compatible ODBC driver found. Please check your credentials and network connectivity.")
    
    def get_connection(self):
        """Get database connection"""
        if not self.connection_string:
            raise Exception("No valid database connection string available")
        
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            raise
    
    def normalize_address(self, address: str) -> str:
        """Normalize address string for consistent hashing"""
        # Remove extra spaces, convert to lowercase, remove special chars
        normalized = ' '.join(address.lower().strip().split())
        # Remove common punctuation that doesn't affect address meaning
        normalized = normalized.replace(',', '').replace('.', '').replace('-', ' ')
        normalized = normalized.replace('#', '').replace('apt', '').replace('suite', '').replace('unit', '')
        return normalized
    
    def generate_address_hash(self, address: str) -> str:
        """Generate SHA256 hash for normalized address"""
        normalized = self.normalize_address(address)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def find_existing_address(self, address: str, similarity_threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """Find existing similar address in database"""
        address_hash = self.generate_address_hash(address)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First, try exact hash match
            cursor.execute('''
                SELECT * FROM standardized_addresses 
                WHERE address_hash = ?
            ''', (address_hash,))
            
            result = cursor.fetchone()
            if result:
                # Update usage count for exact match
                cursor.execute('''
                    UPDATE standardized_addresses 
                    SET usage_count = usage_count + 1, updated_at = GETDATE()
                    WHERE id = ?
                ''', (result[0],))
                conn.commit()
                conn.close()
                return self._row_to_dict(result)
            
            # If no exact match, try fuzzy matching based on postal code
            normalized_input = self.normalize_address(address)
            words = normalized_input.split()
            
            # Extract potential postal code for fuzzy matching
            potential_postal = None
            for word in words:
                if len(word) >= 4 and (word.isdigit() or any(c.isalpha() for c in word)):
                    potential_postal = word
                    break
            
            if potential_postal and len(potential_postal) >= 4:
                # Look for similar addresses with same postal code
                cursor.execute('''
                    SELECT TOP 10 *, original_address
                    FROM standardized_addresses 
                    WHERE postal_code LIKE ? OR postal_code = ?
                    ORDER BY usage_count DESC
                ''', (f"%{potential_postal}%", potential_postal))
                
                results = cursor.fetchall()
                
                # Perform similarity check on normalized addresses
                for row in results:
                    existing_normalized = self.normalize_address(row[2])  # original_address
                    similarity = self._calculate_similarity(normalized_input, existing_normalized)
                    
                    if similarity >= similarity_threshold:
                        # Update usage count for similar match
                        cursor.execute('''
                            UPDATE standardized_addresses 
                            SET usage_count = usage_count + 1, updated_at = GETDATE()
                            WHERE id = ?
                        ''', (row[0],))
                        conn.commit()
                        conn.close()
                        return self._row_to_dict(row)
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"❌ Error finding existing address: {str(e)}")
            return None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using token matching"""
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def save_address(self, original_address: str, standardized_result: Dict[str, Any]) -> int:
        """Save standardized address to database (only if successfully processed)"""
        
        # Only save if the address was successfully processed
        if (standardized_result.get('status') != 'success' or 
            standardized_result.get('confidence') == 'low' or
            'failed' in standardized_result.get('api_source', '') or
            'fallback' in standardized_result.get('api_source', '')):
            print(f"   ⚠️  Skipping database save - address not successfully processed")
            return None
        
        address_hash = self.generate_address_hash(original_address)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if address already exists (should not happen due to find_existing_address check)
            cursor.execute('SELECT id, usage_count FROM standardized_addresses WHERE address_hash = ?', (address_hash,))
            existing = cursor.fetchone()
            
            if existing:
                # Update usage count and updated_at manually
                cursor.execute('''
                    UPDATE standardized_addresses 
                    SET usage_count = usage_count + 1, updated_at = GETDATE()
                    WHERE id = ?
                ''', (existing[0],))
                conn.commit()
                conn.close()
                return existing[0]
            
            # Insert new address with all the enhanced columns
            cursor.execute('''
                INSERT INTO standardized_addresses (
                    address_hash, original_address, formatted_address,
                    street_number, street_name, street_type, unit_type, unit_number,
                    building_name, floor_number, city, state, county, postal_code, 
                    country, country_code, district, region, suburb, locality, 
                    sublocality, canton, prefecture, oblast, confidence, issues, 
                    api_source, latitude, longitude, address_type, po_box,
                    delivery_instructions, mail_route
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                address_hash,
                original_address,
                standardized_result.get('formatted_address', ''),
                standardized_result.get('street_number'),
                standardized_result.get('street_name'),
                standardized_result.get('street_type'),
                standardized_result.get('unit_type'),
                standardized_result.get('unit_number'),
                standardized_result.get('building_name'),
                standardized_result.get('floor_number'),
                standardized_result.get('city'),
                standardized_result.get('state'),
                standardized_result.get('county'),
                standardized_result.get('postal_code'),
                standardized_result.get('country'),
                standardized_result.get('country_code'),
                standardized_result.get('district'),
                standardized_result.get('region'),
                standardized_result.get('suburb'),
                standardized_result.get('locality'),
                standardized_result.get('sublocality'),
                standardized_result.get('canton'),
                standardized_result.get('prefecture'),
                standardized_result.get('oblast'),
                standardized_result.get('confidence'),
                str(standardized_result.get('issues', [])),
                standardized_result.get('api_source'),
                float(standardized_result.get('latitude', 0)) if standardized_result.get('latitude') and str(standardized_result.get('latitude')).strip() else None,
                float(standardized_result.get('longitude', 0)) if standardized_result.get('longitude') and str(standardized_result.get('longitude')).strip() else None,
                standardized_result.get('address_type'),
                standardized_result.get('po_box'),
                standardized_result.get('delivery_instructions'),
                standardized_result.get('mail_route')
            ))
            
            # Get the inserted ID
            cursor.execute('SELECT @@IDENTITY')
            address_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            print(f"   💾 Saved to Azure SQL Database (ID: {int(address_id)})")
            return int(address_id)
            
        except Exception as e:
            print(f"❌ Error saving address: {str(e)}")
            return None
    
    def get_address_by_id(self, address_id: int) -> Optional[Dict[str, Any]]:
        """Get address by unique ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM standardized_addresses WHERE id = ?', (address_id,))
            result = cursor.fetchone()
            conn.close()
            
            return self._row_to_dict(result) if result else None
            
        except Exception as e:
            print(f"❌ Error getting address by ID: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM standardized_addresses')
            total_addresses = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(usage_count) FROM standardized_addresses')
            total_usages = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM standardized_addresses WHERE usage_count > 1')
            reused_addresses = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_unique_addresses': total_addresses,
                'total_address_lookups': total_usages,
                'reused_addresses': reused_addresses,
                'cache_hit_rate': (total_usages - total_addresses) / total_usages * 100 if total_usages > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error getting database stats: {str(e)}")
            return {
                'total_unique_addresses': 0,
                'total_address_lookups': 0,
                'reused_addresses': 0,
                'cache_hit_rate': 0
            }
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        if not row:
            return None
        
        return {
            'id': row[0],
            'address_hash': row[1],
            'original_address': row[2],
            'formatted_address': row[3],
            'street_number': row[4],
            'street_name': row[5],
            'street_type': row[6],
            'unit_type': row[7],
            'unit_number': row[8],
            'city': row[9],
            'state': row[10],
            'postal_code': row[11],
            'country': row[12],
            'latitude': row[13],
            'longitude': row[14],
            'confidence': row[15],
            'issues': row[16],
            'api_source': row[17],
            'created_at': row[18],
            'updated_at': row[19],
            'usage_count': row[20]
        }
