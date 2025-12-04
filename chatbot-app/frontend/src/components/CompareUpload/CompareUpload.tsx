import React, { useCallback, useEffect, useRef, useState } from 'react';
import { uploadCompareFile, checkProcessingStatus, downloadFile, previewResultFile, downloadSampleFile, getAvailableModels, AIModel } from '../../services/api';
import '../../styles/shared.css';
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
    if (!selectedFile) return;
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
    <div className="modern-container">
      {/* Hero Section */}
      <div className="modern-hero">
        <div className="modern-hero-icon">⚖️</div>
        <h1 className="modern-hero-title">Batch Compare Upload</h1>
        <p className="modern-hero-subtitle">Upload your file to run intelligent address comparison and standardization</p>
      </div>

      {/* Main Card */}
      <div className="modern-card">
        {/* Info Cards Grid */}
        <div className="modern-info-cards">
          <div className="modern-info-card modern-info-card-blue">
            <div className="modern-info-card-icon">📊</div>
            <div className="modern-info-card-content">
              <div className="modern-info-card-title">Batch Processing</div>
              <div className="modern-info-card-text">Records processed in batches of 5 for optimal performance and accuracy</div>
            </div>
          </div>
          
          <div className="modern-info-card modern-info-card-amber">
            <div className="modern-info-card-icon">📋</div>
            <div className="modern-info-card-content">
              <div className="modern-info-card-title">Required Headers</div>
              <div className="modern-info-card-text">Site_Name, Site_Address_1-4, Site_City, Site_State, Site_Postcode, Site_Country</div>
            </div>
          </div>
        </div>

        {/* Sample Download Section */}
        <div className="sample-download-section">
          <button onClick={handleDownloadSample} className="sample-download-btn">
            <span className="sample-icon">📥</span>
            Download Sample File
          </button>
          <span className="sample-help-text">See the required format</span>
        </div>

        {/* AI Model Selector */}
        <div className="model-selector-card">
          <div className="model-selector-header">
            <span className="model-icon">🤖</span>
            <span className="model-label">AI Model</span>
          </div>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={uploading || !!isProcessing || loadingModels}
            className="model-select"
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
          <p className="model-coming-soon">💡 Additional AI models coming soon</p>
        </div>

        {/* Upload Area */}
        <div className="upload-area">
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
          <label htmlFor="compare-file-input" className="file-upload-zone">
            {!selectedFile ? (
              <>
                <div className="upload-icon">📁</div>
                <div className="upload-text-primary">Choose your file</div>
                <div className="upload-text-secondary">Drag & drop or click to browse (.xlsx, .xls, .csv)</div>
              </>
            ) : (
              <div className="selected-file-display">
                <div className="file-icon">📄</div>
                <div className="file-details">
                  <div className="file-name">{selectedFile.name}</div>
                  <div className="file-size">{formatFileSize(selectedFile.size)}</div>
                </div>
                <div className="file-checkmark">✓</div>
              </div>
            )}
          </label>
        </div>

        {/* Action Buttons */}
        <div className="action-buttons">
          <button 
            onClick={handleUpload} 
            disabled={!selectedFile || uploading || !!isProcessing} 
            className="modern-btn modern-btn-primary"
          >
            {uploading && <span className="modern-btn-spinner" />}
            <span>{uploading ? 'Uploading...' : isProcessing ? 'Processing...' : 'Upload & Compare'}</span>
          </button>
          
          <button 
            onClick={handleReset} 
            disabled={uploading} 
            className="modern-btn modern-btn-gray"
          >
            Reset
          </button>
          
          {isCompleted && processingStatus?.output_file && (
            <button onClick={handleDownload} className="modern-btn modern-btn-success">
              <span>📥</span>
              Download Result
            </button>
          )}
        </div>

        {/* Processing Tip */}
        {isProcessing && (
          <div className="processing-tip">
            <span className="tip-icon">💡</span>
            <div className="tip-text">
              <strong>Tip:</strong> You can click Reset and continue processing other files. Completed files will appear in Processing History.
            </div>
          </div>
        )}

        {/* Progress Section */}
        {(uploading || isProcessing) && (
          <div className="progress-card">
            <div className="progress-header">
              <span className="progress-title">
                {isProcessing ? 'Processing Your File' : 'Uploading File'}
              </span>
              <span className="progress-percentage">
                {isProcessing ? `${processingStatus?.progress || 0}%` : `${uploadProgress}%`}
              </span>
            </div>
            <div className="modern-progress">
              <div 
                className="modern-progress-fill" 
                style={{ width: `${isProcessing ? processingStatus?.progress || 0 : uploadProgress}%` }}
              />
            </div>
            <p className="progress-message">
              {isProcessing ? processingStatus?.message || 'Processing records...' : `${uploadProgress}% uploaded`}
            </p>

            {/* Progress Steps */}
            {steps.length > 0 && (
              <div className="progress-steps">
                {steps.map((s: any) => {
                  const reached = currentProgress >= s.target;
                  return (
                    <div key={s.name} className={`progress-step ${reached ? 'completed' : ''}`}>
                      <div className="step-dot">{reached ? '✓' : s.target}</div>
                      <div className="step-name">{s.label}</div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* File Metadata */}
            {processingStatus?.file_info && (
              <div className="file-metadata">
                <div className="metadata-item">
                  <span className="metadata-label">Rows:</span>
                  <span className="metadata-value">{processingStatus.file_info.rows}</span>
                </div>
                <span className="metadata-divider">•</span>
                <div className="metadata-item">
                  <span className="metadata-label">Columns:</span>
                  <span className="metadata-value">{processingStatus.file_info.columns}</span>
                </div>
              </div>
            )}

            {/* Activity Logs */}
            {recentLogs.length > 0 && (
              <div className="activity-logs">
                <div className="logs-header">Recent Activity</div>
                <div className="logs-list">
                  {recentLogs.map((l: any, idx: number) => (
                    <div key={`${l.ts}-${idx}`} className="log-entry">
                      <span className="log-time">{new Date(l.ts).toLocaleTimeString()}</span>
                      <span className="log-message">{l.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Success Result */}
        {isCompleted && (
          <div className="result-card result-success">
            <div className="result-icon">✓</div>
            <h3 className="result-title">Comparison Complete!</h3>
            <p className="result-message">{processingStatus?.message}</p>
            {processingStatus?.output_file && (
              <div className="result-file">
                <span className="file-label">Output File:</span>
                <span className="file-path">{processingStatus.output_file}</span>
              </div>
            )}
          </div>
        )}

        {/* Preview Table */}
        {isCompleted && preview && preview.rows?.length > 0 && (
          <div className="preview-card">
            <div className="preview-header">
              <h3 className="preview-title">Result Preview</h3>
            </div>
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

        {/* Error Result */}
        {hasError && (
          <div className="result-card result-error">
            <div className="result-icon">✕</div>
            <h3 className="result-title">Error Occurred</h3>
            <p className="result-message">{error || processingStatus?.error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompareUpload;
