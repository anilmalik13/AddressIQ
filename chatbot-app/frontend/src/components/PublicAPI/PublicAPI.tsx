import React, { useState } from 'react';
import '../../styles/shared.css';
import './PublicAPI.css';
import { downloadDocumentationGuide as downloadDocGuideAPI, downloadSampleFile } from '../../services/api';

interface APIEndpoint {
  id: string;
  title: string;
  description: string;
  method: string;
  endpoint: string;
  parameters: { [key: string]: any };
  example: any;
  responseExample: any;
  sampleDownload?: string;
}

interface AccordionState {
  [key: string]: boolean;
}

const PublicAPI: React.FC = () => {
  const [activeAccordion, setActiveAccordion] = useState<AccordionState>({});

  const apiEndpoints: APIEndpoint[] = [
    {
      id: 'file-upload',
      title: 'File Upload & Processing', 
      description: 'Upload Excel/CSV files for address standardization and get processed file directly',
      method: 'POST',
      endpoint: '/api/v1/files/upload',
      parameters: {
        file: 'File (Excel/CSV)'
      },
      example: {
        description: 'Upload a file using multipart/form-data and receive processed file',
        curl: 'curl -X POST -F "file=@addresses.xlsx" http://localhost:5001/api/v1/files/upload'
      },
      responseExample: {
        description: "Returns processed CSV file directly as download",
        filename: "addresses_processed_20230922_143022.csv",
        content_type: "text/csv",
        note: "File is returned as attachment download, not JSON response"
      },
      sampleDownload: '/v1/samples/file-upload'
    },
    {
      id: 'address-single',
      title: 'Single Address Standardization',
      description: 'Standardize and validate a single address',
      method: 'POST',
      endpoint: '/api/v1/addresses/standardize',
      parameters: {
        address: 'Raw address string to standardize'
      },
      example: {
        description: 'Standardize a single address',
        curl: 'curl -X POST -H "Content-Type: application/json" -d \'{"address": "123 Main St, New York, NY 10001"}\' http://localhost:5001/api/v1/addresses/standardize'
      },
      responseExample: {
        success: true,
        input_address: "123 Main St, New York, NY 10001",
        standardized_address: {
          street_number: "123",
          street_name: "Main Street",
          city: "New York",
          state: "NY",
          postal_code: "10001",
          country: "USA"
        }
      }
    },
    {
      id: 'address-batch',
      title: 'Batch Address Standardization',
      description: 'Standardize multiple addresses in a single request',
      method: 'POST',
      endpoint: '/api/v1/addresses/batch-standardize',
      parameters: {
        addresses: 'Array of address strings (max 1000)'
      },
      example: {
        description: 'Standardize multiple addresses',
        curl: 'curl -X POST -H "Content-Type: application/json" -d \'{"addresses": ["123 Main St, NY", "456 Oak Ave, CA"]}\' http://localhost:5001/api/v1/addresses/batch-standardize'
      },
      responseExample: {
        success: true,
        total_addresses: 2,
        processed_addresses: 2,
        results: [
          {
            index: 0,
            input_address: "123 Main St, NY",
            standardized_address: {
              street_number: "123",
              street_name: "Main Street",
              city: "New York",
              state: "NY",
              postal_code: "10001",
              country: "USA"
            },
            error: null
          },
          {
            index: 1,
            input_address: "456 Oak Ave, CA",
            standardized_address: {
              street_number: "456",
              street_name: "Oak Avenue",
              city: "Los Angeles",
              state: "CA",
              postal_code: "90210",
              country: "USA"
            },
            error: null
          }
        ]
      }
    },
    {
      id: 'compare-upload',
      title: 'Compare Upload Processing',
      description: 'Upload files for address comparison and get processed results directly',
      method: 'POST',
      endpoint: '/api/v1/compare/upload',
      parameters: {
        file: 'File for comparison processing (CSV/Excel)'
      },
      example: {
        description: 'Upload a file for comparison and receive processed file',
        curl: 'curl -X POST -F "file=@compare_addresses.csv" http://localhost:5001/api/v1/compare/upload'
      },
      responseExample: {
        description: "Returns processed comparison CSV file directly as download",
        filename: "compare_addresses_processed_20230922_143025.csv",
        content_type: "text/csv",
        note: "File is returned as attachment download, not JSON response"
      },
      sampleDownload: '/v1/samples/compare-upload'
    },
    {
      id: 'database-connect-table',
      title: 'Database Connection - Table Mode',
      description: 'Connect to database and fetch data from a specific table with selected columns',
      method: 'POST',
      endpoint: '/api/v1/database/connect',
      parameters: {
        connectionString: 'Database connection string (required)',
        sourceType: 'Must be "table" for table mode (required)',
        tableName: 'Name of the database table (required)',
        columnNames: 'Array of column names to fetch (required, at least one non-empty)',
        uniqueId: 'Primary key or unique identifier column (optional)',
        limit: 'Maximum number of records to return (optional, default: 10)'
      },
      example: {
        description: 'Fetch specific columns from a database table',
        curl: 'curl -X POST -H "Content-Type: application/json" -H "X-API-Key: your-api-key" -d \'{"connectionString": "Server=localhost;Database=MyDB;User Id=user;Password=pass;TrustServerCertificate=True;", "sourceType": "table", "tableName": "Mast_Site", "columnNames": ["Site_Name", "Site_Address_1", "Site_City", "Site_Country"], "uniqueId": "Site_PK", "limit": 50}\' http://localhost:5001/api/v1/database/connect'
      },
      responseExample: {
        success: true,
        message: "Query executed successfully. Retrieved 3 records.",
        data: [
          { Site_PK: 1001, Site_Name: "Main Office", Site_Address_1: "123 Business Park Dr", Site_City: "New York", Site_Country: "USA" },
          { Site_PK: 1002, Site_Name: "West Coast Branch", Site_Address_1: "456 Technology Blvd", Site_City: "Los Angeles", Site_Country: "USA" },
          { Site_PK: 1003, Site_Name: "Regional Hub", Site_Address_1: "789 Commerce Ave", Site_City: "Chicago", Site_Country: "USA" }
        ],
        row_count: 3,
        columns: ["Site_PK", "Site_Name", "Site_Address_1", "Site_City", "Site_Country"],
        query_executed: "SELECT TOP 50 Site_PK, Site_Name, Site_Address_1, Site_City, Site_Country FROM Mast_Site"
      }
    },
    {
      id: 'database-connect-query',
      title: 'Database Connection - Query Mode',
      description: 'Connect to database and execute a custom SQL query to fetch data',
      method: 'POST',
      endpoint: '/api/v1/database/connect',
      parameters: {
        connectionString: 'Database connection string (required)',
        sourceType: 'Must be "query" for query mode (required)',
        query: 'Custom SQL query to execute (required, cannot be empty)',
        limit: 'Maximum number of records to return (optional, default: 10)'
      },
      example: {
        description: 'Execute a custom SQL query to fetch address data',
        curl: 'curl -X POST -H "Content-Type: application/json" -H "X-API-Key: your-api-key" -d \'{"connectionString": "Server=localhost;Database=MyDB;User Id=user;Password=pass;TrustServerCertificate=True;", "sourceType": "query", "query": "SELECT TOP 3 Site_Address_1 as address FROM Mast_Site", "limit": 3}\' http://localhost:5001/api/v1/database/connect'
      },
      responseExample: {
        success: true,
        message: "Query executed successfully. Retrieved 3 records.",
        data: [
          { address: "123 Business Park Dr" },
          { address: "456 Technology Blvd" },
          { address: "789 Commerce Ave" }
        ],
        row_count: 3,
        columns: ["address"],
        query_executed: "SELECT TOP 3 Site_Address_1 as address FROM Mast_Site"
      }
    }
  ];

  const toggleAccordion = (id: string) => {
    setActiveAccordion(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };



  const downloadSample = async (sampleUrl: string, filename: string) => {
    try {
      await downloadSampleFile(sampleUrl, filename);
    } catch (error) {
      console.error('Failed to download sample file:', error);
      // Could add user notification here if needed
    }
  };

  const downloadDocumentationGuide = async (guideType: string, downloadName: string) => {
    try {
      await downloadDocGuideAPI(guideType, downloadName);
    } catch (error) {
      console.error('Failed to download documentation guide:', error);
      // Could add user notification here if needed
    }
  };

  return (
    <div className="modern-container">
      {/* Hero Section */}
      <div className="modern-hero">
        <div className="modern-hero-icon">🔗</div>
        <h1 className="modern-hero-title">Public API</h1>
        <p className="modern-hero-subtitle">Comprehensive API documentation and testing interface for all AddressIQ features</p>
      </div>

      {/* Main Card */}
      <div className="modern-card">
        {/* Info Cards */}
        <div className="modern-info-cards">
          <div className="modern-info-card modern-info-card-blue">
            <div className="modern-info-card-icon">📚</div>
            <div className="modern-info-card-content">
              <div className="modern-info-card-title">RESTful API Endpoints</div>
              <div className="modern-info-card-text">
                Access all AddressIQ features programmatically: standardize addresses, process files, compare data, and connect to databases.
              </div>
            </div>
          </div>
          <div className="modern-info-card modern-info-card-green">
            <div className="modern-info-card-icon">📥</div>
            <div className="modern-info-card-content">
              <div className="modern-info-card-title">Sample Files & Guides</div>
              <div className="modern-info-card-text">
                Download sample files and comprehensive Postman testing guides for each endpoint to get started quickly.
              </div>
            </div>
          </div>
        </div>

        <div className="api-endpoints">
        {apiEndpoints.map((endpoint) => (
          <div key={endpoint.id} className="api-accordion">
            <div 
              className={`accordion-header ${activeAccordion[endpoint.id] ? 'active' : ''}`}
              onClick={() => toggleAccordion(endpoint.id)}
            >
              <div className="accordion-title">
                <span className={`method-badge ${endpoint.method.toLowerCase()}`}>
                  {endpoint.method}
                </span>
                <h3>{endpoint.title}</h3>
              </div>
              <span className="accordion-icon">
                {activeAccordion[endpoint.id] ? '▼' : '▶'}
              </span>
            </div>

            {activeAccordion[endpoint.id] && (
              <div className="accordion-content">
                <div className="endpoint-info">
                  <p className="description">{endpoint.description}</p>
                  
                  <div className="endpoint-url">
                    <strong>Endpoint:</strong> 
                    <code>{endpoint.endpoint}</code>
                  </div>

                  <div className="parameters">
                    <h4>Parameters:</h4>
                    <ul>
                      {Object.entries(endpoint.parameters).map(([key, value]) => (
                        <li key={key}>
                          <code>{key}</code>: {value}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {endpoint.sampleDownload && (
                    <div className="sample-download">
                      <h4>Sample File:</h4>
                      <button 
                        className="sample-download-btn"
                        onClick={() => downloadSample(
                          endpoint.sampleDownload!, 
                          endpoint.id === 'file-upload' ? 'file-upload-sample.csv' : 'compare-upload-sample.csv'
                        )}
                      >
                        📥 Download Sample {endpoint.id === 'file-upload' ? 'Upload' : 'Compare'} File
                      </button>
                    </div>
                  )}

                  {endpoint.id === 'file-upload' && (
                    <div className="documentation-download">
                      <h4>📖 Postman Testing Guide:</h4>
                      <button 
                        className="documentation-download-btn"
                        onClick={() => downloadDocumentationGuide('file-upload', 'AddressIQ_API_Postman_Guide.docx')}
                        title="Download step-by-step Postman testing instructions"
                      >
                        📄 Download Postman API Guide (.docx)
                      </button>
                      <p className="documentation-description">
                        Complete step-by-step instructions for testing this API with Postman, including screenshots and troubleshooting tips.
                      </p>
                    </div>
                  )}

                  {endpoint.id === 'address-single' && (
                    <div className="documentation-download">
                      <h4>📖 Postman Testing Guide:</h4>
                      <button 
                        className="documentation-download-btn"
                        onClick={() => downloadDocumentationGuide('address-single', 'AddressIQ_Single_Address_API_Guide.docx')}
                        title="Download step-by-step Postman testing instructions for Single Address API"
                      >
                        📄 Download Address API Guide (.docx)
                      </button>
                      <p className="documentation-description">
                        Complete step-by-step instructions for testing the Single Address Standardization API with Postman, including screenshots and troubleshooting tips.
                      </p>
                    </div>
                  )}

                  {endpoint.id === 'address-batch' && (
                    <div className="documentation-download">
                      <h4>📖 Postman Testing Guide:</h4>
                      <button 
                        className="documentation-download-btn"
                        onClick={() => downloadDocumentationGuide('address-batch', 'AddressIQ_Batch_Address_API_Guide.docx')}
                        title="Download step-by-step Postman testing instructions for Batch Address API"
                      >
                        📄 Download Batch API Guide (.docx)
                      </button>
                      <p className="documentation-description">
                        Complete step-by-step instructions for testing the Batch Address Standardization API with Postman, including screenshots and troubleshooting tips.
                      </p>
                    </div>
                  )}

                  {endpoint.id === 'compare-upload' && (
                    <div className="documentation-download">
                      <h4>📖 Postman Testing Guide:</h4>
                      <button 
                        className="documentation-download-btn"
                        onClick={() => downloadDocumentationGuide('compare-upload', 'AddressIQ_Compare_Upload_API_Guide.docx')}
                        title="Download step-by-step Postman testing instructions for Compare Upload Processing API"
                      >
                        📄 Download Compare API Guide (.docx)
                      </button>
                      <p className="documentation-description">
                        Complete step-by-step instructions for testing the Compare Upload Processing API with Postman, including screenshots and troubleshooting tips.
                      </p>
                    </div>
                  )}

                  {endpoint.id === 'database-connect-table' && (
                    <div className="documentation-download">
                      <h4>📖 Postman Testing Guide:</h4>
                      <button 
                        className="documentation-download-btn"
                        onClick={() => downloadDocumentationGuide('database-table', 'AddressIQ_Database_Table_Mode_API_Guide.docx')}
                        title="Download step-by-step Postman testing instructions for Database Table Mode API"
                      >
                        📄 Download Database Table Mode Guide (.docx)
                      </button>
                      <p className="documentation-description">
                        Complete step-by-step instructions for testing the Database Connection Table Mode API with Postman, including screenshots and troubleshooting tips.
                      </p>
                    </div>
                  )}

                  {endpoint.id === 'database-connect-query' && (
                    <div className="documentation-download">
                      <h4>📖 Postman Testing Guide:</h4>
                      <button 
                        className="documentation-download-btn"
                        onClick={() => downloadDocumentationGuide('database-query', 'AddressIQ_Database_Query_Mode_API_Guide.docx')}
                        title="Download step-by-step Postman testing instructions for Database Query Mode API"
                      >
                        📄 Download Database Query Mode Guide (.docx)
                      </button>
                      <p className="documentation-description">
                        Complete step-by-step instructions for testing the Database Connection Query Mode API with Postman, including screenshots and troubleshooting tips.
                      </p>
                    </div>
                  )}

                  <div className="example-section">
                    <h4>Example Request:</h4>
                    <div className="code-block">
                      <pre>{endpoint.example.curl}</pre>
                    </div>
                  </div>

                  <div className="response-section">
                    <h4>Example Response:</h4>
                    <div className="code-block">
                      <pre>{JSON.stringify(endpoint.responseExample, null, 2)}</pre>
                    </div>
                  </div>


                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      </div>
    </div>
  );
};

export default PublicAPI;
