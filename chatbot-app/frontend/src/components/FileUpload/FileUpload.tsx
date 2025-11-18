import React, { useCallback, useState, useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { uploadFileRequest, uploadFileFailure, resetUploadState, checkProcessingStatus, downloadProcessedFile } from '../../store/slices/fileUploadSlice';
import { downloadSampleFile } from '../../services/api';
import './FileUpload.css';

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

const FileUpload: React.FC = () => {
    const dispatch = useAppDispatch();
    const { uploading, uploadProgress, uploadResult, error, processingId, processingStatus } = useAppSelector(
        (state) => state.fileUpload
    );
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    // Use a ref for the polling interval to avoid triggering re-renders
    const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    // Start polling for processing status when we get a processing ID
    useEffect(() => {
        const done = ['completed', 'error'];
        const currentStatus = processingStatus?.status;
        if (processingId && !done.includes(currentStatus || '')) {
            // Start polling if not already started
            if (!statusIntervalRef.current) {
                statusIntervalRef.current = setInterval(() => {
                    dispatch(checkProcessingStatus(processingId));
                }, 2000);
            }
        } else {
            // Stop polling if finished or no processing id
            if (statusIntervalRef.current) {
                clearInterval(statusIntervalRef.current);
                statusIntervalRef.current = null;
            }
        }
        return () => {
            // On dependency change/unmount, if processing finished, clear interval
            if ((!processingId || done.includes(currentStatus || '')) && statusIntervalRef.current) {
                clearInterval(statusIntervalRef.current);
                statusIntervalRef.current = null;
            }
        };
    }, [dispatch, processingId, processingStatus?.status]);

    // Ensure interval cleared on unmount
    useEffect(() => () => {
        if (statusIntervalRef.current) {
            clearInterval(statusIntervalRef.current);
            statusIntervalRef.current = null;
        }
    }, []);

    const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type - now includes CSV
            const allowedTypes = [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'application/csv'
            ];
            
            const allowedExtensions = ['.xlsx', '.xls', '.csv'];
            const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
            
            if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
                // Show error via Redux state instead of alert
                dispatch(uploadFileFailure('Invalid file type. Please select a valid Excel (.xlsx, .xls) or CSV (.csv) file.'));
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
                return;
            }

            setSelectedFile(file);
            dispatch(resetUploadState());
        }
    }, [dispatch]);

    // Auto-reset file if upload fails due to empty file or invalid headers
    useEffect(() => {
        if (error && (
            error.toLowerCase().includes('no data rows') || 
            error.toLowerCase().includes('no columns') || 
            error.toLowerCase().includes('no records') ||
            error.toLowerCase().includes('missing required columns') ||
            error.toLowerCase().includes('invalid headers')
        )) {
            // Reset file after a brief delay to show the error message first
            const timer = setTimeout(() => {
                setSelectedFile(null);
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const handleUpload = useCallback(() => {
        if (selectedFile) {
            dispatch(uploadFileRequest(selectedFile));
        }
    }, [dispatch, selectedFile]);

    const handleReset = useCallback(() => {
        setSelectedFile(null);
        dispatch(resetUploadState());
        if (statusIntervalRef.current) {
            clearInterval(statusIntervalRef.current);
            statusIntervalRef.current = null;
        }
        // Clear native file input so selecting the same file again fires onChange
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    }, [dispatch]);

    const handleDownload = useCallback(() => {
        if (processingStatus?.output_file) {
            dispatch(downloadProcessedFile(processingStatus.output_file));
        }
    }, [dispatch, processingStatus?.output_file]);

    const handleDownloadSample = useCallback(async () => {
        try {
            await downloadSampleFile('/v1/samples/file-upload', 'file-upload-sample.csv');
        } catch (error) {
            console.error('Failed to download sample file:', error);
        }
    }, []);

    const isProcessing = processingStatus && ['uploaded', 'processing'].includes(processingStatus.status);
    const isCompleted = processingStatus?.status === 'completed';
    const hasError = processingStatus?.status === 'error' || !!error;

    const steps = processingStatus?.steps || [];
    const currentProgress = processingStatus?.progress || 0;
    const recentLogs = (processingStatus?.logs || []).slice(-5).reverse();

    return (
        <div className="file-upload-container">
            <div className="file-upload-card">
                <h1>File Upload</h1>
                <p>Upload your Excel (.xlsx, .xls) or CSV (.csv) file to process address data</p>
                
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
                            but the operations are performed on 5 records at a time. Processing time varies and directly depends upon the number of records in your file.
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
                            <strong> Site_Name, Site_Address_1, Site_Address_2, Site_Address_3, Site_Address_4, Site_City, Site_State, Site_Postcode, Site_Country</strong>. Download the sample file to see the correct format.
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
                        📥 Download Sample Upload File
                    </button>
                </div>

                <div className="upload-section">
                    <div className="file-input-wrapper">
                        <input
                            ref={fileInputRef}
                            type="file"
                            id="file-input"
                            accept=".xlsx,.xls,.csv"
                            onChange={handleFileSelect}
                            onClick={(e) => {
                                // Ensure value cleared before opening dialog so selecting same file triggers onChange
                                (e.currentTarget as HTMLInputElement).value = '';
                            }}
                            disabled={uploading}
                            className="file-input"
                        />
                        <label htmlFor="file-input" className="file-input-label">
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
                        <button
                            onClick={handleUpload}
                            disabled={!selectedFile || uploading || !!isProcessing}
                            className="upload-button"
                        >
                            {uploading ? 'Uploading...' : isProcessing ? 'Processing...' : 'Upload & Process File'}
                        </button>
                        
                        <button
                            onClick={handleReset}
                            disabled={uploading}
                            className="reset-button"
                        >
                            Reset
                        </button>

                        {isCompleted && processingStatus?.output_file && (
                            <button
                                onClick={handleDownload}
                                className="download-button"
                            >
                                Download Processed File
                            </button>
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
                                <div 
                                    className="progress-fill" 
                                    style={{ 
                                        width: `${isProcessing ? processingStatus?.progress || 0 : uploadProgress}%` 
                                    }}
                                />
                            </div>
                            <p>
                                {isProcessing 
                                    ? `${processingStatus?.progress || 0}% - ${processingStatus?.message || 'Processing...'}`
                                    : `${uploadProgress}% uploaded`
                                }
                            </p>
                            {steps.length > 0 && (
                                <div className="steps-wrapper">
                                    <div className="steps">
                                        {steps.map(s => {
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
                                        {recentLogs.map(l => (
                                            <li key={l.ts}>{new Date(l.ts).toLocaleTimeString()} - {l.message}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}

                    {isCompleted && (
                        <div className="result success">
                            <h3>Processing Complete!</h3>
                            <p>{processingStatus?.message}</p>
                            {processingStatus?.output_file && (
                                <p><strong>Output file:</strong> {processingStatus.output_file}</p>
                            )}
                        </div>
                    )}

                    {uploadResult && !processingStatus && (
                        <div className="result success">
                            <h3>Upload Complete!</h3>
                            <p>{uploadResult}</p>
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

export default FileUpload;
