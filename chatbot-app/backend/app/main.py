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
from .services.azure_openai import get_access_token, connect_wso2
from csv_address_processor import CSVAddressProcessor  # direct import for in-process execution

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

@app.route('/api/download/<filename>', methods=['GET'])
def download_processed_file(filename):
    """Download processed file from outbound directory"""
    try:
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
                df = pd.read_csv(file_path, encoding='utf-8', nrows=5)  # Just read first 5 rows to validate
            else:
                df = pd.read_excel(file_path, nrows=5)  # Just read first 5 rows to validate
            
            file_info = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist()
            }
            
        except Exception as e:
            # If file is invalid, remove it and return error
            os.remove(file_path)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)