"""
AddressIQ API Endpoints Documentation

This file defines the new organized API structure that will serve both existing 
frontend components and the new public API interface.

API Versioning: All new endpoints will be under /api/v1/
Backward Compatibility: Existing endpoints remain functional but deprecated

Features to Expose as Public APIs:
1. File Upload & Processing (Excel/CSV)
2. Compare Upload 
3. Address Processing (Single & Batch)
4. Database Connect & Processing

API Categories:
"""

from flask import Blueprint
from .main import app

# Create blueprints for organized API structure
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# File Processing API endpoints
file_api = Blueprint('file_api', __name__, url_prefix='/api/v1/files')

# Address Processing API endpoints  
address_api = Blueprint('address_api', __name__, url_prefix='/api/v1/addresses')

# Database API endpoints
database_api = Blueprint('database_api', __name__, url_prefix='/api/v1/database')

# Compare API endpoints
compare_api = Blueprint('compare_api', __name__, url_prefix='/api/v1/compare')

# API Documentation endpoints
docs_api = Blueprint('docs_api', __name__, url_prefix='/api/v1/docs')

# Register blueprints
app.register_blueprint(api_v1)
app.register_blueprint(file_api)
app.register_blueprint(address_api)
app.register_blueprint(database_api)
app.register_blueprint(compare_api)
app.register_blueprint(docs_api)