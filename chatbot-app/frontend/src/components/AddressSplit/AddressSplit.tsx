import React, { useCallback, useState } from 'react';
import { splitAddress } from '../../services/api';
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

const AddressSplit: React.FC = () => {
    const [inputAddress, setInputAddress] = useState<string>('');
    const [processing, setProcessing] = useState<boolean>(false);
    const [result, setResult] = useState<SplitResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [processingStage, setProcessingStage] = useState<string>('');
    const [estimatedTime, setEstimatedTime] = useState<number>(0);
    const [elapsedTime, setElapsedTime] = useState<number>(0);
    const [specialCharWarning, setSpecialCharWarning] = useState<string | null>(null);

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
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Stage 2: Detecting splits
            setProcessingStage('Detecting potential address splits...');
            await new Promise(resolve => setTimeout(resolve, 500));
            
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

    const handleReset = useCallback(() => {
        setInputAddress('');
        setResult(null);
        setError(null);
    }, []);

    const handleCopyResult = useCallback((text: string) => {
        if (text) {
            navigator.clipboard.writeText(text);
        }
    }, []);

    return (
        <div className="address-split-container">
            <div className="address-split-card">
                <h1>Address Splitting</h1>
                <p>
                    Enter an address that contains coordinating conjunctions (like "and" or "&") 
                    between multiple addresses. The system will automatically split and standardize them.
                </p>

                <div className="processing-section">
                    <div className="input-section">
                        <label htmlFor="address-input">Enter Address:</label>
                        <textarea
                            id="address-input"
                            value={inputAddress}
                            onChange={handleInputChange}
                            placeholder='10255 and 10261 Iron Rock Way'
                            disabled={processing}
                            className="address-input"
                            rows={4}
                        />
                        <small className="hint">
                            Example: "10255 and 10261 Iron Rock Way" - will be split into 2 addresses
                        </small>
                        
                        {specialCharWarning && (
                            <div className="warning-message">
                                <span className="warning-icon">⚠️</span>
                                <span className="warning-text">{specialCharWarning}</span>
                            </div>
                        )}
                    </div>

                    <div className="button-group">
                        <button 
                            onClick={handleProcess} 
                            disabled={!inputAddress.trim() || processing} 
                            className="process-button"
                        >
                            {processing ? 'Processing...' : 'Split & Process Address'}
                        </button>
                        
                        <button
                            onClick={handleReset}
                            disabled={processing}
                            className="reset-button"
                        >
                            Reset
                        </button>
                    </div>

                    {processing && (
                        <div className="loading-section">
                            <div className="loading-content">
                                <div className="loading-header">
                                    <div className="loading-spinner" />
                                    <div className="loading-text">
                                        <h4>Processing Address</h4>
                                        <p className="stage-text">{processingStage}</p>
                                    </div>
                                </div>
                                
                                {estimatedTime > 0 && (
                                    <div className="progress-info">
                                        <div className="progress-bar-container">
                                            <div 
                                                className="progress-bar" 
                                                style={{ 
                                                    width: `${Math.min((elapsedTime / estimatedTime) * 100, 95)}%`,
                                                    transition: 'width 1s linear'
                                                }}
                                            />
                                        </div>
                                        <div className="time-info">
                                            <span className="elapsed-time">
                                                ⏱️ {elapsedTime}s elapsed
                                            </span>
                                            {elapsedTime < estimatedTime && (
                                                <span className="estimated-time">
                                                    ~{estimatedTime}s total
                                                </span>
                                            )}
                                        </div>
                                        {estimatedTime > 20 && elapsedTime < 10 && (
                                            <div className="processing-note">
                                                <small>
                                                    💡 Complex splits require standardizing each address individually.
                                                    This ensures accurate results.
                                                </small>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {result && (
                        <div className="result-section">
                            <div className={`split-info ${result.split ? 'split-detected' : 'no-split'}`}>
                                <div className="split-header">
                                    <h3>
                                        {result.split 
                                            ? `✂️ Address Split Detected (${result.count} addresses)` 
                                            : '✓ No Split Needed'}
                                    </h3>
                                </div>
                                <div className="split-reason">
                                    <strong>Analysis:</strong> {result.reason}
                                </div>
                            </div>

                            {result.addresses && result.addresses.length > 0 && (
                                <div className="addresses-wrapper">
                                    <h3 className="results-title">
                                        {result.split ? 'Standardized Addresses' : 'Standardized Address'}
                                    </h3>
                                    <div className={`addresses-grid ${result.split ? 'grid-layout' : 'single-layout'}`}>
                                        {result.addresses.map((addr, idx) => (
                                            <div key={idx} className={`address-result-card ${addr.status}`}>
                                                <div className="card-header">
                                                    <span className="badge index">
                                                        {result.split ? `#${idx + 1}` : ''}
                                                    </span>
                                                    <span className={`badge status ${addr.status}`}>
                                                        {addr.status}
                                                    </span>
                                                    {result.split && addr.splitNumber && (
                                                        <span className="badge split-num">
                                                            {addr.splitNumber}
                                                        </span>
                                                    )}
                                                </div>

                                                <div className="address-content">
                                                    <div className="address-field">
                                                        <strong>Original:</strong>
                                                        <p>{addr.originalAddress}</p>
                                                    </div>
                                                    
                                                    <div className="address-field standardized">
                                                        <strong>Standardized:</strong>
                                                        <p>{addr.processedAddress}</p>
                                                    </div>

                                                    {addr.explanation && (
                                                        <div className="explanation-section">
                                                            <div className="explanation-badge" title={addr.explanation}>
                                                                ℹ️ Processing Notes
                                                            </div>
                                                            <div className="explanation-tooltip">
                                                                {addr.explanation}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {addr.components && Object.keys(addr.components).some(k => addr.components[k]) && (
                                                        <div className="components-section">
                                                            <strong>Components:</strong>
                                                            <div className="components-grid">
                                                                {addr.components.street_number && (
                                                                    <div className="component">
                                                                        <span className="label">Street #:</span>
                                                                        <span className="value">{addr.components.street_number}</span>
                                                                    </div>
                                                                )}
                                                                {addr.components.street_name && (
                                                                    <div className="component">
                                                                        <span className="label">Street:</span>
                                                                        <span className="value">{addr.components.street_name}</span>
                                                                    </div>
                                                                )}
                                                                {addr.components.street_type && (
                                                                    <div className="component">
                                                                        <span className="label">Type:</span>
                                                                        <span className="value">{addr.components.street_type}</span>
                                                                    </div>
                                                                )}
                                                                {addr.components.city && (
                                                                    <div className="component">
                                                                        <span className="label">City:</span>
                                                                        <span className="value">{addr.components.city}</span>
                                                                    </div>
                                                                )}
                                                                {addr.components.state && (
                                                                    <div className="component">
                                                                        <span className="label">State:</span>
                                                                        <span className="value">{addr.components.state}</span>
                                                                    </div>
                                                                )}
                                                                {addr.components.postal_code && (
                                                                    <div className="component">
                                                                        <span className="label">Postal:</span>
                                                                        <span className="value">{addr.components.postal_code}</span>
                                                                    </div>
                                                                )}
                                                                {addr.components.country && (
                                                                    <div className="component">
                                                                        <span className="label">Country:</span>
                                                                        <span className="value">{addr.components.country}</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="meta-info">
                                                        <span className="chip source">{addr.source}</span>
                                                        <span className="chip confidence">conf: {addr.confidence}</span>
                                                    </div>

                                                    <div className="actions-row">
                                                        <button 
                                                            onClick={() => handleCopyResult(addr.processedAddress)} 
                                                            className="mini-btn"
                                                        >
                                                            📋 Copy
                                                        </button>
                                                        {addr.error && (
                                                            <span className="error-text" title={addr.error}>
                                                                ⚠ {addr.error}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {error && (
                        <div className="result error">
                            <h3>Error</h3>
                            <p>{error}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AddressSplit;
