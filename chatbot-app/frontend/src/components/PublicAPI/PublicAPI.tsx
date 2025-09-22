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
      id: 'database-connect',
      title: 'Database Connection & Processing',
      description: 'Connect to external databases and process address data',
      method: 'POST',
      endpoint: '/api/v1/database/connect',
      parameters: {
        server: 'Database server address',
        database: 'Database name',
        query: 'SQL query to fetch addresses',
        limit: 'Maximum number of records (optional, default: 10)'
      },
      example: {
        description: 'Connect to database and process addresses',
        curl: 'curl -X POST -H "Content-Type: application/json" -d \'{"server": "localhost", "database": "addresses_db", "query": "SELECT address FROM customers LIMIT 100"}\' http://localhost:5001/api/v1/database/connect'
      },
      responseExample: {
        success: true,
        processing_id: "789e1234-e89b-12d3-a456-426614174002",
        status: "queued",
        message: "Database processing started successfully"
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
