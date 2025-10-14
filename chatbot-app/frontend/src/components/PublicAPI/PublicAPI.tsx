import React, { useState } from 'react';
import './PublicAPI.css';

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
  const [testResults, setTestResults] = useState<{ [key: string]: any }>({});
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});

  const apiEndpoints: APIEndpoint[] = [
    {
      id: 'file-upload',
      title: 'File Upload & Processing', 
      description: 'Upload Excel/CSV files for address standardization and processing',
      method: 'POST',
      endpoint: '/api/v1/files/upload',
      parameters: {
        file: 'File (Excel/CSV)',
        options: 'Processing options (optional)'
      },
      example: {
        description: 'Upload a file using multipart/form-data',
        curl: 'curl -X POST -F "file=@addresses.xlsx" http://localhost:5001/api/v1/files/upload'
      },
      responseExample: {
        success: true,
        processing_id: "123e4567-e89b-12d3-a456-426614174000",
        filename: "addresses_20230922_143022.xlsx",
        file_size: 45632,
        status: "queued",
        message: "File uploaded successfully and processing started"
      },
      sampleDownload: '/api/v1/samples/file-upload'
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
        results: []
      }
    },
    {
      id: 'compare-upload',
      title: 'Compare Upload Processing',
      description: 'Upload files for address comparison and analysis',
      method: 'POST',
      endpoint: '/api/v1/compare/upload',
      parameters: {
        file: 'File for comparison processing',
        options: 'Comparison options (optional)'
      },
      example: {
        description: 'Upload a file for comparison',
        curl: 'curl -X POST -F "file=@compare_addresses.csv" http://localhost:5001/api/v1/compare/upload'
      },
      responseExample: {
        success: true,
        processing_id: "456e7890-e89b-12d3-a456-426614174001",
        filename: "compare_addresses_20230922_143025.csv",
        status: "queued",
        message: "Comparison file uploaded successfully"
      },
      sampleDownload: '/api/v1/samples/compare-upload'
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
        columnNames: 'Array of column names to fetch (required, at least one)',
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
        query: 'Custom SQL query to execute (required)',
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

  const testEndpoint = async (endpoint: APIEndpoint) => {
    setLoading(prev => ({ ...prev, [endpoint.id]: true }));
    
    try {
      let requestData: any = {};
      let requestMethod = endpoint.method;
      let requestUrl = `http://localhost:5001${endpoint.endpoint}`;
      let headers: any = {};

      switch (endpoint.id) {
        case 'address-single':
          requestData = { address: "123 Main Street, New York, NY 10001" };
          headers['Content-Type'] = 'application/json';
          break;
        case 'address-batch':
          requestData = { 
            addresses: [
              "123 Main Street, New York, NY 10001",
              "456 Oak Avenue, Los Angeles, CA 90210"
            ]
          };
          headers['Content-Type'] = 'application/json';
          break;
        case 'database-connect':
          requestData = {
            server: "test-server",
            database: "test-db",
            query: "SELECT address FROM test_table LIMIT 5",
            limit: 5
          };
          headers['Content-Type'] = 'application/json';
          break;
        case 'file-upload':
        case 'compare-upload':
          setTestResults(prev => ({
            ...prev,
            [endpoint.id]: {
              note: "File upload testing requires actual file selection. Use the cURL example or upload a file through the interface.",
              example_response: endpoint.responseExample
            }
          }));
          return;
      }

      const response = await fetch(requestUrl, {
        method: requestMethod,
        headers: headers,
        body: JSON.stringify(requestData)
      });

      const result = await response.json();
      setTestResults(prev => ({
        ...prev,
        [endpoint.id]: {
          status: response.status,
          response: result
        }
      }));

    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [endpoint.id]: {
          error: `Request failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [endpoint.id]: false }));
    }
  };

  const downloadSample = (sampleUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.href = `http://localhost:5001${sampleUrl}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadDocumentation = () => {
    const link = document.createElement('a');
    link.href = 'http://localhost:5001/api/v1/docs/download';
    link.download = 'AddressIQ_API_Postman_Guide.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadAddressGuide = () => {
    const link = document.createElement('a');
    link.href = 'http://localhost:5001/api/v1/docs/download-address-guide';
    link.download = 'AddressIQ_Single_Address_API_Guide.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadBatchGuide = () => {
    const link = document.createElement('a');
    link.href = 'http://localhost:5001/api/v1/docs/download-batch-guide';
    link.download = 'AddressIQ_Batch_Address_API_Guide.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadCompareGuide = () => {
    const link = document.createElement('a');
    link.href = 'http://localhost:5001/api/v1/docs/download-compare-guide';
    link.download = 'AddressIQ_Compare_Upload_API_Guide.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadDatabaseTableGuide = () => {
    const link = document.createElement('a');
    link.href = 'http://localhost:5001/api/v1/docs/download-database-table-guide';
    link.download = 'AddressIQ_Database_Table_Mode_API_Guide.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadDatabaseQueryGuide = () => {
    const link = document.createElement('a');
    link.href = 'http://localhost:5001/api/v1/docs/download-database-query-guide';
    link.download = 'AddressIQ_Database_Query_Mode_API_Guide.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="public-api-container">
      <div className="api-header">
        <h1>🔗 AddressIQ Public API</h1>
        <p className="api-description">
          Comprehensive API documentation and testing interface for all AddressIQ features. 
          Standardize addresses, process files, compare data, and connect to databases programmatically.
        </p>
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
                        onClick={downloadDocumentation}
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
                        onClick={downloadAddressGuide}
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
                        onClick={downloadBatchGuide}
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
                        onClick={downloadCompareGuide}
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
                        onClick={downloadDatabaseTableGuide}
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
                        onClick={downloadDatabaseQueryGuide}
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

                  <div className="test-section">
                    <button 
                      className="test-button"
                      onClick={() => testEndpoint(endpoint)}
                      disabled={loading[endpoint.id]}
                    >
                      {loading[endpoint.id] ? 'Testing...' : 'Test This Endpoint'}
                    </button>
                    
                    {testResults[endpoint.id] && (
                      <div className="test-results">
                        <h5>Test Results:</h5>
                        <div className="code-block">
                          <pre>{JSON.stringify(testResults[endpoint.id], null, 2)}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PublicAPI;
