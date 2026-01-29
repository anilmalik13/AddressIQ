import React, { useCallback, useState, useRef, useEffect } from 'react';
import { splitAddress, uploadSplitFile, checkProcessingStatus } from '../../services/api';
import './AddressSplit.css';

interface SplitAddressResult {
    originalAddress: string;
    processedAddress: string;
    status: string;
    confidence: string;
    source: string;
    components: Record<string, string>;
    splitIndicator?: string;
    splitNumber?: string;
    splitReason?: string;
    explanation?: string;
    error?: string;
}

interface SplitResponse {
    split: boolean;
    count: number;
    reason: string;
    addresses: SplitAddressResult[];
}

type ProcessingMode = 'text' | 'file';
type SplitMode = 'rule' | 'gpt';

const AddressSplit: React.FC = () => {
    
    // Mode state
    const [mode, setMode] = useState<ProcessingMode>('text');
    
    // Text processing state
    const [inputAddress, setInputAddress] = useState<string>('');
    const [processing, setProcessing] = useState<boolean>(false);
    const [result, setResult] = useState<SplitResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [processingStage, setProcessingStage] = useState<string>('');
    const [estimatedTime, setEstimatedTime] = useState<number>(0);
    const [elapsedTime, setElapsedTime] = useState<number>(0);
    const [specialCharWarning, setSpecialCharWarning] = useState<string | null>(null);
    
    // File upload state
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [fileProcessing, setFileProcessing] = useState<boolean>(false);
    const [fileStatus, setFileStatus] = useState<any>(null);
    const [splitMode, setSplitMode] = useState<SplitMode>('rule');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
    
    // Wait dialog state
    const [showWaitDialog, setShowWaitDialog] = useState<boolean>(false);
    const [waitChoice, setWaitChoice] = useState<'wait' | 'dontWait' | null>(null);
    const [processingProgress, setProcessingProgress] = useState<number>(0);
    const [processingMessage, setProcessingMessage] = useState<string>('');

    // Detect special characters that might interfere with address splitting
    const detectSpecialCharacters = useCallback((text: string): { hasSpecial: boolean; chars: string[]; message: string | null } => {
        // Special characters that might interfere with splitting
        const problematicChars = ['(', ')', '[', ']', '{', '}', ':', ';', '|', '/', '\\', '~', '`', '!', '?', '@', '#', '$', '%', '^', '*', '=', '+', '<', '>'];
        
        const foundChars: string[] = [];
        for (const char of problematicChars) {
            if (text.includes(char)) {
                foundChars.push(char);
            }
        }
        
        if (foundChars.length > 0) {
            const charList = foundChars.map(c => `'${c}'`).join(', ');
            return {
                hasSpecial: true,
                chars: foundChars,
                message: `Warning: Your address contains special characters (${charList}) that may interfere with splitting. Please review and remove them before processing.`
            };
        }
        
        return { hasSpecial: false, chars: [], message: null };
    }, []);

    const handleInputChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = event.target.value;
        setInputAddress(newValue);
        
        // Check for special characters and show warning
        const detection = detectSpecialCharacters(newValue);
        setSpecialCharWarning(detection.message);
    }, [detectSpecialCharacters]);

    const handleProcess = useCallback(async () => {
        const trimmed = inputAddress.trim();
        if (!trimmed) return;

        setProcessing(true);
        setError(null);
        setResult(null);
        setElapsedTime(0);
        
        // Estimate time based on potential split complexity
        const hasMultipleConjunctions = (trimmed.match(/\band\b|&/gi) || []).length;
        const estimatedAddressCount = hasMultipleConjunctions > 0 ? hasMultipleConjunctions + 1 : 1;
        const timePerAddress = 15; // seconds per address for standardization
        const baseTime = 5; // base processing time
        const estimated = baseTime + (estimatedAddressCount * timePerAddress);
        setEstimatedTime(estimated);

        // Start elapsed time counter
        const startTime = Date.now();
        const timerInterval = setInterval(() => {
            setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
        }, 1000);

        try {
             // Stage 1: Analyzing
            setProcessingStage('Analyzing address structure...');
            await new Promise(resolve => setTimeout(resolve, 50));
            
            // Stage 2: Detecting splits
            setProcessingStage('Detecting potential address splits...');
            await new Promise(resolve => setTimeout(resolve, 50));
            
            // Stage 3: Processing
            setProcessingStage(
                estimatedAddressCount > 2
                    ? `Processing ${estimatedAddressCount} addresses (this may take ${estimated}s)...`
                    : 'Standardizing addresses...'
            );

            const response = await splitAddress(trimmed);
            
            clearInterval(timerInterval);
            setProcessingStage('Complete!');
            setResult(response);
        } catch (err: any) {
            clearInterval(timerInterval);
            setError(err.message || 'Address splitting failed');
        } finally {
            setProcessing(false);
            setTimeout(() => {
                setProcessingStage('');
                setEstimatedTime(0);
            }, 500);
        }
    }, [inputAddress]);

    // File upload handlers
    const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type
            const validTypes = [
                'text/csv',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/csv'
            ];
            const validExtensions = ['.csv', '.xls', '.xlsx'];
            const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
            
            if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
                setError('Please select a valid CSV or Excel file (.csv, .xls, .xlsx)');
                return;
            }
            
            setSelectedFile(file);
            setError(null);
            setFileStatus(null);
        }
    }, []);

    const handleFileRemove = useCallback(() => {
        setSelectedFile(null);
        setUploadProgress(0);
        setError(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    }, []);

    // Remove the polling function as we're no longer tracking individual file status in this component

    const handleFileUpload = useCallback(async () => {
        if (!selectedFile) return;
        // Show wait dialog
        setShowWaitDialog(true);
    }, [selectedFile]);
    
    const startPolling = useCallback((procId: string) => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
        }
        
        const poll = async () => {
            try {
                const status = await checkProcessingStatus(procId);
                setProcessingProgress(status.progress || 0);
                setProcessingMessage(status.message || 'Processing...');
                
                if (status.status === 'completed') {
                    clearInterval(pollIntervalRef.current!);
                    setFileProcessing(false);
                    setFileStatus({
                        status: 'completed',
                        message: 'File processed successfully!',
                        processing_id: procId,
                        output_file: status.output_file,
                        output_path: status.output_path
                    });
                    setSelectedFile(null);
                    if (fileInputRef.current) {
                        fileInputRef.current.value = '';
                    }
                } else if (status.status === 'error' || status.status === 'failed') {
                    clearInterval(pollIntervalRef.current!);
                    setFileProcessing(false);
                    setError(status.error || 'Processing failed');
                }
            } catch (err: any) {
                console.error('Polling error:', err);
            }
        };
        
        poll(); // Initial poll
        pollIntervalRef.current = setInterval(poll, 2000); // Poll every 2 seconds
    }, []);
    
    const handleWaitChoice = useCallback(async (choice: 'wait' | 'dontWait') => {
        setWaitChoice(choice);
        setShowWaitDialog(false);
        
        if (!selectedFile) return;

        setFileProcessing(true);
        setError(null);
        setUploadProgress(0);
        
        const fileToUpload = selectedFile;
        const modeToUse = splitMode;

        try {
            const response = await uploadSplitFile(
                fileToUpload,
                true, // enable_split
                modeToUse,
                undefined, // model
                (progress) => setUploadProgress(progress)
            );
            
            if (choice === 'wait') {
                // Start polling for progress
                setProcessingProgress(10);
                setProcessingMessage('Upload complete, processing file...');
                startPolling(response.processing_id);
            } else {
                // Don't wait - clear form and show success
                setSelectedFile(null);
                setFileProcessing(false);
                setUploadProgress(0);
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
                setFileStatus({
                    status: 'queued',
                    message: `File uploaded successfully! Processing ID: ${response.processing_id}. You can upload another file or check Processing History for results.`,
                    processing_id: response.processing_id
                });
                setTimeout(() => {
                    setFileStatus(null);
                }, 5000);
            }

        } catch (err: any) {
            setFileProcessing(false);
            setError(err.message || 'File upload failed');
        }
    }, [selectedFile, splitMode, startPolling]);
    
    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, []);

    const handleReset = useCallback(() => {
        setInputAddress('');
        setResult(null);
        setError(null);
        setSelectedFile(null);
        setFileStatus(null);
        setFileProcessing(false);
        setUploadProgress(0);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    }, []);

    const handleCopyResult = useCallback((text: string) => {
        if (text) {
            navigator.clipboard.writeText(text);
        }
    }, []);
    
    const handleDownloadFile = useCallback(async (outputFile: string) => {
        try {
            const response = await fetch(`http://localhost:5001/api/download/${outputFile}`);
            if (!response.ok) throw new Error('Download failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = outputFile;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err: any) {
            setError('Failed to download file: ' + err.message);
        }
    }, []);

    const handleModeChange = useCallback((newMode: ProcessingMode) => {
        setMode(newMode);
        setError(null);
        setResult(null);
        setFileStatus(null);
    }, []);

    return (
        <div className="modern-container">
            <div className="modern-hero">
                <div className="modern-hero-icon">🔀</div>
                <h1 className="modern-hero-title">Address Splitting</h1>
                <p className="modern-hero-subtitle">
                    Intelligently split and standardize addresses with coordinating conjunctions
                </p>
            </div>

            <div className="modern-card">
                {/* Mode Toggle */}
                <div className="mode-toggle-container">
                    <button
                        onClick={() => handleModeChange('text')}
                        className={`mode-btn ${mode === 'text' ? 'active' : ''}`}
                        disabled={processing || fileProcessing}
                    >
                        <span className="mode-icon">✍️</span>
                        <span className="mode-text">
                            <strong>Text Input</strong>
                            <small>Enter addresses manually</small>
                        </span>
                    </button>
                    <button
                        onClick={() => handleModeChange('file')}
                        className={`mode-btn ${mode === 'file' ? 'active' : ''}`}
                        disabled={processing || fileProcessing}
                    >
                        <span className="mode-icon">📄</span>
                        <span className="mode-text">
                            <strong>File Upload</strong>
                            <small>Process CSV or Excel file</small>
                        </span>
                    </button>
                </div>

                <div className="modern-info-cards">
                    <div className="modern-info-card modern-info-card-blue">
                        <div className="modern-info-card-icon">✨</div>
                        <div className="modern-info-card-content">
                            <div className="modern-info-card-title">Smart Detection</div>
                            <div className="modern-info-card-text">
                                Automatically detects "and" or "&" between addresses
                            </div>
                        </div>
                    </div>

                    <div className="modern-info-card modern-info-card-green">
                        <div className="modern-info-card-icon">🎯</div>
                        <div className="modern-info-card-content">
                            <div className="modern-info-card-title">AI-Powered</div>
                            <div className="modern-info-card-text">
                                Each split address is standardized with AI precision
                            </div>
                        </div>
                    </div>
                </div>

                {/* Text Input Mode */}
                {mode === 'text' && (
                    <>
                        <div className="split-input-section">
                            <label htmlFor="address-input" className="modern-label">
                                Enter Address with Multiple Numbers:
                            </label>
                            <textarea
                                id="address-input"
                                value={inputAddress}
                                onChange={handleInputChange}
                                placeholder="10255 and 10261 Iron Rock Way"
                                disabled={processing}
                                className="modern-textarea"
                                rows={4}
                            />
                            <small className="split-hint">
                                💡 Example: "10255 and 10261 Iron Rock Way" will be split into 2 addresses
                            </small>
                            
                            {specialCharWarning && (
                                <div className="modern-alert modern-alert-warning">
                                    <span className="modern-alert-icon">⚠️</span>
                                    <span>{specialCharWarning}</span>
                                </div>
                            )}
                        </div>

                        <div className="split-button-group">
                            <button 
                                onClick={handleProcess} 
                                disabled={!inputAddress.trim() || processing} 
                                className="modern-btn modern-btn-primary"
                            >
                        {processing ? (
                            <>
                                <span className="modern-btn-spinner" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <span>🔀</span>
                                Split & Standardize
                            </>
                        )}
                    </button>
                    
                    <button
                        onClick={handleReset}
                        disabled={processing}
                        className="modern-btn modern-btn-gray"
                    >
                        Reset
                    </button>
                </div>
                    </>
                )}

                {/* File Upload Mode */}
                {mode === 'file' && (
                    <>
                        <div className="upload-section">
                            <label className="modern-label">
                                Upload CSV or Excel File:
                            </label>

                            {!selectedFile && (
                                <div className="upload-dropzone">
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".csv,.xls,.xlsx"
                                        onChange={handleFileSelect}
                                        disabled={fileProcessing}
                                        className="file-input-hidden"
                                        id="file-upload-split"
                                    />
                                    <label htmlFor="file-upload-split" className="file-upload-label">
                                        <div className="upload-icon">📁</div>
                                        <div className="upload-text">
                                            <strong>Click to upload</strong> or drag and drop
                                        </div>
                                        <div className="upload-hint">
                                            CSV or Excel (XLSX, XLS) up to 50MB
                                        </div>
                                    </label>
                                </div>
                            )}

                            {selectedFile && !fileProcessing && !fileStatus && (
                                <div className="file-selected-card">
                                    <div className="file-selected-info">
                                        <div className="file-icon">📄</div>
                                        <div className="file-details">
                                            <div className="file-name">{selectedFile.name}</div>
                                            <div className="file-size">
                                                {(selectedFile.size / 1024).toFixed(2)} KB
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleFileRemove}
                                        className="file-remove-btn"
                                        title="Remove file"
                                    >
                                        ✕
                                    </button>
                                </div>
                            )}

                            {selectedFile && !fileProcessing && !fileStatus && (
                                <>
                                    <div className="split-mode-section">
                                        <label className="modern-label">
                                            Splitting Mode:
                                        </label>
                                        <div className="split-mode-options">
                                            <button
                                                onClick={() => setSplitMode('rule')}
                                                className={`split-mode-btn ${splitMode === 'rule' ? 'active' : ''}`}
                                            >
                                                <span className="split-mode-icon">📋</span>
                                                <span className="split-mode-text">
                                                    <strong>Rule-Based</strong>
                                                    <small>Fast & efficient</small>
                                                </span>
                                            </button>
                                            <button
                                                onClick={() => setSplitMode('gpt')}
                                                className={`split-mode-btn ${splitMode === 'gpt' ? 'active' : ''}`}
                                            >
                                                <span className="split-mode-icon">🤖</span>
                                                <span className="split-mode-text">
                                                    <strong>AI-Powered</strong>
                                                    <small>GPT-based analysis</small>
                                                </span>
                                            </button>
                                        </div>
                                    </div>

                                    <div className="split-button-group">
                                        <button
                                            onClick={handleFileUpload}
                                            disabled={!selectedFile}
                                            className="modern-btn modern-btn-primary"
                                        >
                                            <span>🔀</span>
                                            Process File
                                        </button>
                                        <button
                                            onClick={handleFileRemove}
                                            className="modern-btn modern-btn-gray"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </>
                            )}

                            {fileProcessing && waitChoice === null && (
                                <div className="upload-progress-card">
                                    <div className="upload-progress-header">
                                        <div className="upload-progress-icon">📤</div>
                                        <div className="upload-progress-text">
                                            <strong>Uploading file...</strong>
                                            <small>{uploadProgress}% complete</small>
                                        </div>
                                    </div>
                                    <div className="modern-progress">
                                        <div 
                                            className="modern-progress-fill" 
                                            style={{ width: `${uploadProgress}%` }}
                                        />
                                    </div>
                                </div>
                            )}
                            
                            {fileProcessing && waitChoice === 'wait' && (
                                <div className="upload-progress-card">
                                    <div className="upload-progress-header">
                                        <div className="upload-progress-icon">⚙️</div>
                                        <div className="upload-progress-text">
                                            <strong>Processing file...</strong>
                                            <small>{processingMessage}</small>
                                        </div>
                                    </div>
                                    <div className="modern-progress">
                                        <div 
                                            className="modern-progress-fill" 
                                            style={{ width: `${processingProgress}%` }}
                                        />
                                    </div>
                                    <div className="split-time-info" style={{ marginTop: '8px' }}>
                                        <span>{processingProgress}% complete</span>
                                    </div>
                                </div>
                            )}

                            {fileStatus && fileStatus.status === 'queued' && (
                                <div className="modern-alert modern-alert-success" style={{ marginTop: '20px' }}>
                                    <span className="modern-alert-icon">✓</span>
                                    <div>
                                        <strong>File uploaded successfully!</strong>
                                        <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                                            Processing ID: <strong>{fileStatus.processing_id}</strong>
                                        </p>
                                        <p style={{ margin: '4px 0 0 0', fontSize: '13px', opacity: '0.9' }}>
                                            You can upload another file or check <a href="/job-history" style={{ color: 'inherit', textDecoration: 'underline' }}>Processing History</a> for results.
                                        </p>
                                    </div>
                                </div>
                            )}
                            
                            {fileStatus && fileStatus.status === 'completed' && (
                                <div className="modern-alert modern-alert-success" style={{ marginTop: '20px' }}>
                                    <span className="modern-alert-icon">✓</span>
                                    <div>
                                        <strong>File processed successfully!</strong>
                                        <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                                            Processing ID: <strong>{fileStatus.processing_id}</strong>
                                        </p>
                                        <div style={{ marginTop: '12px' }}>
                                            <button
                                                onClick={() => handleDownloadFile(fileStatus.output_file)}
                                                className="modern-btn modern-btn-primary"
                                            >
                                                📥 Download Processed File
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {processing && mode === 'text' && (
                    <div className="split-loading-card">
                        <div className="split-loading-header">
                            <div className="modern-btn-spinner" style={{ width: '40px', height: '40px' }} />
                            <div className="split-loading-text">
                                <h4 className="split-loading-title">Processing Address</h4>
                                <p className="split-loading-stage">{processingStage}</p>
                            </div>
                        </div>
                        
                        {estimatedTime > 0 && (
                            <div className="split-progress-section">
                                <div className="modern-progress">
                                    <div 
                                        className="modern-progress-fill" 
                                        style={{ 
                                            width: `${Math.min((elapsedTime / estimatedTime) * 100, 95)}%`
                                        }}
                                    />
                                </div>
                                <div className="split-time-info">
                                    <span className="split-time-elapsed">
                                        ⏱️ {elapsedTime}s elapsed
                                    </span>
                                    {elapsedTime < estimatedTime && (
                                        <span className="split-time-estimate">
                                            ~{estimatedTime}s total
                                        </span>
                                    )}
                                </div>
                                {estimatedTime > 20 && elapsedTime < 10 && (
                                    <div className="modern-alert modern-alert-info" style={{ marginTop: '12px' }}>
                                        <span className="modern-alert-icon">💡</span>
                                        <span>
                                            Complex splits require standardizing each address individually for accurate results.
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {result && (
                    <div className="split-results-section">
                        <div className={`split-result-header ${result.split ? 'split-detected' : 'no-split'}`}>
                            <div className="split-result-icon">
                                {result.split ? '✂️' : '✓'}
                            </div>
                            <div className="split-result-content">
                                <h3 className="split-result-title">
                                    {result.split 
                                        ? `Address Split Detected (${result.count} addresses)` 
                                        : 'No Split Needed'}
                                </h3>
                                <p className="split-result-reason">
                                    <strong>Analysis:</strong> {result.reason}
                                </p>
                            </div>
                        </div>

                        {result.addresses && result.addresses.length > 0 && (
                            <div className="split-addresses-container">
                                <h4 className="split-addresses-title">
                                    {result.split ? 'Standardized Addresses' : 'Standardized Address'}
                                </h4>
                                <div className={`split-addresses-grid ${result.split ? 'multi-column' : 'single-column'}`}>
                                    {result.addresses.map((addr, idx) => (
                                        <div key={idx} className={`split-address-card status-${addr.status}`}>
                                            <div className="split-address-badges">
                                                {result.split && (
                                                    <span className="split-badge index">
                                                        #{idx + 1}
                                                    </span>
                                                )}
                                                <span className={`split-badge status ${addr.status}`}>
                                                    {addr.status === 'success' ? '✓' : addr.status === 'error' ? '✗' : '⚠'}  {addr.status}
                                                </span>
                                                {result.split && addr.splitNumber && (
                                                    <span className="split-badge info">
                                                        {addr.splitNumber}
                                                    </span>
                                                )}
                                            </div>

                                            <div className="split-address-body">
                                                <div className="split-address-field">
                                                    <div className="split-field-label">Original Address</div>
                                                    <div className="split-field-value original">{addr.originalAddress}</div>
                                                </div>
                                                
                                                <div className="split-address-field">
                                                    <div className="split-field-label">Standardized Address</div>
                                                    <div className="split-field-value standardized">{addr.processedAddress}</div>
                                                    <button 
                                                        className="split-copy-btn"
                                                        onClick={() => handleCopyResult(addr.processedAddress)}
                                                        title="Copy standardized address"
                                                    >
                                                        📋 Copy
                                                    </button>
                                                </div>

                                                {addr.explanation && (
                                                    <div className="modern-alert modern-alert-info" style={{ margin: '12px 0 0' }}>
                                                        <span className="modern-alert-icon">💡</span>
                                                        <span style={{ fontSize: '13px' }}>{addr.explanation}</span>
                                                    </div>
                                                )}

                                                {addr.components && Object.keys(addr.components).some(k => addr.components[k]) && (
                                                    <details className="split-components-details">
                                                        <summary className="split-components-summary">
                                                            🗂️ View Components ({Object.keys(addr.components).filter(k => addr.components[k]).length})
                                                        </summary>
                                                        <div className="split-components-grid">
                                                            {Object.entries(addr.components).filter(([_, value]) => value).map(([key, value]) => (
                                                                <div key={key} className="split-component">
                                                                    <span className="split-component-label">
                                                                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                                                    </span>
                                                                    <span className="split-component-value">{value}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </details>
                                                )}

                                                {addr.error && (
                                                    <div className="modern-alert modern-alert-error">
                                                        <span className="modern-alert-icon">❌</span>
                                                        <span>{addr.error}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {error && (
                    <div className="modern-alert modern-alert-error split-error-message">
                        <span className="modern-alert-icon">❌</span>
                        <span>{error}</span>
                    </div>
                )}
            </div>
            
            {/* Wait Dialog Modal */}
            {showWaitDialog && (
                <div className="modal-overlay" onClick={() => setShowWaitDialog(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Processing Options</h3>
                            <button className="modal-close" onClick={() => setShowWaitDialog(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <p>Your file has been uploaded. Would you like to wait here for processing to complete?</p>
                            <div className="modal-options">
                                <div className="modal-option-card">
                                    <div className="modal-option-icon">⏱️</div>
                                    <h4>Wait Here</h4>
                                    <p>Stay on this page and download the processed file when ready</p>
                                    <button 
                                        className="modern-btn modern-btn-primary"
                                        onClick={() => handleWaitChoice('wait')}
                                    >
                                        Wait for Results
                                    </button>
                                </div>
                                <div className="modal-option-card">
                                    <div className="modal-option-icon">📋</div>
                                    <h4>Process in Background</h4>
                                    <p>Continue uploading files and check Processing History later</p>
                                    <button 
                                        className="modern-btn modern-btn-gray"
                                        onClick={() => handleWaitChoice('dontWait')}
                                    >
                                        Go to History
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AddressSplit;
