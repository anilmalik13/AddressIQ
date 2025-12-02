from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import subprocess
import time
from pathlib import Path
from .services.azure_openai import get_access_token, connect_wso2, read_csv_with_encoding_detection
from csv_address_processor import CSVAddressProcessor  # direct import for in-process execution
import uuid
import re
import sys
import json
import pyodbc
import requests  # for webhook notifications
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
# no external encoding detector here; rely on utf-8 replacement for preview

# Import database job manager
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import job_manager

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure upload settings - using inbound folder instead of C:\uploaded_files
BASE_DIR = Path(__file__).parent.parent  # Points to backend folder
INBOUND_FOLDER = BASE_DIR / 'inbound'
OUTBOUND_FOLDER = BASE_DIR / 'outbound'
SAMPLES_FOLDER = BASE_DIR / 'samples'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['INBOUND_FOLDER'] = str(INBOUND_FOLDER)
app.config['OUTBOUND_FOLDER'] = str(OUTBOUND_FOLDER)
app.config['SAMPLES_FOLDER'] = str(SAMPLES_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
os.makedirs(INBOUND_FOLDER, exist_ok=True)
os.makedirs(OUTBOUND_FOLDER, exist_ok=True)
os.makedirs(SAMPLES_FOLDER, exist_ok=True)

# DEPRECATED: In-memory storage - now using database
# Store processing status (kept for backwards compatibility during migration)
processing_status = {}

# Initialize automatic cleanup scheduler
scheduler = BackgroundScheduler(daemon=True)

# Configuration for cleanup schedule
CLEANUP_HOUR = int(os.getenv('CLEANUP_HOUR', '2'))  # Default: 2 AM
CLEANUP_MINUTE = int(os.getenv('CLEANUP_MINUTE', '0'))  # Default: 0 minutes
CLEANUP_ENABLED = os.getenv('CLEANUP_ENABLED', 'true').lower() == 'true'  # Default: enabled

def automatic_cleanup_job():
    """Background job to automatically clean up expired files and jobs"""
    try:
        print(f"\n🧹 [Automatic Cleanup] Starting scheduled cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result = job_manager.cleanup_expired_jobs(dry_run=False)
        
        deleted_count = result.get('deleted_count', 0)
        errors = result.get('errors', [])
        
        if deleted_count > 0:
            print(f"✅ [Automatic Cleanup] Successfully deleted {deleted_count} expired job(s)")
            print(f"   Deleted jobs: {', '.join(result.get('deleted_jobs', [])[:5])}{'...' if deleted_count > 5 else ''}")
        else:
            print("✅ [Automatic Cleanup] No expired jobs found")
        
        if errors:
            print(f"⚠️  [Automatic Cleanup] {len(errors)} error(s) occurred:")
            for err in errors[:3]:  # Show first 3 errors
                print(f"   - Job {err.get('job_id')}: {err.get('error')}")
        
        print(f"🧹 [Automatic Cleanup] Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return result
        
    except Exception as e:
        print(f"❌ [Automatic Cleanup] Failed: {str(e)}")
        return {'error': str(e), 'deleted_count': 0}

if CLEANUP_ENABLED:
    # Schedule cleanup to run daily at configured time (default: 2 AM)
    scheduler.add_job(
        func=automatic_cleanup_job,
        trigger=CronTrigger(hour=CLEANUP_HOUR, minute=CLEANUP_MINUTE),
        id='automatic_cleanup',
        name='Automatic Expired Files Cleanup',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    print(f"✅ Automatic cleanup scheduler started (runs daily at {CLEANUP_HOUR:02d}:{CLEANUP_MINUTE:02d})")
    print(f"   Next cleanup: {scheduler.get_job('automatic_cleanup').next_run_time}")
    
    # Run cleanup immediately on startup (in background thread to not block startup)
    print("🚀 [Startup Cleanup] Running initial cleanup on application start...")
    import threading
    startup_cleanup = threading.Thread(target=automatic_cleanup_job, daemon=True)
    startup_cleanup.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown(wait=False))
else:
    print("⚠️  Automatic cleanup is DISABLED (set CLEANUP_ENABLED=true to enable)")

# Simple API key security for public standardization endpoint
PUBLIC_API_KEY = os.getenv('ADDRESSIQ_PUBLIC_API_KEY')  # set in environment / .env

def _allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _check_api_key():
    """Validate API key from header X-API-Key or query parameter api_key if key configured.
    If no PUBLIC_API_KEY configured, allow all (development mode)."""
    if not PUBLIC_API_KEY:
        return True, None  # open mode
    supplied = request.headers.get('X-API-Key') or request.args.get('api_key')
    if supplied and supplied == PUBLIC_API_KEY:
        return True, None
    return False, 'Invalid or missing API key'

def _sanitize_address(addr: str) -> str:
    if not isinstance(addr, str):
        return ''
    # Remove control characters, trim length, neutralize script tags
    addr = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', addr)
    addr = addr.replace('\r', ' ').replace('\n', ' ').strip()
    # Basic strip of dangerous angle brackets
    addr = addr.replace('<', ' ').replace('>', ' ')
    # limit length
    if len(addr) > 500:
        addr = addr[:500]
    return addr

def _validate_file_upload_headers(df: pd.DataFrame) -> dict:
    """
    Validate headers for File Upload component.
    Case-insensitive comparison.
    
    Required headers:
    - Site_Name
    - Site_Address_1
    - Site_Address_2
    - Site_Address_3
    - Site_Address_4
    - Site_City
    - Site_State
    - Site_Postcode
    - Site_Country
    
    Returns:
        dict with 'valid' (bool) and 'error' (str) keys
    """
    required_headers = [
        'Site_Name',
        'Site_Address_1',
        'Site_Address_2',
        'Site_Address_3',
        'Site_Address_4',
        'Site_City',
        'Site_State',
        'Site_Postcode',
        'Site_Country'
    ]
    
    # Get actual headers from dataframe
    actual_headers = df.columns.tolist()
    
    # Convert to lowercase for case-insensitive comparison
    actual_headers_lower = [str(h).lower().strip() for h in actual_headers]
    required_headers_lower = [h.lower().strip() for h in required_headers]
    
    # Check if all required headers are present
    missing_headers = []
    for req_header in required_headers:
        req_lower = req_header.lower().strip()
        if req_lower not in actual_headers_lower:
            missing_headers.append(req_header)
    
    if missing_headers:
        return {
            'valid': False,
            'error': f"Missing required columns: {', '.join(missing_headers)}. Please ensure your file contains all required headers.",
            'missing_headers': missing_headers,
            'actual_headers': actual_headers
        }
    
    return {
        'valid': True,
        'error': None,
        'missing_headers': [],
        'actual_headers': actual_headers
    }

def _validate_compare_upload_headers(df: pd.DataFrame) -> dict:
    """
    Validate headers for Compare Upload component.
    Case-insensitive comparison.
    
    Required headers:
    - Site_Name
    - Site_Address_1
    - Site_Address_2
    - Site_Address_3
    - Site_Address_4
    - Site_City
    - Site_State
    - Site_Postcode
    - Site_Country
    
    Returns:
        dict with 'valid' (bool) and 'error' (str) keys
    """
    required_headers = [
        'Site_Name',
        'Site_Address_1',
        'Site_Address_2',
        'Site_Address_3',
        'Site_Address_4',
        'Site_City',
        'Site_State',
        'Site_Postcode',
        'Site_Country'
    ]
    
    # Get actual headers from dataframe
    actual_headers = df.columns.tolist()
    
    # Convert to lowercase for case-insensitive comparison
    actual_headers_lower = [str(h).lower().strip() for h in actual_headers]
    required_headers_lower = [h.lower().strip() for h in required_headers]
    
    # Check if all required headers are present
    missing_headers = []
    for req_header in required_headers:
        req_lower = req_header.lower().strip()
        if req_lower not in actual_headers_lower:
            missing_headers.append(req_header)
    
    if missing_headers:
        return {
            'valid': False,
            'error': f"Missing required columns: {', '.join(missing_headers)}. Please ensure your file contains all required headers.",
            'missing_headers': missing_headers,
            'actual_headers': actual_headers
        }
    
    # Check for extra headers (optional - just for information)
    extra_headers = []
    for actual_header in actual_headers:
        actual_lower = str(actual_header).lower().strip()
        if actual_lower not in required_headers_lower:
            extra_headers.append(actual_header)
    
    return {
        'valid': True,
        'error': None,
        'missing_headers': [],
        'extra_headers': extra_headers,
        'actual_headers': actual_headers
    }

# Helper for consistent status updates and lightweight logging
def _update_status(processing_id: str, **fields):
    """
    Update job status in database (and legacy in-memory dict for backwards compatibility)
    """
    # Handle log messages
    log_message = fields.pop('log', None)
    
    # Update database
    if log_message:
        job_manager.add_log(processing_id, log_message, fields.get('progress'))
    
    if fields:
        job_manager.update_job(processing_id, **fields)
    
    # Send webhook if job completed or failed
    if fields.get('status') in ['completed', 'failed', 'error']:
        _send_webhook_notification(processing_id)
    
    # LEGACY: Also update in-memory dict for backwards compatibility
    entry = processing_status.get(processing_id)
    if entry:
        now_iso = datetime.utcnow().isoformat() + 'Z'
        entry['updated_at'] = now_iso
        for k, v in fields.items():
            entry[k] = v
        if log_message:
            logs = entry.setdefault('logs', [])
            logs.append({'ts': now_iso, 'message': log_message, 'progress': entry.get('progress')})
            if len(logs) > 100:
                del logs[:-100]

def _send_webhook_notification(job_id: str):
    """
    Send webhook notification when job completes or fails
    Runs in background thread to not block processing
    """
    def send_webhook():
        try:
            job = job_manager.get_job(job_id)
            if not job or not job.get('callback_url'):
                return
            
            # Prepare webhook payload
            payload = {
                'job_id': job_id,
                'status': job['status'],
                'progress': job.get('progress', 0),
                'message': job.get('message'),
                'error': job.get('error'),
                'filename': job.get('original_filename'),
                'created_at': job.get('created_at'),
                'finished_at': job.get('finished_at'),
                'expires_at': job.get('expires_at')
            }
            
            # Add download URL if completed successfully
            if job['status'] == 'completed' and job.get('output_file'):
                # Construct full download URL
                base_url = request.url_root if request else 'http://localhost:5000/'
                payload['download_url'] = f"{base_url}api/v1/files/download/{job['output_file']}"
                payload['output_file'] = job['output_file']
            
            # Send POST request to callback URL
            response = requests.post(
                job['callback_url'],
                json=payload,
                timeout=10,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'AddressIQ-Webhook/1.0'
                }
            )
            response.raise_for_status()
            
            print(f"✅ Webhook sent successfully for job {job_id} to {job['callback_url']}")
            
        except requests.exceptions.Timeout:
            print(f"⚠️ Webhook timeout for job {job_id}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Webhook failed for job {job_id}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error sending webhook for job {job_id}: {e}")
    
    # Run webhook in background thread
    thread = threading.Thread(target=send_webhook, daemon=True)
    thread.start()

@app.route('/api/processing-status/<processing_id>/logs', methods=['GET'])
def get_processing_logs(processing_id):
    entry = processing_status.get(processing_id)
    if not entry:
        return jsonify({'error': 'Processing ID not found'}), 404
    return jsonify({'logs': entry.get('logs', [])}), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint for frontend connectivity tests"""
    return jsonify({
        'status': 'ok',
        'message': 'Backend running',
        'endpoints': [
            '/api/upload-excel',
            '/api/processing-status/<id>',
            '/api/download/<filename>',
            '/api/uploaded-files',
            '/api/process-address',
            '/api/process-addresses',
            '/api/public/standardize',
            '/api/coordinates',
            '/api/countries',
            '/api/models'
        ]
    }), 200

# AI Model Management
def _load_ai_models():
    """Load AI models configuration from JSON file"""
    try:
        config_path = Path(__file__).parent / 'config' / 'ai_models.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"⚠️ Failed to load AI models configuration: {e}")
        # Return default configuration
        return {
            'models': [
                {
                    'id': 'gpt4omni',
                    'name': 'GPT-4 Omni',
                    'displayName': 'GPT-4 Omni',
                    'provider': 'azure_openai',
                    'description': 'Advanced AI model for address standardization',
                    'enabled': True
                }
            ],
            'default_model': 'gpt4omni'
        }

def _validate_model(model_id: str) -> dict:
    """
    Validate if the provided model ID is valid and enabled.
    Returns dict with 'valid' (bool), 'error' (str), and 'model_config' (dict) keys.
    """
    if not model_id:
        return {'valid': False, 'error': 'Model ID is required', 'model_config': None}
    
    config = _load_ai_models()
    models = config.get('models', [])
    
    # Find the model by ID
    model_config = None
    for model in models:
        if model.get('id') == model_id:
            model_config = model
            break
    
    if not model_config:
        return {'valid': False, 'error': f'Invalid model ID: {model_id}', 'model_config': None}
    
    if not model_config.get('enabled', False):
        return {'valid': False, 'error': f'Model is disabled: {model_id}', 'model_config': None}
    
    return {'valid': True, 'error': None, 'model_config': model_config}

@app.route('/api/models', methods=['GET'])
def get_ai_models():
    """Get list of available AI models (only returns display names and IDs, not internal config)"""
    try:
        config = _load_ai_models()
        models = config.get('models', [])
        
        # Filter enabled models and return only safe fields
        available_models = []
        for model in models:
            if model.get('enabled', False):
                available_models.append({
                    'id': model.get('id'),
                    'displayName': model.get('displayName'),
                    'description': model.get('description', '')
                })
        
        return jsonify({
            'models': available_models,
            'default_model': config.get('default_model', 'gpt4omni')
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch models: {str(e)}'}), 500

# Basic request logging to help debug proxy path issues
@app.before_request
def log_request():
    try:
        print(f"[REQ] {request.method} {request.path}")
    except Exception:
        pass

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _safe_ident(name: str) -> str:
    """Very conservative identifier quoting for SQL Server names (table/column).
    Allows only letters, numbers, underscore, and dot for schema qualification.
    Wraps parts in square brackets. Falls back to simple stripping if invalid.
    """
    if not isinstance(name, str):
        return ''
    parts = [p for p in name.split('.') if p]
    safe_parts = []
    for p in parts:
        if re.match(r'^[A-Za-z0-9_]+$', p):
            safe_parts.append(f'[{p}]')
        else:
            # Remove unsafe chars
            cleaned = re.sub(r'[^A-Za-z0-9_]', '', p)
            safe_parts.append(f'[{cleaned}]')
    return '.'.join(safe_parts) if safe_parts else ''

def _df_to_inbound_csv(df: pd.DataFrame, base_filename: str) -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe = re.sub(r'[^A-Za-z0-9_.-]', '_', base_filename or 'db_extract')
    filename = f"{safe}_{ts}.csv"
    file_path = INBOUND_FOLDER / filename
    # normalize columns to strings
    df.columns = [str(c) for c in df.columns]
    # Use UTF-8-BOM to ensure proper Unicode handling for special characters
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    return filename

# --- Connection string utilities -------------------------------------------------
def _parse_kv_conn_str(conn_str: str) -> dict:
    """Parse a semicolon-separated key=value string into a dict (preserves last occurrence).
    Ignores empty segments and segments without '='. Trims whitespace around keys/values.
    """
    result = {}
    if not isinstance(conn_str, str):
        return result
    for seg in conn_str.split(';'):
        if not seg or '=' not in seg:
            continue
        k, v = seg.split('=', 1)
        k = (k or '').strip()
        v = (v or '').strip()
        if k:
            result[k] = v
    return result

def _first_present(d: dict, names: list) -> str:
    """Return the first value found in dict for any of the provided names (case-insensitive)."""
    lower_map = {k.lower(): v for k, v in d.items()}
    for n in names:
        v = lower_map.get(n.lower())
        if isinstance(v, str) and v.strip() != '':
            return v.strip()
    return ''

def _mask(s: str, keep: int = 1) -> str:
    if not s:
        return ''
    if len(s) <= keep:
        return '*' * len(s)
    return s[:keep] + '*' * (len(s) - keep)

def _build_sqlserver_odbc_conn_str(raw: str) -> tuple[str, dict, list]:
    """Build a canonical SQL Server ODBC connection string and report diagnostics.
    Returns (conn_str, attrs_dict, warnings).
    """
    attrs = _parse_kv_conn_str(raw)
    warnings = []
    server = _first_present(attrs, ['SERVER', 'Server', 'Data Source', 'Address', 'Addr', 'Network Address'])
    database = _first_present(attrs, ['DATABASE', 'Database', 'Initial Catalog'])
    uid = _first_present(attrs, ['UID', 'User ID', 'User Id', 'User', 'Username', 'UserName'])
    pwd = _first_present(attrs, ['PWD', 'Password', 'Pwd'])
    driver = _first_present(attrs, ['DRIVER', 'Driver']) or '{ODBC Driver 17 for SQL Server}'
    encrypt = _first_present(attrs, ['Encrypt']) or 'yes'
    tsc = _first_present(attrs, ['TrustServerCertificate']) or 'no'
    auth = _first_present(attrs, ['Authentication'])
    timeout = _first_present(attrs, ['Connection Timeout', 'Timeout'])

    canon = {
        'DRIVER': driver,
        'SERVER': server,
        'DATABASE': database,
        'UID': uid,
        'PWD': pwd,
        'Encrypt': encrypt,
        'TrustServerCertificate': tsc,
    }
    if auth:
        canon['Authentication'] = auth
    if timeout:
        canon['Connection Timeout'] = timeout

    missing = [k for k in ['SERVER', 'DATABASE', 'UID', 'PWD'] if not canon.get(k)]
    if missing:
        warnings.append(f"Missing required attributes: {', '.join(missing)}")

    # Recompose connection string
    parts = []
    for k in ['DRIVER', 'SERVER', 'DATABASE', 'UID', 'PWD', 'Encrypt', 'TrustServerCertificate', 'Authentication', 'Connection Timeout']:
        if k in canon and canon[k] != '':
            parts.append(f"{k}={canon[k]}")
    conn_out = ';'.join(parts)
    return conn_out, canon, warnings

def _execute_database_query_sync(connection_string: str, source_type: str, data: dict, limit: int) -> dict:
    """Execute database query synchronously and return results directly"""
    try:
        import pyodbc
        import pandas as pd
        import numpy as np
        
        # Normalize/validate connection string
        final_conn_str, canon, warns = _build_sqlserver_odbc_conn_str(connection_string)
        
        if warns and any(w.startswith('Missing required attributes') for w in warns):
            return {
                'success': False,
                'error': f'Invalid connection string: {"; ".join(warns)}',
                'data': [],
                'row_count': 0,
                'columns': [],
                'warnings': warns
            }
        
        # Connect to database and execute query
        with pyodbc.connect(final_conn_str) as conn:
            df = None
            executed_query = ""
            
            if source_type == 'table':
                # Build query from table and columns
                table_name = data.get('tableName', '').strip()
                column_names = data.get('columnNames', [])
                unique_id = data.get('uniqueId', '').strip()
                
                # Prepare columns list
                cols = []
                if unique_id:
                    cols.append(unique_id)
                for c in column_names:
                    if not c:
                        continue
                    c_clean = str(c).strip()
                    if unique_id and c_clean.lower() == unique_id.lower():
                        continue
                    cols.append(c_clean)
                
                # Build SQL query
                safe_cols = ', '.join([_safe_ident(c) for c in cols]) if cols else '*'
                safe_table = _safe_ident(table_name)
                top_clause = f"TOP {limit} " if limit else ''
                executed_query = f"SELECT {top_clause}{safe_cols} FROM {safe_table}"
                
                df = pd.read_sql_query(executed_query, conn)
                
            else:  # source_type == 'query'
                # Execute provided SQL query
                query_text = data.get('query', '')
                executed_query = query_text
                raw = pd.read_sql_query(query_text, conn)
                df = raw.head(limit) if limit and limit > 0 else raw
        
        if df is None or df.empty:
            return {
                'success': True,
                'message': 'Query executed successfully but returned no data',
                'data': [],
                'row_count': 0,
                'columns': [],
                'query_executed': executed_query
            }
        
        # Convert DataFrame to JSON-serializable format
        data_records = df.to_dict('records')
        
        # Clean up NaN values and convert to JSON-serializable types
        for record in data_records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    record[key] = value.isoformat()
                elif isinstance(value, (np.integer, np.int64)):
                    record[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[key] = float(value)
        
        return {
            'success': True,
            'message': f'Query executed successfully. Retrieved {len(data_records)} records.',
            'data': data_records,
            'row_count': len(data_records),
            'columns': list(df.columns),
            'query_executed': executed_query,
            'warnings': warns if warns else []
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Database query failed: {str(e)}',
            'data': [],
            'row_count': 0,
            'columns': [],
            'query_executed': executed_query if 'executed_query' in locals() else 'N/A'
        }

def process_db_task(processing_id: str, payload: dict):
    """Background task: fetch from DB (table/query), save to inbound, process to outbound."""
    try:
        conn_str = payload.get('connectionString') or ''
        source_type = payload.get('sourceType')
        unique_id = (payload.get('uniqueId') or '').strip()
        # Normalize column names: support comma-separated entries
        column_names = []
        for entry in (payload.get('columnNames') or []):
            for part in str(entry).split(','):
                name = part.strip()
                if name:
                    column_names.append(name)
        table_name = (payload.get('tableName') or '').strip()
        query_text = payload.get('query') or ''
        limit = int(payload.get('limit') or 10)

        # Normalize/validate connection string
        final_conn_str, canon, warns = _build_sqlserver_odbc_conn_str(conn_str)
        masked_uid = _mask(canon.get('UID', ''), 2)
        _update_status(
            processing_id,
            status='processing',
            message='Connecting to database…',
            progress=20,
            log=f"DB connect using DRIVER={canon.get('DRIVER')}, SERVER={canon.get('SERVER')}, DATABASE={canon.get('DATABASE')}, UID={masked_uid}"
        )
        if warns:
            _update_status(processing_id, log=f"ConnString warnings: {' | '.join(warns)}")
            # If required attrs are missing, fail early with clear error
            if any(w.startswith('Missing required attributes') for w in warns):
                _update_status(processing_id, status='error', message='Invalid connection string', progress=100, error='; '.join(warns))
                return

        with pyodbc.connect(final_conn_str) as conn:
            _update_status(processing_id, message='Fetching data from database…', progress=30, log=f'Source: {source_type}')
            df = None
            if source_type == 'table':
                cols = []
                if unique_id:
                    cols.append(unique_id)
                for c in column_names:
                    if not c:
                        continue
                    if unique_id and c.strip().lower() == unique_id.strip().lower():
                        continue
                    cols.append(c)
                # quote identifiers
                safe_cols = ', '.join([_safe_ident(c) for c in cols]) if cols else '*'
                safe_table = _safe_ident(table_name)
                top_clause = f"TOP {limit} " if limit else ''
                sql = f"SELECT {top_clause}{safe_cols} FROM {safe_table}"
                _update_status(processing_id, log=f'Executing: {sql}')
                df = pd.read_sql_query(sql, conn)
            else:
                # arbitrary SQL; use pandas to run, then trim to limit
                _update_status(processing_id, log='Executing provided SQL query')
                raw = pd.read_sql_query(query_text, conn)
                df = raw.head(limit) if limit and limit > 0 else raw

        if df is None or df.empty:
            _update_status(processing_id, status='error', message='No data returned from database', progress=100, error='Empty dataset', log='Query returned zero rows')
            return

        _update_status(processing_id, message='Writing inbound CSV…', progress=50, log=f'Rows fetched: {len(df)}')
        inbound_filename = _df_to_inbound_csv(df, 'db_extract')
        _update_status(processing_id, filename=inbound_filename)

        _update_status(processing_id, message='Processing inbound CSV…', progress=70, log='Invoking CSVAddressProcessor')
        processor = CSVAddressProcessor(base_directory=str(BASE_DIR))
        output_path = processor.process_csv_file(str(INBOUND_FOLDER / inbound_filename))

        if output_path and os.path.exists(output_path):
            _update_status(processing_id, status='completed', message='Database data processed successfully', progress=100, output_file=os.path.basename(output_path), output_path=output_path, finished_at=datetime.utcnow().isoformat() + 'Z', log=f'Output: {os.path.basename(output_path)}')
        else:
            _update_status(processing_id, status='error', message='Processing completed but no output file found', progress=100, error='No outbound output', log='Missing output file')
    except Exception as e:
        _update_status(processing_id, status='error', message='DB processing failed', progress=100, error=str(e), log=f'Exception: {e}')

# Inbound preview removed per requirement change

@app.route('/api/db/connect', methods=['POST'])
def db_connect_and_process():
    """Start a DB fetch+process job based on payload from UI (table or query)."""
    try:
        data = request.get_json() or {}
        mode = data.get('mode')  # 'format' | 'compare' (compare disabled on UI)
        source_type = data.get('sourceType')  # 'table' | 'query'
        connection_string = data.get('connectionString')
        if not connection_string or not source_type:
            return jsonify({'error': 'connectionString and sourceType are required'}), 400

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        processing_id = f"db_{timestamp}_{uuid.uuid4().hex[:6]}"
        processing_status[processing_id] = {
            'status': 'queued',
            'message': 'Request accepted',
            'filename': None,
            'progress': 10,
            'output_file': None,
            'error': None,
            'started_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'finished_at': None,
            'logs': [{'ts': datetime.utcnow().isoformat() + 'Z', 'message': 'DB task queued', 'progress': 10}],
            'steps': [
                {'name': 'queued', 'label': 'Queued', 'target': 10},
                {'name': 'connect', 'label': 'Connect DB', 'target': 20},
                {'name': 'fetch', 'label': 'Fetch', 'target': 40},
                {'name': 'write', 'label': 'Write inbound', 'target': 50},
                {'name': 'standardize', 'label': 'Process', 'target': 80},
                {'name': 'complete', 'label': 'Complete', 'target': 100},
            ]
        }

        # enrich payload with default limit
        data['limit'] = int(data.get('limit') or 10)

        thread = threading.Thread(target=process_db_task, args=(processing_id, data))
        thread.daemon = True
        thread.start()

        return jsonify({'message': 'DB task started', 'processing_id': processing_id}), 200
    except Exception as e:
        return jsonify({'error': f'DB connect failed: {str(e)}'}), 500

@app.route('/upload-excel', methods=['POST'])
def upload_excel_redirect():
    """Redirect requests without /api prefix to the proper endpoint"""
    return jsonify({
        'error': 'Please use /api/upload-excel endpoint instead of /upload-excel',
        'debug_info': 'The proxy configuration may not be working correctly'
    }), 404

def process_file_background(processing_id, filename, model_id=None):
    """Process the uploaded file in-process using CSVAddressProcessor for better progress feedback."""
    try:
        inbound_file = INBOUND_FOLDER / filename
        if not inbound_file.exists():
            _update_status(processing_id, status='error', message='Uploaded file not found on server', progress=100, error='Missing inbound file', log='Inbound file missing')
            return

        _update_status(processing_id, status='processing', message='Initializing processor...', progress=20, log='Processor initialization')

        processor = CSVAddressProcessor(base_directory=str(BASE_DIR), model=model_id)
        _update_status(processing_id, message='Reading input file...', progress=35, log='Reading input file')
        time.sleep(0.15)

        _update_status(processing_id, message='Standardizing addresses...', progress=55, log='Starting standardization')
        output_path = processor.process_csv_file(str(inbound_file))

        _update_status(processing_id, message='Finalizing output...', progress=85, log='Finalizing output file')
        time.sleep(0.1)

        if output_path and os.path.exists(output_path):
            _update_status(processing_id, status='completed', message='File processed successfully', progress=100, output_file=os.path.basename(output_path), output_path=output_path, finished_at=datetime.utcnow().isoformat() + 'Z', log='Processing completed')
        else:
            _update_status(processing_id, status='error', message='Output file not generated', progress=100, error='Processor did not return output path', log='No output file located')
    except Exception as e:
        _update_status(processing_id, status='error', message='Processing failed with error', progress=100, error=str(e), log=f'Exception: {e}')

def process_compare_background(processing_id, filename, model_id=None):
    """Run batch compare across inbound via subprocess and detect produced outbound file."""
    try:
        inbound_file = INBOUND_FOLDER / filename
        if not inbound_file.exists():
            _update_status(processing_id, status='error', message='Uploaded file not found on server', progress=100, error='Missing inbound file', log='Inbound file missing')
            return

        # Snapshot outbound directory before run
        before = {f.name: (OUTBOUND_FOLDER / f.name).stat().st_mtime for f in OUTBOUND_FOLDER.glob('*') if f.is_file()}
        start_ts = time.time()

        _update_status(processing_id, status='processing', message='Running batch comparison...', progress=35, log='Starting batch-compare subprocess')

        script_path = BASE_DIR / 'csv_address_processor.py'
        # Target only the uploaded file to avoid interference from other inbound files
        cmd = [
            sys.executable,
            str(script_path),
            str(inbound_file),  # positional input_file per argparse spec
            '--compare-csv',
            '--batch-size', '5'
        ]
        
        # Add model parameter if provided
        if model_id:
            cmd.extend(['--model', model_id])
        
        try:
            recent_lines = []
            child_env = os.environ.copy()
            child_env['PYTHONIOENCODING'] = 'utf-8'
            with subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=child_env
            ) as proc:
                for line in proc.stdout:  # stream logs
                    line_stripped = line.strip()
                    _update_status(processing_id, log=line_stripped)
                    recent_lines.append(line_stripped)
                    if len(recent_lines) > 40:
                        recent_lines.pop(0)
                ret = proc.wait()
                if ret != 0:
                    tail = '\n'.join(recent_lines[-10:])
                    _update_status(processing_id, status='error', message='Batch comparison failed', progress=100, error=f'return code {ret}: {tail}', log=f'Batch-compare exited {ret}')
                    return
        except Exception as se:
            _update_status(processing_id, status='error', message='Failed to start batch comparison', progress=100, error=str(se), log=f'Subprocess error: {se}')
            return

        _update_status(processing_id, message='Locating comparison result...', progress=75, log='Scanning outbound directory for new files')

        # Find new/updated files after start_ts
        candidates = []
        for p in OUTBOUND_FOLDER.glob('*.csv'):
            try:
                mtime = p.stat().st_mtime
                if mtime >= start_ts and (p.name not in before or mtime > before.get(p.name, 0)):
                    candidates.append((mtime, p))
            except Exception:
                continue

        if not candidates:
            _update_status(processing_id, status='error', message='Comparison output not found', progress=100, error='No new file in outbound', log='No outbound file detected')
            return

        candidates.sort(key=lambda x: x[0], reverse=True)
        newest = candidates[0][1]

        _update_status(processing_id, status='completed', message='Comparison completed', progress=100,
                       output_file=newest.name, output_path=str(newest), finished_at=datetime.utcnow().isoformat() + 'Z',
                       log=f'Found output: {newest.name}')
    except Exception as e:
        _update_status(processing_id, status='error', message='Batch comparison failed with error', progress=100, error=str(e), log=f'Exception: {e}')

@app.route('/api/processing-status/<processing_id>', methods=['GET'])
def get_processing_status(processing_id):
    """Get the status of file processing - now with database persistence"""
    try:
        # Try database first
        job = job_manager.get_job(processing_id)
        if job:
            return jsonify(job), 200
        
        # LEGACY: Fallback to in-memory dict for backwards compatibility
        if processing_id in processing_status:
            return jsonify(processing_status[processing_id]), 200
        
        return jsonify({'error': 'Processing ID not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_result_file(filename):
    """Preview a processed outbound file (CSV/Excel) with basic pagination."""
    try:
        page = int(request.args.get('page') or 1)
        page_size = int(request.args.get('page_size') or 50)
        page = page if page > 0 else 1
        page_size = page_size if page_size > 0 else 50

        file_path = OUTBOUND_FOLDER / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        ext = str(file_path.suffix).lower()
        columns = []
        rows = []

        if ext == '.csv':
            # Read header first to get columns (fast)
            try:
                header_df = pd.read_csv(file_path, nrows=0, encoding='utf-8')
                columns = [str(c) for c in list(header_df.columns)]
            except Exception:
                try:
                    header_df = pd.read_csv(file_path, nrows=0, encoding='latin1')
                    columns = [str(c) for c in list(header_df.columns)]
                except Exception:
                    columns = []

            # Use chunks to page through without loading entire file
            chunk_size = page_size
            target_index = page - 1
            chunk_iter = None
            try:
                chunk_iter = pd.read_csv(file_path, chunksize=chunk_size, encoding='utf-8', on_bad_lines='skip')
            except Exception:
                chunk_iter = pd.read_csv(file_path, chunksize=chunk_size, encoding='latin1', on_bad_lines='skip')

            current = 0
            selected = None
            for chunk in chunk_iter:
                if current == target_index:
                    selected = chunk
                    break
                current += 1

            if selected is not None:
                selected.columns = [str(c) for c in selected.columns]
                if not columns:
                    columns = [str(c) for c in list(selected.columns)]
                rows = selected.fillna('').to_dict(orient='records')

        elif ext in ('.xlsx', '.xls'):
            # Excel: read header to get columns then read page using skiprows/nrows
            try:
                header_df = pd.read_excel(file_path, nrows=0)
                columns = [str(c) for c in list(header_df.columns)]
            except Exception:
                columns = []

            skiprows = range(1, (page - 1) * page_size + 1) if page > 1 else None
            try:
                df = pd.read_excel(file_path, skiprows=skiprows, nrows=page_size)
                df.columns = [str(c) for c in df.columns]
                if not columns:
                    columns = [str(c) for c in list(df.columns)]
                rows = df.fillna('').to_dict(orient='records')
            except Exception:
                rows = []
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        return jsonify({'columns': columns, 'rows': rows}), 200
    except Exception as e:
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_processed_file(filename):
    """Download processed file from outbound directory"""
    try:
        # Serve only outbound processed files
        file_path = OUTBOUND_FOLDER / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_output_file(filename):
    """Return a small JSON preview of an outbound file (CSV or Excel).
    Query params:
      - limit: DEPRECATED alias of page_size
      - page: 1-based page index (default 1)
      - page_size: number of rows per page (default 100, max 500)
    """
    try:
        file_path = OUTBOUND_FOLDER / filename
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': 'File not found'}), 404

        # Parse pagination params
        try:
            page = int(request.args.get('page', '1'))
        except Exception:
            page = 1
        try:
            page_size = int(request.args.get('page_size', request.args.get('limit', '100')))
        except Exception:
            page_size = 100
        page = max(1, page)
        page_size = max(1, min(page_size, 500))
        start = (page - 1) * page_size

        ext = file_path.suffix.lower()
        df = None
        total_rows = 0
        if ext in ['.csv', '.txt']:
            # Count rows in binary mode (encoding agnostic)
            try:
                with open(file_path, 'rb') as fb:
                    total_rows = sum(1 for _ in fb) - 1  # minus header
                    if total_rows < 0:
                        total_rows = 0
            except Exception:
                total_rows = 0

            # Read page using UTF-8 with replacement to avoid decode errors for preview
            skip = range(1, 1 + start) if start > 0 else None
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                df = pd.read_csv(
                    f,
                    sep=None,
                    engine='python',
                    skiprows=skip,
                    nrows=page_size,
                    on_bad_lines='skip',
                    dtype=str
                )
        elif ext in ['.xlsx', '.xls']:
            # Total rows: approximate by reading first column fully
            try:
                total_rows = int(pd.read_excel(str(file_path), usecols=[0]).shape[0])
            except Exception:
                total_rows = 0
            skip = range(1, 1 + start) if start > 0 else None
            df = pd.read_excel(str(file_path), nrows=page_size, skiprows=skip)
        else:
            return jsonify({'error': f'Unsupported file type: {ext}'}), 400

        # Normalize columns to strings and replace NaN with None
        df.columns = [str(c) for c in df.columns]
        records = json.loads(df.where(pd.notnull(df), None).to_json(orient='records'))
        if total_rows == 0:
            # Fallback if we couldn't compute total rows; approximate with page info
            total_rows = start + len(records)

        return jsonify({
            'filename': filename,
            'columns': df.columns.tolist(),
            'rowCount': len(records),
            'rows': records,
            'page': page,
            'pageSize': page_size,
            'totalRows': int(total_rows)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    """Handle Excel/CSV file upload and trigger batch processing"""
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files.'}), 400
        
        # Get and validate model parameter
        model_id = request.form.get('model')
        if not model_id:
            # Use default model if not provided
            config = _load_ai_models()
            model_id = config.get('default_model', 'gpt4omni')
        
        # Validate model
        model_validation = _validate_model(model_id)
        if not model_validation['valid']:
            return jsonify({'error': model_validation['error']}), 400
        
        model_config = model_validation['model_config']
        
        # Generate secure filename with timestamp
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
    # Save file to inbound directory (requirement: use application inbound folder, not C:\ uploads)
        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Validate file content by trying to read it
        try:
            if ext.lower() in ['.csv', '.txt']:
                # Use robust encoding detection to handle non-UTF-8 CSVs
                df = read_csv_with_encoding_detection(file_path)
            else:
                df = pd.read_excel(file_path)

            # Check if file is empty (no data rows)
            if df.shape[0] == 0:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({'error': 'The uploaded file contains no data rows. Please upload a file with at least one record.'}), 400
            
            # Check if file has no columns
            if df.shape[1] == 0:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({'error': 'The uploaded file contains no columns. Please upload a valid file with data.'}), 400

            # Validate required headers
            validation_result = _validate_file_upload_headers(df)
            if not validation_result['valid']:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({
                    'error': validation_result['error'],
                    'missing_headers': validation_result.get('missing_headers', []),
                    'actual_headers': validation_result.get('actual_headers', [])
                }), 400

            file_info = {
                'rows': int(df.shape[0]),
                'columns': int(df.shape[1]),
                'column_names': df.columns.tolist() if hasattr(df, 'columns') else []
            }

        except Exception as e:
            # If file is invalid, remove it and return error
            try:
                os.remove(file_path)
            except Exception:
                pass
            error_msg = str(e)
            # Provide more specific error messages for common issues
            if 'Error tokenizing data' in error_msg or 'ParserError' in error_msg:
                return jsonify({'error': f'Failed to parse the file. Please ensure it is a valid Excel or CSV file. Error: {error_msg}'}), 400
            elif 'XLRDError' in error_msg or 'BadZipFile' in error_msg:
                return jsonify({'error': f'The Excel file appears to be corrupted or in an unsupported format. Please try re-saving the file and uploading again. Error: {error_msg}'}), 400
            else:
                return jsonify({'error': f'Invalid file format or corrupted file: {error_msg}'}), 400
        
        # Generate processing ID for tracking
        processing_id = f"proc_{timestamp}_{hash(unique_filename) % 10000}"
        
        # Create job in database
        job_manager.create_job(
            job_id=processing_id,
            filename=unique_filename,
            original_filename=filename,
            component='upload',
            file_size=os.path.getsize(file_path),
            file_rows=file_info['rows'],
            file_columns=file_info['columns'],
            file_info=file_info,
            progress=10,
            message='File uploaded successfully',
            user_ip=request.remote_addr,
            steps=[
                {'name': 'upload', 'label': 'Upload', 'target': 10},
                {'name': 'initialize', 'label': 'Initialize', 'target': 20},
                {'name': 'read', 'label': 'Read File', 'target': 35},
                {'name': 'standardize', 'label': 'Standardize', 'target': 55},
                {'name': 'finalize', 'label': 'Finalize', 'target': 85},
                {'name': 'complete', 'label': 'Complete', 'target': 100}
            ],
            logs=[{'ts': datetime.utcnow().isoformat() + 'Z', 'message': 'Upload received', 'progress': 10}]
        )
        
        # LEGACY: Also initialize in-memory status for backwards compatibility
        processing_status[processing_id] = {
            'status': 'uploaded',
            'message': 'File uploaded successfully',
            'filename': unique_filename,
            'original_filename': filename,
            'progress': 10,
            'output_file': None,
            'error': None,
            'file_info': file_info,
            'started_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'finished_at': None,
            'logs': [{'ts': datetime.utcnow().isoformat() + 'Z', 'message': 'Upload received', 'progress': 10}],
            'steps': [
                {'name': 'upload', 'label': 'Upload', 'target': 10},
                {'name': 'initialize', 'label': 'Initialize', 'target': 20},
                {'name': 'read', 'label': 'Read File', 'target': 35},
                {'name': 'standardize', 'label': 'Standardize', 'target': 55},
                {'name': 'finalize', 'label': 'Finalize', 'target': 85},
                {'name': 'complete', 'label': 'Complete', 'target': 100}
            ]
        }
        
        # Start batch processing in background thread
        thread = threading.Thread(
            target=process_file_background,
            args=(processing_id, unique_filename, model_id)
        )
        thread.daemon = True
        thread.start()
        
        # Return success response with processing ID
        return jsonify({
            'message': f'File uploaded successfully! Processing started.',
            'processing_id': processing_id,
            'filename': unique_filename,
            'file_info': file_info,
            'model': model_config.get('displayName')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/upload-compare', methods=['POST'])
def upload_compare():
    """Handle file upload and trigger batch comparison over inbound directory."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files.'}), 400

        # Get and validate model parameter
        model_id = request.form.get('model')
        if not model_id:
            # Use default model if not provided
            config = _load_ai_models()
            model_id = config.get('default_model', 'gpt4omni')
        
        # Validate model
        model_validation = _validate_model(model_id)
        if not model_validation['valid']:
            return jsonify({'error': model_validation['error']}), 400
        
        model_config = model_validation['model_config']

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"

        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)

        # Validate quick read with robust CSV encoding handling
        file_info = None
        try:
            if ext.lower() in ['.csv', '.txt']:
                df = read_csv_with_encoding_detection(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Check if file is empty (no data rows)
            if df.shape[0] == 0:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({'error': 'The uploaded file contains no data rows. Please upload a file with at least one record.'}), 400
            
            # Check if file has no columns
            if df.shape[1] == 0:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({'error': 'The uploaded file contains no columns. Please upload a valid file with data.'}), 400
            
            # Validate required headers
            validation_result = _validate_compare_upload_headers(df)
            if not validation_result['valid']:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({
                    'error': validation_result['error'],
                    'missing_headers': validation_result.get('missing_headers', []),
                    'actual_headers': validation_result.get('actual_headers', [])
                }), 400
            
            file_info = {
                'rows': int(df.shape[0]),
                'columns': int(df.shape[1]),
                'column_names': df.columns.tolist() if hasattr(df, 'columns') else []
            }
        except Exception as ve:
            try:
                os.remove(file_path)
            except Exception:
                pass
            error_msg = str(ve)
            # Provide more specific error messages for common issues
            if 'Error tokenizing data' in error_msg or 'ParserError' in error_msg:
                return jsonify({'error': f'Failed to parse the file. Please ensure it is a valid Excel or CSV file. Error: {error_msg}'}), 400
            elif 'XLRDError' in error_msg or 'BadZipFile' in error_msg:
                return jsonify({'error': f'The Excel file appears to be corrupted or in an unsupported format. Please try re-saving the file and uploading again. Error: {error_msg}'}), 400
            else:
                return jsonify({'error': f'Invalid file: {error_msg}'}), 400

        processing_id = f"cmp_{timestamp}_{hash(unique_filename) % 10000}"
        processing_status[processing_id] = {
            'status': 'uploaded',
            'message': 'File uploaded for comparison',
            'filename': unique_filename,
            'original_filename': filename,
            'progress': 15,
            'output_file': None,
            'error': None,
            'file_info': file_info,
            'started_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'finished_at': None,
            'logs': [{'ts': datetime.utcnow().isoformat() + 'Z', 'message': 'Upload received', 'progress': 15}],
            'steps': [
                {'name': 'upload', 'label': 'Upload', 'target': 15},
                {'name': 'compare', 'label': 'Batch Compare', 'target': 75},
                {'name': 'finalize', 'label': 'Finalize', 'target': 90},
                {'name': 'complete', 'label': 'Complete', 'target': 100}
            ]
        }

        thread = threading.Thread(target=process_compare_background, args=(processing_id, unique_filename, model_id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'message': 'Comparison started',
            'processing_id': processing_id,
            'filename': unique_filename,
            'file_info': file_info,
            'model': model_config.get('displayName')
        }), 200
    except Exception as e:
        return jsonify({'error': f'Upload compare failed: {str(e)}'}), 500

@app.route('/api/process-address', methods=['POST'])
def process_address():
    """Process a single address for standardization"""
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        # Get and validate model parameter
        model_id = data.get('model')
        if not model_id:
            # Use default model if not provided
            config = _load_ai_models()
            model_id = config.get('default_model', 'gpt4omni')
        
        # Validate model
        model_validation = _validate_model(model_id)
        if not model_validation['valid']:
            return jsonify({'error': model_validation['error']}), 400
        
        # Import the CSV processor to use its address standardization
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from csv_address_processor import CSVAddressProcessor
        
        processor = CSVAddressProcessor(model=model_id)
        result = processor.standardize_single_address(address, 0)  # row_index 0 for single address
        
        # Check if Azure OpenAI processing was successful
        if result.get('status') == 'success' and result.get('formatted_address'):
            return jsonify({
                'processedAddress': result.get('formatted_address', address),
                'confidence': result.get('confidence', 'unknown'),
                'components': {
                    'street_number': result.get('street_number', ''),
                    'street_name': result.get('street_name', ''),
                    'city': result.get('city', ''),
                    'state': result.get('state', ''),
                    'postal_code': result.get('postal_code', ''),
                    'country': result.get('country', ''),
                    'latitude': result.get('latitude', ''),
                    'longitude': result.get('longitude', '')
                },
                'status': 'success',
                'source': 'azure_openai'
            }), 200
        else:
            # If Azure OpenAI fails, try to use free APIs for basic processing
            processor.configure_free_apis(nominatim=True, geocodify=True)
            
            # Try free APIs for basic geocoding
            basic_result = {'success': False}
            try:
                basic_result = processor.geocode_with_nominatim(address)
            except:
                try:
                    basic_result = processor.geocode_with_geocodify(address)
                except:
                    pass
            
            if basic_result.get('success'):
                return jsonify({
                    'processedAddress': basic_result.get('formatted_address', address),
                    'confidence': basic_result.get('confidence', 'medium'),
                    'components': {
                        'street_number': basic_result.get('street_number', ''),
                        'street_name': basic_result.get('street_name', ''),
                        'city': basic_result.get('city', ''),
                        'state': basic_result.get('state', ''),
                        'postal_code': basic_result.get('postal_code', ''),
                        'country': basic_result.get('country', ''),
                        'latitude': basic_result.get('latitude', ''),
                        'longitude': basic_result.get('longitude', '')
                    },
                    'status': 'success',
                    'source': 'free_api'
                }), 200
            else:
                # Return original address with a note about Azure OpenAI being unavailable
                return jsonify({
                    'processedAddress': address,
                    'confidence': 'unavailable',
                    'components': {},
                    'status': 'fallback',
                    'source': 'original',
                    'note': 'Azure OpenAI credentials not configured. Please set up OAuth credentials for full address processing capabilities.'
                }), 200
            
    except Exception as e:
        return jsonify({'error': f'Address processing failed: {str(e)}'}), 500

@app.route('/api/process-addresses', methods=['POST'])
def process_addresses():
    """Process multiple addresses (newline list) returning array of results"""
    try:
        data = request.get_json() or {}
        addresses = data.get('addresses')
        if not addresses or not isinstance(addresses, list):
            return jsonify({'error': 'addresses (list) is required'}), 400

        # Get and validate model parameter
        model_id = data.get('model')
        if not model_id:
            # Use default model if not provided
            config = _load_ai_models()
            model_id = config.get('default_model', 'gpt4omni')
        
        # Validate model
        model_validation = _validate_model(model_id)
        if not model_validation['valid']:
            return jsonify({'error': model_validation['error']}), 400

        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from csv_address_processor import CSVAddressProcessor
        processor = CSVAddressProcessor(model=model_id)

        results = []
        for idx, raw in enumerate(addresses):
            addr = (raw or '').strip()
            if not addr:
                results.append({
                    'originalAddress': raw,
                    'processedAddress': '',
                    'status': 'skipped',
                    'confidence': 'n/a',
                    'source': 'none',
                    'components': {},
                    'error': 'Empty address line'
                })
                continue
            try:
                single = processor.standardize_single_address(addr, idx)
                if single and single.get('status') == 'success' and single.get('formatted_address'):
                    results.append({
                        'originalAddress': addr,
                        'processedAddress': single.get('formatted_address', addr),
                        'status': 'success',
                        'confidence': single.get('confidence', 'unknown'),
                        'source': 'azure_openai',
                        'components': {
                            'street_number': single.get('street_number', ''),
                            'street_name': single.get('street_name', ''),
                            'city': single.get('city', ''),
                            'state': single.get('state', ''),
                            'postal_code': single.get('postal_code', ''),
                            'country': single.get('country', ''),
                            'latitude': single.get('latitude', ''),
                            'longitude': single.get('longitude', '')
                        }
                    })
                else:
                    processor.configure_free_apis(nominatim=True, geocodify=True)
                    fallback = {'success': False}
                    try:
                        fallback = processor.geocode_with_nominatim(addr)
                    except Exception:
                        try:
                            fallback = processor.geocode_with_geocodify(addr)
                        except Exception:
                            pass
                    if fallback.get('success'):
                        results.append({
                            'originalAddress': addr,
                            'processedAddress': fallback.get('formatted_address', addr),
                            'status': 'success',
                            'confidence': fallback.get('confidence', 'medium'),
                            'source': 'free_api',
                            'components': {
                                'street_number': fallback.get('street_number', ''),
                                'street_name': fallback.get('street_name', ''),
                                'city': fallback.get('city', ''),
                                'state': fallback.get('state', ''),
                                'postal_code': fallback.get('postal_code', ''),
                                'country': fallback.get('country', ''),
                                'latitude': fallback.get('latitude', ''),
                                'longitude': fallback.get('longitude', '')
                            }
                        })
                    else:
                        results.append({
                            'originalAddress': addr,
                            'processedAddress': addr,
                            'status': 'fallback',
                            'confidence': 'unavailable',
                            'source': 'original',
                            'components': {},
                            'error': 'Processing unavailable'
                        })
            except Exception as inner_e:
                results.append({
                    'originalAddress': addr,
                    'processedAddress': addr,
                    'status': 'error',
                    'confidence': 'unknown',
                    'source': 'error',
                    'components': {},
                    'error': str(inner_e)
                })

        return jsonify({'results': results, 'count': len(results)}), 200
    except Exception as e:
        return jsonify({'error': f'Multi-address processing failed: {str(e)}'}), 500

@app.route('/api/public/standardize', methods=['POST', 'GET'])
def public_standardize():
    """Public API: standardize one or more addresses.
    Security: optional API key via X-API-Key header or api_key query parameter.
    Input (POST JSON): {"address": ".."} or {"addresses": ["..",".."]}
    Input (GET): /api/public/standardize?address=..&address=..
    Response JSON: {request_id, count, results:[{original, formatted, components:{}, confidence, status, source, error}]}
    """
    ok, err = _check_api_key()
    if not ok:
        return jsonify({'error': err}), 401
    try:
        if request.method == 'GET':
            # multiple 'address' params allowed
            addrs = request.args.getlist('address') or []
        else:
            payload = request.get_json(silent=True) or {}
            if 'addresses' in payload and isinstance(payload['addresses'], list):
                addrs = payload['addresses']
            elif 'address' in payload:
                addrs = [payload['address']]
            else:
                return jsonify({'error': 'Provide "address" or "addresses" in body'}), 400
        if not addrs:
            return jsonify({'error': 'No addresses supplied'}), 400
        # Sanitize & de-duplicate while keeping order
        cleaned = []
        seen = set()
        for a in addrs:
            s = _sanitize_address(a)
            if not s:
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(s)
        if not cleaned:
            return jsonify({'error': 'All supplied addresses were empty after sanitization'}), 400

        processor = CSVAddressProcessor(base_directory=str(BASE_DIR))
        results = []
        for idx, addr in enumerate(cleaned):
            try:
                res = processor.standardize_single_address(addr, idx)
                if res and res.get('status') == 'success' and res.get('formatted_address'):
                    results.append(_format_public_result(addr, res, 'azure_openai'))
                else:
                    # fallback
                    processor.configure_free_apis(nominatim=True, geocodify=True)
                    fb = {'success': False}
                    try:
                        fb = processor.geocode_with_nominatim(addr)
                    except Exception:
                        try:
                            fb = processor.geocode_with_geocodify(addr)
                        except Exception:
                            pass
                    if fb.get('success'):
                        results.append(_format_public_result(addr, fb, 'free_api'))
                    else:
                        results.append({
                            'original': addr,
                            'formatted': addr,
                            'components': {},
                            'confidence': 'unavailable',
                            'status': 'fallback',
                            'source': 'original',
                            'error': 'Standardization unavailable'
                        })
            except Exception as inner:
                results.append({
                    'original': addr,
                    'formatted': addr,
                    'components': {},
                    'confidence': 'unknown',
                    'status': 'error',
                    'source': 'error',
                    'error': str(inner)
                })

        return jsonify({
            'request_id': str(uuid.uuid4()),
            'count': len(results),
            'results': results,
            'api_version': 'v1'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Public standardization failed: {str(e)}'}), 500

def _format_public_result(original_addr: str, data: dict, source: str):
    return {
        'original': original_addr,
        'formatted': data.get('formatted_address', original_addr),
        'components': {
            'street_number': data.get('street_number', ''),
            'street_name': data.get('street_name', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'postal_code': data.get('postal_code', ''),
            'country': data.get('country', ''),
            'latitude': data.get('latitude', ''),
            'longitude': data.get('longitude', '')
        },
        'confidence': data.get('confidence', 'unknown'),
        'status': data.get('status', 'success'),
        'source': source,
        'error': None
    }

@app.route('/api/uploaded-files', methods=['GET'])
def list_uploaded_files():
    """List all files in inbound and outbound directories"""
    try:
        files = []
        
        # Get inbound files
        if INBOUND_FOLDER.exists():
            for filename in os.listdir(INBOUND_FOLDER):
                file_path = INBOUND_FOLDER / filename
                if file_path.is_file():
                    stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'path': str(file_path),
                        'type': 'inbound'
                    })
        
        # Get outbound files
        if OUTBOUND_FOLDER.exists():
            for filename in os.listdir(OUTBOUND_FOLDER):
                file_path = OUTBOUND_FOLDER / filename
                if file_path.is_file():
                    stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'path': str(file_path),
                        'type': 'outbound'
                    })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({'files': files}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@app.route('/api/coordinates', methods=['GET'])
def get_coordinates():
    """Get coordinates for sites with valid latitude and longitude from Mast_Site table"""
    try:
        country = request.args.get('country')
        
        if not country:
            return jsonify({'error': 'Country parameter is required'}), 400
        
        # Database connection string for Azure SQL
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=dev-server-sqldb.database.windows.net;"
            "DATABASE=dev-aurora-sqldb;"
            "UID=aurora;"
            "PWD=rcqM4?nTZH+hpfX7;"
            "TrustServerCertificate=yes;"
        )
        
        # Connect to database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Query to fetch sites with valid coordinates for the selected country
        # Filter out records where Site_PK = 0 or coordinates are NULL/empty/zero
        # Note: Site_Latitude and Site_Longitude are VARCHAR, so we check for non-empty strings
        query = """
            SELECT 
                Site_PK,
                Site_Name,
                Site_Address_1,
                Site_Address_2,
                Site_Address_3,
                Site_Address_4,
                Site_City,
                Site_State,
                Site_PostCode,
                Site_Country,
                Site_Latitude,
                Site_Longitude
            FROM [dbo].[Mast_Site]
            WHERE Site_PK != 0
                AND Site_Country = ?
                AND Site_Latitude IS NOT NULL
                AND Site_Longitude IS NOT NULL
                AND LTRIM(RTRIM(CAST(Site_Latitude AS VARCHAR(50)))) != ''
                AND LTRIM(RTRIM(CAST(Site_Longitude AS VARCHAR(50)))) != ''
                AND LTRIM(RTRIM(CAST(Site_Latitude AS VARCHAR(50)))) != '0'
                AND LTRIM(RTRIM(CAST(Site_Longitude AS VARCHAR(50)))) != '0'
                AND LTRIM(RTRIM(CAST(Site_Latitude AS VARCHAR(50)))) != '0.000000'
                AND LTRIM(RTRIM(CAST(Site_Longitude AS VARCHAR(50)))) != '0.000000'
                AND TRY_CAST(Site_Latitude AS FLOAT) IS NOT NULL
                AND TRY_CAST(Site_Longitude AS FLOAT) IS NOT NULL
                AND TRY_CAST(Site_Latitude AS FLOAT) != 0
                AND TRY_CAST(Site_Longitude AS FLOAT) != 0
            ORDER BY Site_Name
        """
        
        cursor.execute(query, (country,))
        rows = cursor.fetchall()
        
        # Build full address and coordinates list
        coordinates = []
        for row in rows:
            # Construct full address from components
            address_parts = []
            if row.Site_Address_1:
                address_parts.append(row.Site_Address_1.strip())
            if row.Site_Address_2:
                address_parts.append(row.Site_Address_2.strip())
            if row.Site_Address_3:
                address_parts.append(row.Site_Address_3.strip())
            if row.Site_Address_4:
                address_parts.append(row.Site_Address_4.strip())
            if row.Site_City:
                address_parts.append(row.Site_City.strip())
            if row.Site_State:
                address_parts.append(row.Site_State.strip())
            if row.Site_PostCode:
                address_parts.append(row.Site_PostCode.strip())
            if row.Site_Country:
                address_parts.append(row.Site_Country.strip())
            
            full_address = ', '.join(address_parts)
            
            coordinates.append({
                'site_pk': row.Site_PK,
                'site_name': row.Site_Name or '',
                'full_address': full_address,
                'latitude': float(row.Site_Latitude),
                'longitude': float(row.Site_Longitude)
            })
        
        cursor.close()
        conn.close()
        
        print(f"[INFO] Fetched {len(coordinates)} locations for {country}")
        
        return jsonify({
            'country': country,
            'count': len(coordinates),
            'coordinates': coordinates
        }), 200
        
    except pyodbc.Error as db_error:
        print(f"[ERROR] Database error: {str(db_error)}")
        return jsonify({
            'error': f'Database error: {str(db_error)}',
            'type': 'database_error'
        }), 500
    except Exception as e:
        print(f"[ERROR] Coordinate lookup failed: {str(e)}")
        return jsonify({
            'error': f'Coordinate lookup failed: {str(e)}',
            'type': 'general_error'
        }), 500

@app.route('/api/countries', methods=['GET'])
def get_countries():
    """Get list of all countries that have sites with valid coordinates"""
    try:
        # Database connection string for Azure SQL
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=dev-server-sqldb.database.windows.net;"
            "DATABASE=dev-aurora-sqldb;"
            "UID=aurora;"
            "PWD=rcqM4?nTZH+hpfX7;"
            "TrustServerCertificate=yes;"
        )
        
        # Connect to database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Query to get distinct countries with valid coordinates
        # Note: Site_Latitude and Site_Longitude are VARCHAR, so we check for non-empty strings
        query = """
            SELECT DISTINCT Site_Country
            FROM [dbo].[Mast_Site]
            WHERE Site_PK != 0
                AND Site_Country IS NOT NULL
                AND Site_Country != ''
                AND Site_Latitude IS NOT NULL
                AND Site_Longitude IS NOT NULL
                AND LTRIM(RTRIM(CAST(Site_Latitude AS VARCHAR(50)))) != ''
                AND LTRIM(RTRIM(CAST(Site_Longitude AS VARCHAR(50)))) != ''
                AND LTRIM(RTRIM(CAST(Site_Latitude AS VARCHAR(50)))) != '0'
                AND LTRIM(RTRIM(CAST(Site_Longitude AS VARCHAR(50)))) != '0'
                AND LTRIM(RTRIM(CAST(Site_Latitude AS VARCHAR(50)))) != '0.000000'
                AND LTRIM(RTRIM(CAST(Site_Longitude AS VARCHAR(50)))) != '0.000000'
                AND TRY_CAST(Site_Latitude AS FLOAT) IS NOT NULL
                AND TRY_CAST(Site_Longitude AS FLOAT) IS NOT NULL
                AND TRY_CAST(Site_Latitude AS FLOAT) != 0
                AND TRY_CAST(Site_Longitude AS FLOAT) != 0
            ORDER BY Site_Country
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        countries = [row.Site_Country for row in rows]
        
        cursor.close()
        conn.close()
        
        print(f"[INFO] Found {len(countries)} countries with valid coordinates")
        
        return jsonify({
            'count': len(countries),
            'countries': countries
        }), 200
        
    except pyodbc.Error as db_error:
        print(f"[ERROR] Database error: {str(db_error)}")
        return jsonify({
            'error': f'Database error: {str(db_error)}',
            'type': 'database_error'
        }), 500
    except Exception as e:
        print(f"[ERROR] Failed to fetch countries: {str(e)}")
        return jsonify({
            'error': f'Failed to fetch countries: {str(e)}',
            'type': 'general_error'
        }), 500

# ================================
# NEW API STRUCTURE - v1 Endpoints
# ================================

# API Documentation endpoints
@app.route('/api/v1/docs', methods=['GET'])
def get_api_docs():
    """Get comprehensive API documentation for all endpoints"""
    docs = {
        "version": "1.0.0",
        "title": "AddressIQ API",
        "description": "Comprehensive address processing and validation API",
        "endpoints": {
            "files": {
                "description": "File upload and processing operations",
                "endpoints": {
                    "POST /api/v1/files/upload": {
                        "description": "Upload Excel/CSV file and get processed file immediately",
                        "parameters": {
                            "file": "multipart/form-data file upload (CSV, XLS, XLSX)"
                        },
                        "returns": "Directly returns the processed CSV file for download"
                    },
                    "POST /api/v1/files/upload-async": {
                        "description": "Upload Excel/CSV file for asynchronous processing",
                        "parameters": {
                            "file": "multipart/form-data file upload"
                        },
                        "returns": "Processing ID for status checking"
                    },
                    "GET /api/v1/files/status/{processing_id}": {
                        "description": "Get processing status and progress (for async uploads)",
                        "parameters": {"processing_id": "UUID from async upload response"},
                        "returns": "Status, progress percentage, and results"
                    },
                    "GET /api/v1/files/download/{filename}": {
                        "description": "Download processed file (for async uploads)",
                        "parameters": {"filename": "Processed file name"},
                        "returns": "File download"
                    }
                }
            },
            "addresses": {
                "description": "Address processing and standardization",
                "endpoints": {
                    "POST /api/v1/addresses/standardize": {
                        "description": "Standardize single address",
                        "parameters": {"address": "Raw address string"},
                        "returns": "Standardized address components"
                    },
                    "POST /api/v1/addresses/batch-standardize": {
                        "description": "Standardize multiple addresses",
                        "parameters": {"addresses": "Array of address strings"},
                        "returns": "Array of standardized addresses"
                    }
                }
            },
            "compare": {
                "description": "Address comparison operations",
                "endpoints": {
                    "POST /api/v1/compare/upload": {
                        "description": "Upload file for comparison processing",
                        "parameters": {
                            "file": "multipart/form-data file upload",
                            "options": "Comparison options"
                        },
                        "returns": "Processing ID and comparison results"
                    }
                }
            },
            "database": {
                "description": "Database connection and processing",
                "endpoints": {
                    "POST /api/v1/database/connect": {
                        "description": "Connect to database and get query results directly",
                        "parameters": {
                            "connectionString": "Database connection string (required)",
                            "sourceType": "Data source type: 'table' or 'query' (required)",
                            "tableName": "Table name (required if sourceType='table')",
                            "columnNames": "Array of column names (required if sourceType='table', at least one)",
                            "uniqueId": "Unique identifier column name (optional if sourceType='table')",
                            "query": "SQL query (required if sourceType='query')",
                            "limit": "Maximum number of records to return (optional, default: 10)"
                        },
                        "returns": "Direct query results with data array, row count, columns, and success status",
                        "table_mode": {
                            "description": "Fetch specific columns from a database table",
                            "required_parameters": ["connectionString", "sourceType", "tableName", "columnNames"],
                            "optional_parameters": ["uniqueId", "limit"],
                            "request_example": {
                                "connectionString": "Server=localhost;Database=MyDB;User Id=user;Password=pass;TrustServerCertificate=True;",
                                "sourceType": "table",
                                "tableName": "Mast_Site",
                                "columnNames": ["Site_Name", "Site_Address_1", "Site_City", "Site_Country"],
                                "uniqueId": "Site_PK",
                                "limit": 50
                            },
                            "response_example": {
                                "success": True,
                                "message": "Query executed successfully. Retrieved 3 records.",
                                "data": [
                                    {"Site_PK": 1001, "Site_Name": "Main Office", "Site_Address_1": "123 Business Park Dr", "Site_City": "New York", "Site_Country": "USA"},
                                    {"Site_PK": 1002, "Site_Name": "West Coast Branch", "Site_Address_1": "456 Technology Blvd", "Site_City": "Los Angeles", "Site_Country": "USA"},
                                    {"Site_PK": 1003, "Site_Name": "Regional Hub", "Site_Address_1": "789 Commerce Ave", "Site_City": "Chicago", "Site_Country": "USA"}
                                ],
                                "row_count": 3,
                                "columns": ["Site_PK", "Site_Name", "Site_Address_1", "Site_City", "Site_Country"],
                                "query_executed": "SELECT TOP 50 Site_PK, Site_Name, Site_Address_1, Site_City, Site_Country FROM Mast_Site"
                            }
                        },
                        "query_mode": {
                            "description": "Execute a custom SQL query to fetch address data",
                            "required_parameters": ["connectionString", "sourceType", "query"],
                            "optional_parameters": ["limit"],
                            "request_example": {
                                "connectionString": "Server=localhost;Database=MyDB;User Id=user;Password=pass;TrustServerCertificate=True;",
                                "sourceType": "query",
                                "query": "SELECT TOP 3 Site_Address_1 as address FROM Mast_Site",
                                "limit": 3
                            },
                            "response_example": {
                                "success": True,
                                "message": "Query executed successfully. Retrieved 3 records.",
                                "data": [
                                    {"address": "123 Business Park Dr"},
                                    {"address": "456 Technology Blvd"},
                                    {"address": "789 Commerce Ave"}
                                ],
                                "row_count": 3,
                                "columns": ["address"],
                                "query_executed": "SELECT TOP 3 Site_Address_1 as address FROM Mast_Site"
                            }
                        },
                        "response_format": {
                            "success": True,
                            "message": "Query executed successfully. Retrieved 3 records.",
                            "data": [
                                {"id": 1, "address": "123 Main St", "city": "New York"},
                                {"id": 2, "address": "456 Oak Ave", "city": "Los Angeles"},
                                {"id": 3, "address": "789 Pine Rd", "city": "Chicago"}
                            ],
                            "row_count": 3,
                            "columns": ["id", "address", "city"],
                            "query_executed": "SELECT TOP 10 id, address, city FROM customers"
                        }
                    }
                }
            }
        },
        "documentation": {
            "description": "API documentation and guides",
            "endpoints": {
                "GET /api/v1/docs": {
                    "description": "Get comprehensive API documentation (JSON format)",
                    "returns": "Complete API documentation with all endpoints"
                },
                "GET /api/v1/docs/download": {
                    "description": "Download Postman API testing guides (.docx files)",
                    "parameters": {
                        "guide": "Guide type (file-upload, address-single, address-batch, compare-upload, database-table, database-query)"
                    },
                    "returns": "Microsoft Word document with step-by-step Postman instructions for the specified API",
                    "examples": [
                        "/api/v1/docs/download?guide=file-upload",
                        "/api/v1/docs/download?guide=address-single",
                        "/api/v1/docs/download?guide=address-batch"
                    ]
                }
            }
        },
        "authentication": {
            "type": "API Key",
            "header": "X-API-Key",
            "description": "Required for public API access. Set ADDRESSIQ_PUBLIC_API_KEY environment variable."
        }
    }
    return jsonify(docs), 200

@app.route('/api/v1/docs/download', methods=['GET'])
def get_api_documentation_file():
    """Download Postman API testing documentation file based on guide parameter"""
    try:
        # Get the guide parameter from query string
        guide_type = request.args.get('guide', 'file-upload')
        
        # Path to the documentation file in samples directory
        samples_dir = BASE_DIR / 'samples'
        
        # Map guide types to file paths and download names
        guide_mapping = {
            'file-upload': {
                'file': 'AddressIQ API - File Upload & Processing.docx',
                'download_name': 'AddressIQ_API_Postman_Guide.docx'
            },
            'address-single': {
                'file': 'AddressIQ API - Single Address Standardization.docx',
                'download_name': 'AddressIQ_Single_Address_API_Guide.docx'
            },
            'address-batch': {
                'file': 'AddressIQ API - Batch Address Standardization.docx',
                'download_name': 'AddressIQ_Batch_Address_API_Guide.docx'
            },
            'compare-upload': {
                'file': 'AddressIQ API - Compare Upload Processing.docx',
                'download_name': 'AddressIQ_Compare_Upload_API_Guide.docx'
            },
            'database-table': {
                'file': 'AddressIQ API - Database Connection Table Mode.docx',
                'download_name': 'AddressIQ_Database_Table_Mode_API_Guide.docx'
            },
            'database-query': {
                'file': 'AddressIQ API - Database Connection Query Mode.docx',
                'download_name': 'AddressIQ_Database_Query_Mode_API_Guide.docx'
            }
        }
        
        if guide_type not in guide_mapping:
            return jsonify({'error': f'Invalid guide type: {guide_type}'}), 400
        
        guide_info = guide_mapping[guide_type]
        doc_file = samples_dir / guide_info['file']
        
        if not doc_file.exists():
            return jsonify({'error': f'Documentation file not found for guide: {guide_type}'}), 404
        
        return send_file(
            str(doc_file),
            as_attachment=True,
            download_name=guide_info['download_name'],
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return jsonify({'error': f'Documentation download failed: {str(e)}'}), 500

# File Processing API endpoints
@app.route('/api/v1/files/upload', methods=['POST'])
def api_v1_file_upload():
    """v1 API: Upload file for address processing and return processed file directly"""
    # Check API key for public access
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Process file synchronously and return the processed file
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not _allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .xlsx, .xls, or .csv'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = secure_filename(file.filename)
        name_part, ext_part = os.path.splitext(safe_filename)
        unique_filename = f"{name_part}_{timestamp}{ext_part}"
        
        # Save file
        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Process file synchronously
        processor = CSVAddressProcessor(base_directory=str(BASE_DIR))
        output_path = processor.process_csv_file(str(file_path))
        
        if not output_path or not os.path.exists(output_path):
            # Clean up inbound file on error
            try:
                os.remove(file_path)
            except:
                pass
            return jsonify({'error': 'File processing failed - no output generated'}), 500
        
        # Generate a user-friendly filename for download
        original_name = os.path.splitext(safe_filename)[0]
        download_filename = f"{original_name}_processed_{timestamp}.csv"
        
        # Return the processed file directly
        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        # Clean up any temporary files on error
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        return jsonify({'error': f'Upload and processing failed: {str(e)}'}), 500

@app.route('/api/v1/files/upload-async', methods=['POST'])
def api_v1_file_upload_async():
    """v1 API: Upload file for asynchronous address processing with database persistence and webhook support"""
    # Check API key for public access
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not _allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .xlsx, .xls, or .csv'}), 400
        
        # Generate unique job ID and filename
        job_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = secure_filename(file.filename)
        name_part, ext_part = os.path.splitext(safe_filename)
        unique_filename = f"{name_part}_{timestamp}{ext_part}"
        
        # Save file
        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get optional webhook callback URL from form data
        callback_url = request.form.get('callback_url')
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create job in database
        job_manager.create_job(
            job_id=job_id,
            filename=unique_filename,
            original_filename=safe_filename,
            component='compare',
            file_size=file_size,
            callback_url=callback_url,
            api_key=request.headers.get('X-API-Key'),
            user_ip=request.remote_addr,
            progress=0,
            message='File uploaded, processing queued',
            steps=[
                {'name': 'upload', 'label': 'Upload', 'target': 10},
                {'name': 'initialize', 'label': 'Initialize', 'target': 20},
                {'name': 'read', 'label': 'Read File', 'target': 35},
                {'name': 'standardize', 'label': 'Standardize', 'target': 55},
                {'name': 'finalize', 'label': 'Finalize', 'target': 85},
                {'name': 'complete', 'label': 'Complete', 'target': 100}
            ],
            logs=[{'ts': datetime.utcnow().isoformat() + 'Z', 'message': 'File uploaded', 'progress': 0}]
        )
        
        # LEGACY: Also initialize in-memory for backwards compatibility
        processing_status[job_id] = {
            'status': 'queued',
            'message': 'File uploaded, processing queued',
            'filename': unique_filename,
            'progress': 0
        }
        
        # Start background processing
        thread = threading.Thread(target=process_file_background, args=(job_id, unique_filename))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'filename': unique_filename,
            'file_size': file_size,
            'status': 'queued',
            'message': 'File uploaded successfully and processing started',
            'status_url': f'/api/v1/files/status/{job_id}',
            'estimated_time_seconds': 60
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/v1/files/status/<job_id>', methods=['GET'])
def api_v1_file_status(job_id):
    """v1 API: Get file processing status with enhanced details from database"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Get job from database
    job = job_manager.get_job(job_id)
    if not job:
        # LEGACY: Fallback to in-memory dict
        if job_id in processing_status:
            status_data = processing_status[job_id]
            return jsonify({
                'job_id': job_id,
                'status': status_data.get('status', 'unknown'),
                'progress': status_data.get('progress', 0),
                'message': status_data.get('message', ''),
                'filename': status_data.get('filename'),
                'error': status_data.get('error'),
                'output_file': status_data.get('output_file'),
                'created_at': status_data.get('created_at'),
                'finished_at': status_data.get('finished_at')
            }), 200
        return jsonify({'error': 'Job not found'}), 404
    
    # Build response from database job
    response = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job.get('progress', 0),
        'message': job.get('message'),
        'error': job.get('error'),
        'filename': job.get('original_filename'),
        'created_at': job.get('created_at'),
        'started_at': job.get('started_at'),
        'updated_at': job.get('updated_at'),
        'finished_at': job.get('finished_at'),
        'expires_at': job.get('expires_at'),
        'steps': job.get('steps', []),
        'logs': job.get('logs', [])[-10:]  # Last 10 logs only
    }
    
    # Add download URL if completed
    if job['status'] == 'completed' and job.get('output_file'):
        response['download_url'] = f'/api/v1/files/download/{job["output_file"]}'
        response['output_file'] = job['output_file']
    
    # Add file info if available
    if job.get('file_info'):
        response['file_info'] = job['file_info']
    elif job.get('file_rows'):
        response['file_info'] = {
            'rows': job['file_rows'],
            'columns': job['file_columns'],
            'size': job.get('file_size')
        }
    
    return jsonify(response), 200

@app.route('/api/v1/files/download/<filename>', methods=['GET'])
def api_v1_file_download(filename):
    """v1 API: Download processed file"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Check if file is expired before allowing download
    try:
        # Find job by output filename
        all_jobs = job_manager.get_jobs(limit=1000)  # Get recent jobs
        job_for_file = None
        for job in all_jobs:
            if job.get('output_file') == filename:
                job_for_file = job
                break
        
        # If job found, check expiration
        if job_for_file:
            expires_at = job_for_file.get('expires_at')
            if expires_at:
                from datetime import datetime
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.utcnow() > expiry_date.replace(tzinfo=None):
                    return jsonify({'error': 'File has expired and is no longer available for download'}), 410
        
        file_path = OUTBOUND_FOLDER / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/v1/files/jobs', methods=['GET'])
def api_v1_list_jobs():
    """v1 API: List user's jobs with pagination"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    try:
        # Get query parameters
        status = request.args.get('status')  # Filter by status (optional)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Get jobs from database
        jobs = job_manager.get_jobs(status=status, limit=limit, offset=offset)
        
        # Format response
        jobs_list = []
        for job in jobs:
            job_data = {
                'job_id': job['job_id'],
                'status': job['status'],
                'filename': job['original_filename'],
                'component': job.get('component', 'upload'),
                'progress': job.get('progress', 0),
                'created_at': job.get('created_at'),
                'finished_at': job.get('finished_at'),
                'expires_at': job.get('expires_at')
            }
            
            # Add download URL if completed
            if job['status'] == 'completed' and job.get('output_file'):
                job_data['download_url'] = f'/api/v1/files/download/{job["output_file"]}'
                job_data['output_file'] = job['output_file']
            
            # Add error if failed
            if job['status'] in ['failed', 'error']:
                job_data['error'] = job.get('error')
            
            jobs_list.append(job_data)
        
        return jsonify({
            'jobs': jobs_list,
            'count': len(jobs_list),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list jobs: {str(e)}'}), 500

@app.route('/api/v1/admin/stats', methods=['GET'])
def api_v1_admin_stats():
    """v1 API: Get database statistics (basic access)"""
    try:
        stats = job_manager.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/v1/admin/cleanup', methods=['POST'])
def api_v1_admin_cleanup():
    """v1 API: Cleanup expired jobs and files (basic access)"""
    try:
        dry_run = request.args.get('dry_run', 'false').lower() == 'true'
        result = job_manager.cleanup_expired_jobs(dry_run=dry_run)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

# Address Processing API endpoints  
@app.route('/api/v1/addresses/standardize', methods=['POST'])
def api_v1_address_standardize():
    """v1 API: Standardize single address"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing single address processing logic
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        # Process single address using existing logic
        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from csv_address_processor import CSVAddressProcessor
        processor = CSVAddressProcessor()
        
        result = processor.standardize_single_address(address.strip(), 0)
        
        return jsonify({
            'success': True,
            'input_address': address,
            'standardized_address': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Address standardization failed: {str(e)}'}), 500

@app.route('/api/v1/addresses/batch-standardize', methods=['POST'])
def api_v1_addresses_batch_standardize():
    """v1 API: Standardize multiple addresses"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing batch processing logic
    try:
        data = request.get_json() or {}
        addresses = data.get('addresses')
        if not addresses or not isinstance(addresses, list):
            return jsonify({'error': 'addresses (array) is required'}), 400
        
        if len(addresses) > 1000:
            return jsonify({'error': 'Maximum 1000 addresses per batch'}), 400
        
        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from csv_address_processor import CSVAddressProcessor
        processor = CSVAddressProcessor()
        
        results = []
        for idx, raw in enumerate(addresses):
            addr = (raw or '').strip()
            if not addr:
                results.append({
                    'index': idx,
                    'input_address': raw,
                    'standardized_address': None,
                    'error': 'Empty address'
                })
                continue
            
            try:
                result = processor.standardize_single_address(addr, idx)
                results.append({
                    'index': idx,
                    'input_address': raw,
                    'standardized_address': result,
                    'error': None
                })
            except Exception as e:
                results.append({
                    'index': idx,
                    'input_address': raw,
                    'standardized_address': None,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_addresses': len(addresses),
            'processed_addresses': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Batch address processing failed: {str(e)}'}), 500

# Compare Processing API endpoints
@app.route('/api/v1/compare/upload', methods=['POST'])
def api_v1_compare_upload():
    """v1 API: Upload file for comparison processing and return processed file directly"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Process file synchronously and return the processed file
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not _allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .xlsx, .xls, or .csv'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = secure_filename(file.filename)
        name_part, ext_part = os.path.splitext(safe_filename)
        unique_filename = f"compare_{name_part}_{timestamp}{ext_part}"
        
        # Save file to inbound folder
        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Run comparison processing synchronously
        try:
            # Use the same logic as process_compare_background but synchronously
            inbound_file = INBOUND_FOLDER / unique_filename
            if not inbound_file.exists():
                raise Exception('Uploaded file not found on server')

            # Snapshot outbound directory before run
            before = {f.name: (OUTBOUND_FOLDER / f.name).stat().st_mtime for f in OUTBOUND_FOLDER.glob('*') if f.is_file()}
            start_ts = time.time()

            script_path = BASE_DIR / 'csv_address_processor.py'
            # Target only the uploaded file to avoid interference from other inbound files
            cmd = [
                sys.executable,
                str(script_path),
                str(inbound_file),  # positional input_file per argparse spec
                '--compare-csv',
                '--batch-size', '5'
            ]
            
            child_env = os.environ.copy()
            child_env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=child_env,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f'Comparison processing failed: {result.stderr}')

            # Find new/updated files after start_ts
            candidates = []
            for p in OUTBOUND_FOLDER.glob('*.csv'):
                try:
                    mtime = p.stat().st_mtime
                    if mtime >= start_ts and (p.name not in before or mtime > before.get(p.name, 0)):
                        candidates.append((mtime, p))
                except Exception:
                    continue

            if not candidates:
                raise Exception('Comparison output not found - no new file in outbound directory')

            candidates.sort(key=lambda x: x[0], reverse=True)
            output_file = candidates[0][1]
            
            # Generate a user-friendly filename for download
            original_name = os.path.splitext(safe_filename)[0]
            download_filename = f"{original_name}_compared_{timestamp}.csv"
            
            # Return the processed file directly
            return send_file(
                str(output_file),
                as_attachment=True,
                download_name=download_filename,
                mimetype='text/csv'
            )
            
        except subprocess.TimeoutExpired:
            raise Exception('File processing timed out - file may be too large')
        except Exception as processing_error:
            raise Exception(f'File processing failed: {str(processing_error)}')
        
    except Exception as e:
        # Clean up any temporary files on error
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        return jsonify({'error': f'Compare upload and processing failed: {str(e)}'}), 500

def compare_file_background(processing_id, filename):
    """Background task for comparison processing"""
    try:
        # This would implement the comparison logic
        # For now, we'll reuse the existing comparison logic from the original endpoint
        _update_status(processing_id, status='processing', message='Starting comparison...', progress=25)
        
        # You can implement specific comparison logic here
        # For now, using a placeholder
        _update_status(processing_id, status='completed', message='Comparison completed', progress=100)
        
    except Exception as e:
        _update_status(processing_id, status='error', message=f'Comparison failed: {str(e)}', progress=100, error=str(e))

# Database Processing API endpoints
@app.route('/api/v1/database/connect', methods=['POST'])
def api_v1_database_connect():
    """v1 API: Connect to database and get results directly"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Support both legacy format and new enhanced format
        connection_string = data.get('connectionString')
        source_type = data.get('sourceType')
        
        # Enhanced format validation
        if connection_string and source_type:
            # New enhanced format with connection string and flexible query options
            if not connection_string.strip():
                return jsonify({'error': 'connectionString cannot be empty'}), 400
            
            if source_type not in ['table', 'query']:
                return jsonify({'error': 'sourceType must be either "table" or "query"'}), 400
            
            if source_type == 'table':
                # Table mode: require tableName and at least one columnName
                table_name = data.get('tableName', '').strip()
                column_names = data.get('columnNames', [])
                
                if not table_name:
                    return jsonify({'error': 'tableName is required when sourceType is "table"'}), 400
                
                # Ensure columnNames is a list and has at least one valid entry
                if not isinstance(column_names, list) or not any(str(col).strip() for col in column_names):
                    return jsonify({'error': 'At least one columnName is required when sourceType is "table"'}), 400
                
            elif source_type == 'query':
                # Query mode: require query
                query = data.get('query', '').strip()
                if not query:
                    return jsonify({'error': 'query is required when sourceType is "query"'}), 400
        
        else:
            # Legacy format: maintain backward compatibility
            required_fields = ['server', 'database', 'query']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Convert legacy format to enhanced format for internal processing
            server = data.get('server', '')
            database = data.get('database', '')
            username = data.get('username', '')
            password = data.get('password', '')
            query = data.get('query', '')
            
            # Build connection string from individual parameters
            if username and password:
                connection_string = f"Server={server};Database={database};User Id={username};Password={password};TrustServerCertificate=True;"
            else:
                connection_string = f"Server={server};Database={database};Integrated Security=True;TrustServerCertificate=True;"
            
            # Set as query mode
            source_type = 'query'
            data['connectionString'] = connection_string
            data['sourceType'] = source_type
            data['query'] = query
        
        # Set default limit if not provided
        limit = int(data.get('limit', 10))
        
        # Execute database query synchronously and return results directly
        result = _execute_database_query_sync(connection_string, source_type, data, limit)
        
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database connection failed: {str(e)}',
            'data': [],
            'row_count': 0,
            'columns': []
        }), 500

# Sample file download endpoints
@app.route('/api/v1/samples/file-upload', methods=['GET'])
def download_file_upload_sample():
    """Download sample file for file upload processing"""
    try:
        # Use absolute hardcoded path to sample file
        sample_file = SAMPLES_FOLDER / 'file-upload-sample.csv'
        
        if not sample_file.exists():
            app.logger.error(f'Sample file not found at: {sample_file}')
            return jsonify({'error': f'Sample file not found at: {sample_file}'}), 404
        
        return send_file(
            str(sample_file),  # Convert Path to string
            as_attachment=True,
            download_name='file-upload-sample.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        app.logger.error(f'Failed to download file upload sample: {str(e)}')
        return jsonify({'error': f'Failed to download sample: {str(e)}'}), 500

@app.route('/api/v1/samples/compare-upload', methods=['GET'])
def download_compare_upload_sample():
    """Download sample file for compare upload processing"""
    try:
        # Use absolute hardcoded path to sample file
        sample_file = SAMPLES_FOLDER / 'compare-upload-sample.csv'
        
        if not sample_file.exists():
            app.logger.error(f'Sample file not found at: {sample_file}')
            return jsonify({'error': f'Sample file not found at: {sample_file}'}), 404
        
        return send_file(
            str(sample_file),  # Convert Path to string
            as_attachment=True,
            download_name='compare-upload-sample.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        app.logger.error(f'Failed to download compare upload sample: {str(e)}')
        return jsonify({'error': f'Failed to download sample: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)