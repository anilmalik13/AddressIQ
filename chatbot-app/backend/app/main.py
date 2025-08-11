from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
from .services.azure_openai import get_access_token, connect_wso2

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure upload settings
UPLOAD_FOLDER = 'C:\\uploaded_files'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-excel', methods=['POST'])
def upload_excel_without_api():
    """Debug endpoint to catch requests without /api prefix"""
    return jsonify({
        'error': 'This endpoint is missing the /api prefix. Please use /api/upload-excel instead.',
        'debug_info': 'Frontend might be bypassing proxy or using wrong API configuration'
    }), 404

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    """Handle Excel/CSV file upload"""
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
        
        # Save file to upload directory
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
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
        
        # Return success response with file information
        return jsonify({
            'message': f'File uploaded successfully! File contains {file_info["rows"]} sample rows with {file_info["columns"]} columns.',
            'file_path': file_path,
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
    """List all uploaded files"""
    try:
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            return jsonify({'files': []}), 200
        
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': file_path
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