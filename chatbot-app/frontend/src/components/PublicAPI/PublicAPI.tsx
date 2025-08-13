import React, { useMemo, useState } from 'react';
import './PublicAPI.css';
import { processPublicStandardize } from '../../services/api';

const sanitize = (s: string) => {
  let out = '';
  for (let i = 0; i < s.length; i++) {
    const code = s.charCodeAt(i);
    const ch = s[i];
    // Strip control chars except tab/newline (so multi-line input works)
    if (code < 32 && ch !== '\t' && ch !== '\n' && ch !== '\r') {
      out += ' ';
    } else {
      out += ch;
    }
  }
  out = out.replace(/[<>]/g, ' ');
  if (out.length > 500) out = out.slice(0, 500);
  return out;
};

const PublicAPI: React.FC = () => {
  const [addresses, setAddresses] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const list = useMemo(() => addresses.split(/\r?\n/).map(a => sanitize(a.trim())).filter(Boolean), [addresses]);

  const onCall = async () => {
    if (!list.length) return;
    setLoading(true); 
    setError(null); 
    setResults(null);
    try {
      const res = await processPublicStandardize(list);
      setResults(res.results || []);
    } catch (e: any) {
      setError(e.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusChipClass = (status: string) => {
    switch (status) {
      case 'success': return 'status-chip success';
      case 'fallback': return 'status-chip fallback';
      case 'error': return 'status-chip error';
      default: return 'status-chip';
    }
  };

  return (
    <div className="publicapi-container">
      <div className="publicapi-card">
        <div className="publicapi-header">
          <h1>Public Address Standardization API</h1>
          <p>Submit one or more unformatted addresses and get standardized addresses with individual address components.</p>
        </div>

        <div className="publicapi-content">
          <div className="input-section">
            <div className="section-title">Try the API</div>
            
            <div className="form-group">
              <label className="form-label">Enter addresses (one per line)</label>
              <textarea
                className="form-input form-textarea"
                placeholder="123 Main St, NYC, NY&#10;BPTP Capital City, Noida&#10;Another address..."
                value={addresses}
                onChange={e => setAddresses(e.target.value)}
                rows={6}
              />
            </div>

            <div className="button-group">
              <button 
                className="btn btn-primary" 
                onClick={onCall} 
                disabled={!list.length || loading}
              >
                {loading ? 'Processing...' : 'Standardize Addresses'}
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={() => {
                  setAddresses(''); 
                  setResults(null); 
                  setError(null);
                }}
              >
                Clear
              </button>
              <span className="help-text">
                {list.length} address(es) ready to process
              </span>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {/* Results */}
            {results && results.length > 0 && (
              <div className="results-section">
                <div className="section-title">Results ({results.length})</div>
                <div className="results-grid">
                  {results.map((result, index) => (
                    <div key={index} className="result-card">
                      <div className="result-header">
                        <span className="result-number">Address #{index + 1}</span>
                        <div className="copy-buttons">
                          <button className="btn-copy" onClick={() => copy(result.original)}>
                            Copy Original
                          </button>
                          <button className="btn-copy" onClick={() => copy(result.formatted)}>
                            Copy Formatted
                          </button>
                          <button className="btn-copy" onClick={() => copy(JSON.stringify(result.components))}>
                            Copy JSON
                          </button>
                        </div>
                      </div>

                      <div className="status-chips">
                        <span className={getStatusChipClass(result.status)}>
                          {result.status}
                        </span>
                        <span className="status-chip">
                          {result.source}
                        </span>
                        <span className="status-chip">
                          {result.confidence}
                        </span>
                      </div>

                      <div className="address-comparison">
                        <div className="address-row">
                          <span className="address-label">Original</span>
                          <span className="address-value">{result.original}</span>
                        </div>
                        <div className="address-row">
                          <span className="address-label">Standardized</span>
                          <span className="address-value formatted">{result.formatted}</span>
                        </div>
                      </div>

                      <div className="components-section">
                        <div className="components-title">Address Components</div>
                        <div className="components-grid">
                          {Object.entries(result.components).map(([key, value]) => (
                            <div key={key} className="component-item">
                              <span className="component-key">{key.replace(/_/g, ' ')}</span>
                              <span className="component-value">{String(value) || '—'}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {result.error && (
                        <div className="error-row">
                          <span className="error-label">Error</span>
                          <span className="error-value">{result.error}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Documentation Section */}
          <div className="docs-section">
            <div className="section-title">Response Format</div>
            <div className="response-format">
              <div className="code-block response-example">{`{
  "request_id": "unique-uuid",
  "count": 2,
  "api_version": "v1",
  "results": [
    {
      "original": "123 Main St, NYC",
      "formatted": "123 Main Street, New York, NY",
      "components": {
        "street_number": "123",
        "street_name": "Main Street", 
        "city": "New York",
        "state": "NY",
        "postal_code": "",
        "country": "USA",
        "latitude": "",
        "longitude": ""
      },
      "confidence": "high",
      "status": "success",
      "source": "azure_openai"
    }
  ]
}`}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicAPI;
