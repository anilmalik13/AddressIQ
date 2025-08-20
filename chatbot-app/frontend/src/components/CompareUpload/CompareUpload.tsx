import React, { useCallback, useEffect, useRef, useState } from 'react';
import { uploadCompareFile, checkProcessingStatus, downloadFile } from '../../services/api';
import '../FileUpload/FileUpload.css';

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
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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
      alert('Please select a valid Excel (.xlsx, .xls) or CSV (.csv) file');
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
      const res = await uploadCompareFile(selectedFile, (p) => setUploadProgress(p));
      setProcessingId(res.processing_id);
      setUploadProgress(100);
    } catch (e: any) {
      setError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [selectedFile]);

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
        <p>Upload your Excel or CSV to run address comparison. The transformed file will be available to download.</p>

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

          <div className="button-group">
            <button onClick={handleUpload} disabled={!selectedFile || uploading || !!isProcessing} className="upload-button">
              {uploading ? 'Uploading...' : isProcessing ? 'Processing...' : 'Upload & Compare'}
            </button>
            <button onClick={handleReset} disabled={uploading || !!isProcessing} className="reset-button">Reset</button>
            {isCompleted && processingStatus?.output_file && (
              <button onClick={handleDownload} className="download-button">Download Result</button>
            )}
          </div>

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
