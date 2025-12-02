import React, { useCallback, useEffect, useRef, useState } from 'react';
import { uploadCompareFile, checkProcessingStatus, downloadFile, previewResultFile, downloadSampleFile, getAvailableModels, AIModel } from '../../services/api';
import '../FileUpload/FileUpload.css';
import './CompareUpload.css';

// Human-readable file size formatter to avoid showing 0.00 MB for small files
function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return '-';
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  const mb = kb / 1024;
  if (mb < 1024) return `${mb.toFixed(2)} MB`;
  const gb = mb / 1024;
  return `${gb.toFixed(2)} GB`;
}

const CompareUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{columns: string[]; rows: any[]; rowCount: number; page?: number; pageSize?: number; totalRows?: number} | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [loadingModels, setLoadingModels] = useState<boolean>(true);
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoadingModels(true);
        const { models, default_model } = await getAvailableModels();
        setAvailableModels(models);
        setSelectedModel(default_model);
      } catch (error) {
        console.error('Failed to fetch models:', error);
        // Set default fallback
        setAvailableModels([
          {
            id: 'gpt4omni',
            displayName: 'GPT-4 Omni',
            description: 'Advanced AI model for address standardization'
          }
        ]);
        setSelectedModel('gpt4omni');
      } finally {
        setLoadingModels(false);
      }
    };
    fetchModels();
  }, []);

  useEffect(() => {
    const done = ['completed', 'error'];
    const current = processingStatus?.status;
    if (processingId && !done.includes(current || '')) {
      if (!statusIntervalRef.current) {
        statusIntervalRef.current = setInterval(async () => {
          try {
            const st = await checkProcessingStatus(processingId);
            setProcessingStatus(st);
          } catch (e) {
            // ignore polling errors
          }
        }, 2000);
      }
    } else if (statusIntervalRef.current) {
      clearInterval(statusIntervalRef.current);
      statusIntervalRef.current = null;
    }
    return () => {
      if ((!processingId || done.includes(current || '')) && statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }
    };
  }, [processingId, processingStatus?.status]);

  useEffect(() => () => {
    if (statusIntervalRef.current) {
      clearInterval(statusIntervalRef.current);
      statusIntervalRef.current = null;
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!allowedExtensions.includes(ext)) {
      setError('Invalid file type. Please select a valid Excel (.xlsx, .xls) or CSV (.csv) file.');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setSelectedFile(file);
    setError(null);
    setUploadProgress(0);
    setProcessingId(null);
    setProcessingStatus(null);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile || !selectedModel) return;
    try {
      setUploading(true);
      setError(null);
      const res = await uploadCompareFile(selectedFile, selectedModel, (p) => setUploadProgress(p));
      setProcessingId(res.processing_id);
      setUploadProgress(100);
    } catch (e: any) {
      const errorMsg = e.message || 'Upload failed';
      setError(errorMsg);
      
      // Reset file if it's an empty file error or invalid headers
      if (errorMsg.toLowerCase().includes('no data rows') || 
          errorMsg.toLowerCase().includes('no columns') || 
          errorMsg.toLowerCase().includes('no records') ||
          errorMsg.toLowerCase().includes('missing required columns') ||
          errorMsg.toLowerCase().includes('invalid headers')) {
        // Auto-reset after showing error
        setTimeout(() => {
          setSelectedFile(null);
          setUploadProgress(0);
          if (fileInputRef.current) fileInputRef.current.value = '';
        }, 100);
      }
    } finally {
      setUploading(false);
    }
  }, [selectedFile, selectedModel]);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setUploading(false);
    setUploadProgress(0);
    setProcessingId(null);
    setProcessingStatus(null);
    setError(null);
    if (statusIntervalRef.current) {
      clearInterval(statusIntervalRef.current);
      statusIntervalRef.current = null;
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const handleDownload = useCallback(() => {
    if (processingStatus?.output_file) {
      downloadFile(processingStatus.output_file);
    }
  }, [processingStatus?.output_file]);

  const handleDownloadSample = useCallback(async () => {
    try {
      await downloadSampleFile('/v1/samples/compare-upload', 'compare-upload-sample.csv');
    } catch (error) {
      console.error('Failed to download sample file:', error);
    }
  }, []);

  // Load preview after completion
  useEffect(() => {
    const load = async () => {
      if (processingStatus?.status === 'completed' && processingStatus?.output_file) {
        try {
          const pv = await previewResultFile(processingStatus.output_file, page, pageSize);
          setPreview({ columns: pv.columns, rows: pv.rows, rowCount: pv.rowCount, page: pv.page, pageSize: pv.pageSize, totalRows: pv.totalRows });
        } catch (e: any) {
          // Non-fatal if preview fails
          setPreview(null);
          console.warn('Preview failed:', e?.message || e);
        }
      } else {
        setPreview(null);
      }
    };
    load();
  }, [processingStatus?.status, processingStatus?.output_file, page, pageSize]);

  const hiddenColumns = new Set(['method_used', 'timestamp', 'status', 'id']);

  const renderMatchLevel = (value: any) => {
    const raw = (value ?? '').toString().trim();
    const norm = raw.replace(/\s+/g, '_').replace(/-/g, '_').toUpperCase();
    const good = new Set(['VERY_LIKELY_SAME', 'EXACT_MATCH', 'LIKELY_SAME', 'HIGH_MATCH', 'STRONG_MATCH']);
    const mid = new Set(['DIFFERENT_BUT_NEARBY', 'POSSIBLE_MATCH', 'PARTIAL_MATCH', 'MEDIUM_MATCH', 'NEARBY']);
    const bad = new Set(['NO_MATCH', 'LOW_CONFIDENCE_MATCH', 'MISMATCH', 'NONE']);
    let cls = 'match-neutral';
    if (good.has(norm)) cls = 'match-good';
    else if (mid.has(norm)) cls = 'match-mid';
    else if (bad.has(norm)) cls = 'match-bad';

    const displayMap: Record<string, string> = {
      NO_MATCH: 'NO MATCH',
      DIFFERENT_BUT_NEARBY: 'DIFFERENT BUT NEARBY',
      VERY_LIKELY_SAME: 'VERY LIKELY SAME',
      LIKELY_SAME: 'LIKELY SAME',
      POSSIBLE_MATCH: 'POSSIBLE MATCH',
      EXACT_MATCH: 'EXACT MATCH',
      PARTIAL_MATCH: 'PARTIAL MATCH',
      LOW_CONFIDENCE_MATCH: 'LOW CONFIDENCE MATCH',
    };
    const display = displayMap[norm] || raw.replace(/_/g, ' ').toUpperCase();

    return (
      <span className={`pill ${cls}`} title={display}>
        <span className="dot" />
        <span className="match-label">{display}</span>
      </span>
    );
  };

  const renderConfidence = (value: any) => {
    const n = typeof value === 'number' ? value : parseFloat(value);
    const pct = isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
    const color = pct >= 80 ? '#16a34a' : pct >= 50 ? '#f59e0b' : '#ef4444';
    return (
      <div className="confidence" title={`${pct}% confidence`}>
        <div className="bar-bg">
          <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
        </div>
        <span className="bar-label" style={{ color }}>{isNaN(pct) ? String(value ?? '-') : `${pct}%`}</span>
      </div>
    );
  };

  const isProcessing = processingStatus && ['uploaded', 'processing'].includes(processingStatus.status);
  const isCompleted = processingStatus?.status === 'completed';
  const hasError = processingStatus?.status === 'error' || !!error;
  const steps = processingStatus?.steps || [];
  const currentProgress = processingStatus?.progress || 0;
  const recentLogs = (processingStatus?.logs || []).slice(-5).reverse();

  return (
    <div className="file-upload-container">
      <div className="file-upload-card">
        <h1>Batch Compare Upload</h1>
        <p>Upload your Excel (.xlsx, .xls) or CSV (.csv) file to run address comparison. The transformed file will be available to download.</p>
        
        <div className="info-note" style={{ 
          background: '#e3f2fd', 
          border: '1px solid #2196f3', 
          borderRadius: '8px', 
          padding: '12px 16px', 
          margin: '16px 0',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px'
        }}>
          <span style={{ color: '#1976d2', fontSize: '20px', fontWeight: 'bold' }}>ℹ️</span>
          <div style={{ flex: 1 }}>
            <strong style={{ color: '#1565c0', display: 'block', marginBottom: '4px' }}>Processing Information</strong>
            <span style={{ color: '#424242', fontSize: '14px' }}>
              Records are processed in batches of 5 for optimal performance. Your entire file will be processed regardless of size, 
              but the comparison operations are performed on 5 records at a time. Processing time varies and directly depends upon the number of records in your file.
            </span>
          </div>
        </div>

        <div className="info-note" style={{ 
          background: '#fff3e0', 
          border: '1px solid #ff9800', 
          borderRadius: '8px', 
          padding: '12px 16px', 
          margin: '16px 0',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px'
        }}>
          <span style={{ color: '#f57c00', fontSize: '20px', fontWeight: 'bold' }}>⚠️</span>
          <div style={{ flex: 1 }}>
            <strong style={{ color: '#e65100', display: 'block', marginBottom: '4px' }}>Required File Headers</strong>
            <span style={{ color: '#424242', fontSize: '13px' }}>
              Your file must contain these columns (case-insensitive): 
              <strong> Site_Name, Site_Address_1, Site_Address_2, Site_Address_3, Site_Address_4, 
              Site_City, Site_State, Site_Postcode, Site_Country</strong>. Download the sample file to see the correct format.
            </span>
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <button 
            onClick={handleDownloadSample}
            style={{ 
              background: 'none',
              border: 'none',
              color: '#1976d2', 
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              padding: 0,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
            onMouseOver={(e) => e.currentTarget.style.textDecoration = 'underline'}
            onMouseOut={(e) => e.currentTarget.style.textDecoration = 'none'}
          >
            📥 Download Sample Compare File
          </button>
        </div>

        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              ref={fileInputRef}
              type="file"
              id="compare-file-input"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileSelect}
              onClick={(e) => { (e.currentTarget as HTMLInputElement).value = ''; }}
              disabled={uploading}
              className="file-input"
            />
            <label htmlFor="compare-file-input" className="file-input-label">
              {selectedFile ? selectedFile.name : 'Choose Excel or CSV File'}
            </label>
          </div>

          {selectedFile && (
            <div className="file-info">
              <p><strong>File:</strong> {selectedFile.name}</p>
              <p><strong>Size:</strong> {formatFileSize(selectedFile.size)}</p>
            </div>
          )}

          {/* Model Selection - Modern Inline Design */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px',
            padding: '8px 12px',
            background: '#f8f9fa',
            borderRadius: '6px',
            border: '1px solid #e9ecef'
          }}>
            <span style={{ 
              fontSize: '16px',
              lineHeight: '1'
            }}>🤖</span>
            <span style={{ 
              fontSize: '12px', 
              color: '#6c757d',
              fontWeight: '500',
              whiteSpace: 'nowrap'
            }}>Model:</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={uploading || !!isProcessing || loadingModels}
              style={{
                flex: 1,
                padding: '4px 8px',
                fontSize: '12px',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                backgroundColor: uploading || !!isProcessing ? '#e9ecef' : 'white',
                cursor: uploading || !!isProcessing || loadingModels ? 'not-allowed' : 'pointer',
                color: '#212529',
                fontWeight: '500',
                outline: 'none',
                transition: 'all 0.2s ease',
                appearance: 'none',
                backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'12\' height=\'12\' viewBox=\'0 0 12 12\'%3E%3Cpath fill=\'%23495057\' d=\'M6 9L1 4h10z\'/%3E%3C/svg%3E")',
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 8px center',
                paddingRight: '30px'
              }}
              onMouseEnter={(e) => { 
                if (!uploading && !isProcessing && !loadingModels) {
                  e.currentTarget.style.borderColor = '#adb5bd';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(0,123,255,0.1)';
                }
              }}
              onMouseLeave={(e) => { 
                e.currentTarget.style.borderColor = '#dee2e6';
                e.currentTarget.style.boxShadow = 'none';
              }}
              onFocus={(e) => { 
                if (!uploading && !isProcessing) {
                  e.currentTarget.style.borderColor = '#007bff';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(0,123,255,0.15)';
                }
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#dee2e6';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              {loadingModels ? (
                <option>Loading...</option>
              ) : (
                availableModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.displayName}
                  </option>
                ))
              )}
            </select>
          </div>

          <div className="button-group">
            <button onClick={handleUpload} disabled={!selectedFile || uploading || !!isProcessing} className="upload-button">
              {uploading ? 'Uploading...' : isProcessing ? 'Processing...' : 'Upload & Compare'}
            </button>
            <button onClick={handleReset} disabled={uploading} className="reset-button">Reset</button>
            {isCompleted && processingStatus?.output_file && (
              <button onClick={handleDownload} className="download-button">Download Result</button>
            )}
          </div>

          {/* Guidance message for async processing */}
          {isProcessing && (
            <div className="guidance-message">
              💡 <strong>Tip:</strong> You can click Reset and continue processing other files. Completed files will appear in Processing History.
            </div>
          )}

          {(uploading || isProcessing) && (
            <div className="progress-section">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${isProcessing ? processingStatus?.progress || 0 : uploadProgress}%` }} />
              </div>
              <p>
                {isProcessing ? `${processingStatus?.progress || 0}% - ${processingStatus?.message || 'Processing...'}` : `${uploadProgress}% uploaded`}
              </p>
              {steps.length > 0 && (
                <div className="steps-wrapper">
                  <div className="steps">
                    {steps.map((s: any) => {
                      const reached = currentProgress >= s.target;
                      return (
                        <div key={s.name} className={`step ${reached ? 'done' : ''}`}>
                          <div className="step-marker">{reached ? '✓' : ''}</div>
                          <div className="step-label">{s.label}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {processingStatus?.file_info && (
                <div className="file-meta">
                  <small>Rows: {processingStatus.file_info.rows} | Columns: {processingStatus.file_info.columns}</small>
                </div>
              )}
              {recentLogs.length > 0 && (
                <div className="logs">
                  <small><strong>Recent activity:</strong></small>
                  <ul>
                    {recentLogs.map((l: any) => (
                      <li key={l.ts}>{new Date(l.ts).toLocaleTimeString()} - {l.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {isCompleted && (
            <div className="result success">
              <h3>Comparison Complete!</h3>
              <p>{processingStatus?.message}</p>
              {processingStatus?.output_file && (
                <div className="output-file-row">
                  <span className="output-file-label">Output file:</span>
                  <span
                    className="output-file-name"
                    title={processingStatus.output_file}
                  >
                    {processingStatus.output_file}
                  </span>
                </div>
              )}
            </div>
          )}

          {isCompleted && preview && preview.rows?.length > 0 && (
            <div className="preview-card">
              <div className="preview-header">
                <h3 className="preview-title">Result Preview</h3>
              </div>
              {/* pager moved below table */}
              <div className="table-wrapper">
                <table className="result-table">
                  <thead>
                    <tr>
                      <th className="col-index" style={{ width: 80, minWidth: 60, maxWidth: 100 }}>
                        <div className="th-wrap">#</div>
                      </th>
                      {preview.columns.filter(c => !hiddenColumns.has(String(c).toLowerCase())).map((c) => {
                        const key = String(c);
                        const labels: Record<string, string> = {
                          original_address_1: 'Original Address 1',
                          original_address_2: 'Original Address 2',
                          standardized_address_1: 'Standardized Address 1',
                          standardized_address_2: 'Standardized Address 2',
                          match_level: 'Match Level',
                          confidence_score: 'Confidence Score',
                          analysis: 'Analysis',
                        };
                        const label = labels[key.toLowerCase()] || key;
                        const narrow = ['match_level', 'confidence_score'].includes(key.toLowerCase());
                        const style: React.CSSProperties = narrow ? { width: 180, minWidth: 180, maxWidth: 220 } : { width: 360, minWidth: 280 };
                        return (
                          <th key={key} style={style}><div className="th-wrap">{label}</div></th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row, idx) => (
                      <tr key={idx}>
                        <td className="col-index" style={{ width: 80, minWidth: 60, maxWidth: 100 }}>
                          <div className="cell-wrap">{(page - 1) * pageSize + idx + 1}</div>
                        </td>
                        {preview.columns.filter(c => !hiddenColumns.has(String(c).toLowerCase())).map((c) => {
                          const key = String(c);
                          const val = row[key];
                          const keyLc = key.toLowerCase();
                          const narrow = ['match_level', 'confidence_score'].includes(keyLc);
                          const style: React.CSSProperties = narrow ? { width: 180, minWidth: 180, maxWidth: 220 } : { width: 360, minWidth: 280 };
                          if (keyLc === 'match_level') return <td key={key} style={style}><div className="cell-wrap">{renderMatchLevel(val)}</div></td>;
                          if (keyLc === 'confidence_score') return <td key={key} style={style}><div className="cell-wrap">{renderConfidence(val)}</div></td>;
                          return <td key={key} style={style}><div className="cell-wrap" title={val}>{String(val ?? '')}</div></td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="preview-footer">
                <div className="pager">
                  <div className="pager-left">
                    <button className="pager-btn" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>Prev</button>
                    <span className="pager-text">Page {page} of {Math.max(1, Math.ceil((preview.totalRows || 0) / pageSize))}</span>
                    <button className="pager-btn" onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil((preview.totalRows || 0) / pageSize)}>Next</button>
                  </div>
                  <div className="pager-right">
                    <label className="pager-label">Rows per page&nbsp;
                      <select className="pager-select" value={pageSize} onChange={(e) => { setPage(1); setPageSize(parseInt(e.target.value, 10)); }}>
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                        <option value={200}>200</option>
                      </select>
                    </label>
                  </div>
                </div>
                <div className="preview-note">Showing {preview.rowCount} rows • Total {preview.totalRows ?? (page * pageSize)} • Page {page}. Scroll horizontally to see more columns.</div>
              </div>
            </div>
          )}

          {hasError && (
            <div className="result error">
              <h3>Error</h3>
              <p>{error || processingStatus?.error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompareUpload;
