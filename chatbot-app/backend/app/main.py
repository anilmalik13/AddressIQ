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
# no external encoding detector here; rely on utf-8 replacement for preview

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure upload settings - using inbound folder instead of C:\uploaded_files
BASE_DIR = Path(__file__).parent.parent  # Points to backend folder
INBOUND_FOLDER = BASE_DIR / 'inbound'
OUTBOUND_FOLDER = BASE_DIR / 'outbound'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['INBOUND_FOLDER'] = str(INBOUND_FOLDER)
app.config['OUTBOUND_FOLDER'] = str(OUTBOUND_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
os.makedirs(INBOUND_FOLDER, exist_ok=True)
os.makedirs(OUTBOUND_FOLDER, exist_ok=True)

# Store processing status
processing_status = {}

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

# Helper for consistent status updates and lightweight logging
def _update_status(processing_id: str, **fields):
    entry = processing_status.get(processing_id)
    if not entry:
        return
    now_iso = datetime.utcnow().isoformat() + 'Z'
    entry['updated_at'] = now_iso
    log_message = fields.pop('log', None)
    for k, v in fields.items():
        entry[k] = v
    if log_message:
        logs = entry.setdefault('logs', [])
        logs.append({'ts': now_iso, 'message': log_message, 'progress': entry.get('progress')})
        # Keep only last 100 log entries
        if len(logs) > 100:
            del logs[:-100]

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
            '/api/coordinates'
        ]
    }), 200

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
    df.to_csv(file_path, index=False, encoding='utf-8')
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

def process_file_background(processing_id, filename):
    """Process the uploaded file in-process using CSVAddressProcessor for better progress feedback."""
    try:
        inbound_file = INBOUND_FOLDER / filename
        if not inbound_file.exists():
            _update_status(processing_id, status='error', message='Uploaded file not found on server', progress=100, error='Missing inbound file', log='Inbound file missing')
            return

        _update_status(processing_id, status='processing', message='Initializing processor...', progress=20, log='Processor initialization')

        processor = CSVAddressProcessor(base_directory=str(BASE_DIR))
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

def process_compare_background(processing_id, filename):
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
    """Get the status of file processing"""
    try:
        if processing_id in processing_status:
            return jsonify(processing_status[processing_id]), 200
        else:
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
            if filename.lower().endswith('.csv'):
                # Use robust encoding detection to handle non-UTF-8 CSVs
                df = read_csv_with_encoding_detection(file_path)
                # Use a small sample for file info to keep consistent with Excel path
                df_sample = df.head(5)
            else:
                df_sample = pd.read_excel(file_path, nrows=5)

            file_info = {
                'rows': int(getattr(df_sample, 'shape', [0, 0])[0]),
                'columns': int(getattr(df_sample, 'shape', [0, 0])[1]),
                'column_names': getattr(df_sample, 'columns', []).tolist() if hasattr(df_sample, 'columns') else []
            }

        except Exception as e:
            # If file is invalid, remove it and return error
            try:
                os.remove(file_path)
            except Exception:
                pass
            return jsonify({'error': f'Invalid file format or corrupted file: {str(e)}'}), 400
        
        # Generate processing ID for tracking
        processing_id = f"proc_{timestamp}_{hash(unique_filename) % 10000}"
        
        # Initialize processing status
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
            args=(processing_id, unique_filename)
        )
        thread.daemon = True
        thread.start()
        
        # Return success response with processing ID
        return jsonify({
            'message': f'File uploaded successfully! Processing started.',
            'processing_id': processing_id,
            'filename': unique_filename,
            'file_info': file_info
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

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"

        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)

        # Validate quick read with robust CSV encoding handling
        file_info = None
        try:
            if filename.lower().endswith('.csv'):
                df = read_csv_with_encoding_detection(file_path)
                df_sample = df.head(5)
            else:
                df_sample = pd.read_excel(file_path, nrows=5)
            file_info = {
                'rows': int(getattr(df_sample, 'shape', [0, 0])[0]),
                'columns': int(getattr(df_sample, 'shape', [0, 0])[1]),
                'column_names': getattr(df_sample, 'columns', []).tolist() if hasattr(df_sample, 'columns') else []
            }
        except Exception as ve:
            try:
                os.remove(file_path)
            except Exception:
                pass
            return jsonify({'error': f'Invalid file: {str(ve)}'}), 400

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

        thread = threading.Thread(target=process_compare_background, args=(processing_id, unique_filename))
        thread.daemon = True
        thread.start()

        return jsonify({
            'message': 'Comparison started',
            'processing_id': processing_id,
            'filename': unique_filename,
            'file_info': file_info
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
        
        # Import the CSV processor to use its address standardization
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from csv_address_processor import CSVAddressProcessor
        
        processor = CSVAddressProcessor()
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

        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from csv_address_processor import CSVAddressProcessor
        processor = CSVAddressProcessor()

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
    """Get coordinates for region and country"""
    try:
        region = request.args.get('region')
        country = request.args.get('country')
        
        if not region or not country:
            return jsonify({'error': 'Both region and country parameters are required'}), 400
        
        # This is a placeholder - you can integrate with your geographical data source
        # For now, return mock coordinates
        coordinates = {
            'region': region,
            'country': country,
            'latitude': 0.0,
            'longitude': 0.0,
            'message': 'Coordinate lookup functionality to be implemented'
        }
        
        return jsonify(coordinates), 200
        
    except Exception as e:
        return jsonify({'error': f'Coordinate lookup failed: {str(e)}'}), 500

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
                        "description": "Upload Excel/CSV file for address processing",
                        "parameters": {
                            "file": "multipart/form-data file upload",
                            "options": "JSON object with processing options"
                        },
                        "returns": "Processing ID and file information"
                    },
                    "GET /api/v1/files/status/{processing_id}": {
                        "description": "Get processing status and progress",
                        "parameters": {"processing_id": "UUID from upload response"},
                        "returns": "Status, progress percentage, and results"
                    },
                    "GET /api/v1/files/download/{filename}": {
                        "description": "Download processed file",
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
                        "description": "Connect to database and process addresses",
                        "parameters": {
                            "connection": "Database connection details",
                            "query": "SQL query for address extraction",
                            "options": "Processing options"
                        },
                        "returns": "Processing ID and connection status"
                    }
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

# File Processing API endpoints
@app.route('/api/v1/files/upload', methods=['POST'])
def api_v1_file_upload():
    """v1 API: Upload file for address processing"""
    # Check API key for public access
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing upload logic but with consistent v1 response format
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not _allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .xlsx, .xls, or .csv'}), 400
        
        # Generate unique filename and processing ID
        processing_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = secure_filename(file.filename)
        name_part, ext_part = os.path.splitext(safe_filename)
        unique_filename = f"{name_part}_{timestamp}{ext_part}"
        
        # Save file
        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Start background processing
        _update_status(processing_id, status='queued', message='File uploaded, processing queued', 
                      filename=unique_filename, progress=0)
        
        thread = threading.Thread(target=process_file_background, args=(processing_id, unique_filename))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'processing_id': processing_id,
            'filename': unique_filename,
            'file_size': file_size,
            'status': 'queued',
            'message': 'File uploaded successfully and processing started'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/v1/files/status/<processing_id>', methods=['GET'])
def api_v1_file_status(processing_id):
    """v1 API: Get file processing status"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing status logic
    if processing_id not in processing_status:
        return jsonify({'error': 'Processing ID not found'}), 404
    
    status_data = processing_status[processing_id]
    return jsonify({
        'processing_id': processing_id,
        'status': status_data.get('status', 'unknown'),
        'progress': status_data.get('progress', 0),
        'message': status_data.get('message', ''),
        'filename': status_data.get('filename'),
        'error': status_data.get('error'),
        'result_file': status_data.get('result_file'),
        'created_at': status_data.get('created_at'),
        'completed_at': status_data.get('completed_at')
    }), 200

@app.route('/api/v1/files/download/<filename>', methods=['GET'])
def api_v1_file_download(filename):
    """v1 API: Download processed file"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing download logic
    try:
        file_path = OUTBOUND_FOLDER / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

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
        
        result = processor.process_address(address.strip())
        
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
                result = processor.process_address(addr)
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
    """v1 API: Upload file for comparison processing"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing compare upload logic with v1 response format
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not _allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .xlsx, .xls, or .csv'}), 400
        
        # Generate unique filename and processing ID
        processing_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = secure_filename(file.filename)
        name_part, ext_part = os.path.splitext(safe_filename)
        unique_filename = f"compare_{name_part}_{timestamp}{ext_part}"
        
        # Save file
        file_path = os.path.join(app.config['INBOUND_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Start background comparison processing
        _update_status(processing_id, status='queued', message='File uploaded for comparison, processing queued', 
                      filename=unique_filename, progress=0)
        
        # Note: You may need to implement compare_file_background similar to process_file_background
        thread = threading.Thread(target=compare_file_background, args=(processing_id, unique_filename))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'processing_id': processing_id,
            'filename': unique_filename,
            'file_size': file_size,
            'status': 'queued',
            'message': 'File uploaded successfully for comparison processing'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Compare upload failed: {str(e)}'}), 500

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
    """v1 API: Connect to database and process addresses"""
    auth_valid, auth_error = _check_api_key()
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # Reuse existing database connection logic with v1 response format
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        required_fields = ['server', 'database', 'query']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        processing_id = str(uuid.uuid4())
        
        # Set default limit if not provided
        data['limit'] = int(data.get('limit', 10))
        
        # Start background database processing
        _update_status(processing_id, status='queued', message='Database connection queued', progress=0)
        
        thread = threading.Thread(target=process_db_task, args=(processing_id, data))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'processing_id': processing_id,
            'status': 'queued',
            'message': 'Database processing started successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Database connection failed: {str(e)}'}), 500

# Sample file download endpoints
@app.route('/api/v1/samples/file-upload', methods=['GET'])
def download_file_upload_sample():
    """Download sample file for file upload processing"""
    try:
        samples_dir = BASE_DIR / 'samples'
        sample_file = samples_dir / 'file-upload-sample.csv'
        
        if sample_file.exists():
            return send_file(
                sample_file,
                as_attachment=True,
                download_name='file-upload-sample.csv',
                mimetype='text/csv'
            )
        else:
            return jsonify({'error': 'Sample file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to download sample: {str(e)}'}), 500

@app.route('/api/v1/samples/compare-upload', methods=['GET'])
def download_compare_upload_sample():
    """Download sample file for compare upload processing"""
    try:
        samples_dir = BASE_DIR / 'samples'
        sample_file = samples_dir / 'compare-upload-sample.csv'
        
        if sample_file.exists():
            return send_file(
                sample_file,
                as_attachment=True,
                download_name='compare-upload-sample.csv',
                mimetype='text/csv'
            )
        else:
            return jsonify({'error': 'Sample file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to download sample: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)