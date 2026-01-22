import React, { useCallback, useState, useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { uploadFileRequest, uploadFileFailure, resetUploadState, checkProcessingStatus, downloadProcessedFile } from '../../store/slices/fileUploadSlice';
import { downloadSampleFile, getAvailableModels, AIModel } from '../../services/api';
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
    const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>('');
    const [loadingModels, setLoadingModels] = useState<boolean>(true);
    // Use a ref for the polling interval to avoid triggering re-renders
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
        if (selectedFile && selectedModel) {
            dispatch(uploadFileRequest({ file: selectedFile, model: selectedModel }));
        }
    }, [dispatch, selectedFile, selectedModel]);

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
            {/* Hero Section */}
            <div className="hero-section">
                <div className="hero-icon">📄</div>
                <h1 className="hero-title">Upload & Process</h1>
                <p className="hero-subtitle">Transform your address data with AI-powered standardization</p>
            </div>

            {/* Main Content Card */}
            <div className="main-card">
                {/* Info Cards Row */}
                <div className="info-cards-grid">
                    <div className="info-card info-card-blue">
                        <div className="info-card-icon">💡</div>
                        <div className="info-card-content">
                            <div className="info-card-title">Batch Processing</div>
                            <div className="info-card-text">Records processed in batches of 5 for optimal performance</div>
                        </div>
                    </div>
                    <div className="info-card info-card-amber">
                        <div className="info-card-icon">📋</div>
                        <div className="info-card-content">
                            <div className="info-card-title">Required Headers</div>
                            <div className="info-card-text">Site_Name, Site_Address_1-4, City, State, Postcode, Country</div>
                        </div>
                    </div>
                </div>

                {/* Sample File Download */}
                <div className="sample-download-section">
                    <button onClick={handleDownloadSample} className="sample-download-btn">
                        <span className="sample-icon">⬇</span>
                        <span>Download Sample File</span>
                    </button>
                    <span className="sample-help-text">Not sure about the format? Get our template</span>
                </div>

                <div className="upload-section">
                    {/* Drag & Drop File Upload Area */}
                    <div className="upload-area">
                        <input
                            ref={fileInputRef}
                            type="file"
                            id="file-input"
                            accept=".xlsx,.xls,.csv"
                            onChange={handleFileSelect}
                            onClick={(e) => {
                                (e.currentTarget as HTMLInputElement).value = '';
                            }}
                            disabled={uploading}
                            className="file-input"
                        />
                        <label htmlFor="file-input" className="file-upload-zone">
                            {!selectedFile ? (
                                <>
                                    <div className="upload-icon">📁</div>
                                    <div className="upload-text-primary">Drop your file here or click to browse</div>
                                    <div className="upload-text-secondary">Supports .xlsx, .xls, and .csv files</div>
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

                    {/* Action Buttons */}
                    <div className="action-buttons">
                        <button
                            onClick={handleUpload}
                            disabled={!selectedFile || uploading || !!isProcessing}
                            className="btn btn-primary"
                        >
                            {uploading ? (
                                <>
                                    <span className="btn-spinner"></span>
                                    <span>Uploading...</span>
                                </>
                            ) : isProcessing ? (
                                <>
                                    <span className="btn-spinner"></span>
                                    <span>Processing...</span>
                                </>
                            ) : (
                                <>
                                    <span>Start Processing</span>
                                </>
                            )}
                        </button>
                        
                        <button
                            onClick={handleReset}
                            disabled={uploading}
                            className="btn btn-secondary"
                        >
                            <span>Reset</span>
                        </button>

                        {isCompleted && processingStatus?.output_file && (
                            <button
                                onClick={handleDownload}
                                className="btn btn-success"
                            >
                                <span>⬇</span>
                                <span>Download Result</span>
                            </button>
                        )}
                    </div>

                    {/* Processing Tip */}
                    {isProcessing && (
                        <div className="processing-tip">
                            <span className="tip-icon">💡</span>
                            <span className="tip-text">
                                <strong>Pro Tip:</strong> You can reset and process other files. Completed files appear in Processing History.
                            </span>
                        </div>
                    )}

                    {/* Progress Section */}
                    {(uploading || isProcessing) && (
                        <div className="progress-card">
                            <div className="progress-header">
                                <span className="progress-title">
                                    {isProcessing ? 'Processing Your File' : 'Uploading'}
                                </span>
                                <span className="progress-percentage">
                                    {isProcessing ? processingStatus?.progress || 0 : uploadProgress}%
                                </span>
                            </div>
                            <div className="modern-progress-bar">
                                <div 
                                    className="modern-progress-fill" 
                                    style={{ 
                                        width: `${isProcessing ? processingStatus?.progress || 0 : uploadProgress}%` 
                                    }}
                                />
                            </div>
                            <div className="progress-message">
                                {isProcessing 
                                    ? processingStatus?.message || 'Processing...'
                                    : 'Uploading your file...'
                                }
                            </div>
                            
                            {/* Processing Steps */}
                            {steps.length > 0 && (
                                <div className="progress-steps">
                                    {steps.map(s => {
                                        const reached = currentProgress >= s.target;
                                        return (
                                            <div key={s.name} className={`progress-step ${reached ? 'completed' : ''}`}>
                                                <div className="step-dot">{reached ? '✓' : ''}</div>
                                                <div className="step-name">{s.label}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                            
                            {/* File Metadata */}
                            {processingStatus?.file_info && (
                                <div className="file-metadata">
                                    <span className="metadata-item">
                                        <span className="metadata-label">Rows:</span>
                                        <span className="metadata-value">{processingStatus.file_info.rows}</span>
                                    </span>
                                    <span className="metadata-divider">•</span>
                                    <span className="metadata-item">
                                        <span className="metadata-label">Columns:</span>
                                        <span className="metadata-value">{processingStatus.file_info.columns}</span>
                                    </span>
                                </div>
                            )}
                            
                            {/* Activity Logs */}
                            {recentLogs.length > 0 && (
                                <div className="activity-logs">
                                    <div className="logs-header">Recent Activity</div>
                                    <div className="logs-list">
                                        {recentLogs.map(l => (
                                            <div key={l.ts} className="log-entry">
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
                            <div className="result-title">Processing Complete!</div>
                            <div className="result-message">{processingStatus?.message}</div>
                            {processingStatus?.output_file && (
                                <div className="result-file">
                                    <span className="file-label">Output file:</span>
                                    <span className="file-path">{processingStatus.output_file}</span>
                                </div>
                            )}
                        </div>
                    )}

                    {uploadResult && !processingStatus && (
                        <div className="result-card result-success">
                            <div className="result-icon">✓</div>
                            <div className="result-title">Upload Complete!</div>
                            <div className="result-message">{uploadResult}</div>
                        </div>
                    )}

                    {/* Error Result */}
                    {hasError && (
                        <div className="result-card result-error">
                            <div className="result-icon">✕</div>
                            <div className="result-title">Error Occurred</div>
                            <div className="result-message">{error || processingStatus?.error}</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FileUpload;
