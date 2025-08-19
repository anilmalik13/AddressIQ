import React, { useEffect, useMemo, useState } from 'react';
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

// Canonical order for address components displayed and in response preview
const COMPONENT_ORDER = [
  'street_number',
  'street_name',
  'city',
  'state',
  'postal_code',
  'country',
  'latitude',
  'longitude',
];

const PublicAPI: React.FC = () => {
  const [addresses, setAddresses] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resultsOpen, setResultsOpen] = useState(false);
  const [responseOpen, setResponseOpen] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [apiVersion, setApiVersion] = useState<string | null>(null);
  const [responseCount, setResponseCount] = useState<number | null>(null);

  const list = useMemo(() => addresses.split(/\r?\n/).map(a => sanitize(a.trim())).filter(Boolean), [addresses]);

  // Fixed sample endpoint (HTTP GET) per request
  const fixedEndpoint = 'http://localhost:5001/api/public/standardize?address=123%20Main%20St%2C%20NYC';

  const onCall = async () => {
    if (!list.length) return;
    setLoading(true); 
    setError(null); 
    setResults(null);
    try {
      const res: any = await processPublicStandardize(list);
      setResults(res.results || []);
      setRequestId(res.request_id || null);
      setApiVersion(res.api_version || null);
      setResponseCount(typeof res.count === 'number' ? res.count : null);
      setResultsOpen(true); // auto-open results when available
    } catch (e: any) {
      setError(e.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (results && results.length > 0) {
      setResultsOpen(true);
    }
  }, [results]);

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

  const getConfidenceChipClass = (confidence: string) => {
    const c = (confidence || '').toLowerCase();
    switch (c) {
      case 'high': return 'confidence-chip high';
      case 'medium': return 'confidence-chip medium';
      case 'low': return 'confidence-chip low';
      default: return 'confidence-chip';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    const c = (confidence || '').toLowerCase();
    switch (c) {
      case 'high':
        // Shield with check
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        );
      case 'medium':
        // Gauge / speedometer
  return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 14v-4" />
            <path d="M8 14.5a4 4 0 0 1 8 0" />
            <path d="M5 20a10.94 10.94 0 0 1 14 0" />
            <path d="M12 3v2" />
            <path d="m4.93 6.93 1.41 1.41" />
            <path d="M3 13h2" />
            <path d="m18.07 8.34 1.41-1.41" />
            <path d="M19 13h2" />
          </svg>
        );
      case 'low':
        // Triangle warning
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
            <path d="M12 9v5" />
            <path d="M12 17h.01" />
          </svg>
        );
      default:
        // Dot
        return (
          <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="6" /></svg>
        );
    }
  };

  // Build a dynamic response preview that mirrors the backend response and uses real request_id
  const responsePreview = useMemo(() => {
    // Fallback example when no results yet
    const fallback = {
    request_id: requestId || 'unknown',
      count: 1,
    results: [
        {
          original: '123 Main St, NYC',
          formatted: '123 Main Street, New York, NY',
          components: {
            street_number: '123',
            street_name: 'Main Street',
            city: 'New York',
            state: 'NY',
            postal_code: '',
            country: 'USA',
            latitude: '',
            longitude: '',
          },
          confidence: 'high',
          status: 'success',
          source: 'azure_openai',
      error: null,
        },
      ],
    api_version: apiVersion || 'v1',
    };

    if (!results || results.length === 0) {
      return JSON.stringify(fallback, null, 2);
    }

  const mapped = results.map((r: any) => {
      const comps = (r?.components ?? {}) as Record<string, any>;
      const orderedComps: Record<string, any> = {};
      COMPONENT_ORDER.forEach(k => {
        if (k in comps) orderedComps[k] = comps[k];
      });
      Object.keys(comps)
        .filter(k => !COMPONENT_ORDER.includes(k))
        .sort()
        .forEach(k => {
          orderedComps[k] = comps[k];
        });
      return {
        original: r?.original ?? '',
        formatted: r?.formatted ?? '',
        components: orderedComps,
        confidence: r?.confidence ?? '',
        status: r?.status ?? '',
        source: r?.source ?? '',
        error: r?.error ?? null,
      };
    });

    const preview = {
      request_id: requestId || 'unknown',
      count: typeof responseCount === 'number' ? responseCount : results.length,
      results: mapped,
      api_version: apiVersion || 'v1',
    };

    return JSON.stringify(preview, null, 2);
  }, [results, requestId, apiVersion, responseCount]);

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
            
            {/* Endpoint first */}
            <div className="form-group">
              <label className="form-label">Endpoint (HTTP GET)</label>
              <div className="endpoint-row">
                <input className="form-input endpoint-input" type="text" value={fixedEndpoint} disabled readOnly aria-label="Public API endpoint URL" />
                <button className="btn btn-secondary" onClick={() => copy(fixedEndpoint)}>Copy</button>
              </div>
            </div>

            {/* Addresses input next */}
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
                  setResultsOpen(false);
                  setRequestId(null);
                  setApiVersion(null);
                  setResponseCount(null);
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
          </div>

          {/* Accordions */}
          <div className="accordion">
            {/* Results Accordion */}
            <div className="accordion-item">
              <button className="accordion-header" onClick={() => setResultsOpen(o => !o)} aria-expanded={resultsOpen}>
                <span>Results{results && results.length ? ` (${results.length})` : ''}</span>
                <span className={`accordion-icon ${resultsOpen ? 'open' : ''}`}>▸</span>
              </button>
              {resultsOpen && (
                <div className="accordion-panel">
                  {results && results.length > 0 ? (
                    <div className="results-section" style={{marginTop: 0, borderTop: 'none', paddingTop: 0}}>
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
                        <span className="status-wrapper">
                          <span className={getStatusChipClass(result.status)}>
                            {result.status}
                          </span>
                        </span>
                        <span className="confidence-wrapper">
                          <span
                            className={getConfidenceChipClass(result.confidence)}
                            title={`Confidence level: ${result.confidence}`}
                            aria-label={`Confidence level ${result.confidence}`}
                          >
                            {getConfidenceIcon(result.confidence)}
                            <span>{result.confidence}</span>
                          </span>
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
                                {(() => {
                                  const comps = (result.components ?? {}) as Record<string, any>;
                                  const orderedKeys = [
                                    ...COMPONENT_ORDER.filter(k => k in comps),
                                    ...Object.keys(comps).filter(k => !COMPONENT_ORDER.includes(k)).sort(),
                                  ];
                                  return orderedKeys.map((key) => (
                            <div key={key} className="component-item">
                              <span className="component-key">{key.replace(/_/g, ' ')}</span>
                                      <span className="component-value">{String(comps[key] ?? '') || '—'}</span>
                            </div>
                                  ));
                                })()}
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
                  ) : (
                    <div className="no-results">No results found. Enter the address in the above field to see the results.</div>
                  )}
              </div>
            )}
          </div>

            {/* Response Format Accordion */}
            <div className="accordion-item">
              <button className="accordion-header" onClick={() => setResponseOpen(o => !o)} aria-expanded={responseOpen}>
                <span>Response Format</span>
                <span className={`accordion-icon ${responseOpen ? 'open' : ''}`}>▸</span>
              </button>
              {responseOpen && (
                <div className="accordion-panel">
            <div className="response-format">
                    <div className="code-block response-example">{responsePreview}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicAPI;
