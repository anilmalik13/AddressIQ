import React, { useCallback, useState, useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { uploadFileRequest, resetUploadState, checkProcessingStatus, downloadProcessedFile } from '../../store/slices/fileUploadSlice';
import './FileUpload.css';

const FileUpload: React.FC = () => {
    const dispatch = useAppDispatch();
    const { uploading, uploadProgress, uploadResult, error, processingId, processingStatus } = useAppSelector(
        (state) => state.fileUpload
    );
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    // Use a ref for the polling interval to avoid triggering re-renders
    const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
                alert('Please select a valid Excel (.xlsx, .xls) or CSV (.csv) file');
                return;
            }

            setSelectedFile(file);
            dispatch(resetUploadState());
        }
    }, [dispatch]);

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
    }, [dispatch]);

    const handleDownload = useCallback(() => {
        if (processingStatus?.output_file) {
            dispatch(downloadProcessedFile(processingStatus.output_file));
        }
    }, [dispatch, processingStatus?.output_file]);

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
                
                <div className="upload-section">
                    <div className="file-input-wrapper">
                        <input
                            type="file"
                            id="file-input"
                            accept=".xlsx,.xls,.csv"
                            onChange={handleFileSelect}
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
                            <p><strong>Size:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
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
                            disabled={uploading || !!isProcessing}
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
