import React, { useCallback, useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { processAddressRequest, processAddressesRequest, resetAddressState } from '../../store/slices/addressProcessingSlice';
import { getAvailableModels, AIModel } from '../../services/api';
import '../../styles/shared.css';
import './AddressProcessing.css';

const AddressProcessing: React.FC = () => {
    const dispatch = useAppDispatch();
    const { processing, processedAddress, error, multiResults } = useAppSelector((state) => state.addressProcessing);
    const [inputAddress, setInputAddress] = useState<string>('');
    const [mode, setMode] = useState<'single' | 'multi'>('single');
    const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>('');
    const [loadingModels, setLoadingModels] = useState<boolean>(true);

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

    const handleInputChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputAddress(event.target.value);
    }, []);

    const handleProcess = useCallback(() => {
        const trimmed = inputAddress.trim();
        if (!trimmed) return;
        if (mode === 'single') {
            dispatch(processAddressRequest({address: trimmed, model: selectedModel}));
        } else {
            // Split by newlines, filter empties
            const list = trimmed.split(/\r?\n/).map(a => a.trim()).filter(a => a.length > 0);
            if (list.length === 1) {
                dispatch(processAddressRequest({address: list[0], model: selectedModel}));
            } else if (list.length > 1) {
                dispatch(processAddressesRequest({addresses: list, model: selectedModel}));
            }
        }
    }, [dispatch, inputAddress, mode, selectedModel]);

    const handleReset = useCallback(() => {
        setInputAddress('');
        dispatch(resetAddressState());
    }, [dispatch]);

    const handleCopyResult = useCallback((text?: string) => {
        const value = text || processedAddress;
        if (value) {
            navigator.clipboard.writeText(value);
        }
    }, [processedAddress]);

    return (
        <div className="modern-container">
            {/* Hero Section */}
            <div className="modern-hero">
                <div className="modern-hero-icon">🏠</div>
                <h1 className="modern-hero-title">Address Processing</h1>
                <p className="modern-hero-subtitle">Standardize and validate addresses with AI-powered processing</p>
            </div>

            {/* Main Card */}
            <div className="modern-card">
                {/* Info Cards */}
                <div className="modern-info-cards">
                    <div className="modern-info-card modern-info-card-blue">
                        <div className="modern-info-card-icon">🎯</div>
                        <div className="modern-info-card-content">
                            <div className="modern-info-card-title">Single or Batch</div>
                            <div className="modern-info-card-text">Process one address or multiple addresses at once</div>
                        </div>
                    </div>
                    
                    <div className="modern-info-card modern-info-card-green">
                        <div className="modern-info-card-icon">✨</div>
                        <div className="modern-info-card-content">
                            <div className="modern-info-card-title">AI-Powered</div>
                            <div className="modern-info-card-text">Advanced standardization with confidence scoring</div>
                        </div>
                    </div>
                </div>

                {/* Mode Toggle */}
                <div className="mode-toggle-section">
                    <label className="modern-label">Processing Mode</label>
                    <div className="mode-toggle">
                        <button 
                            className={`mode-btn ${mode === 'single' ? 'active' : ''}`} 
                            onClick={() => setMode('single')} 
                            disabled={processing}
                        >
                            Single Address
                        </button>
                        <button 
                            className={`mode-btn ${mode === 'multi' ? 'active' : ''}`} 
                            onClick={() => setMode('multi')} 
                            disabled={processing}
                        >
                            Multiple Addresses
                        </button>
                    </div>
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
                        disabled={processing || loadingModels}
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

                {/* Input Section */}
                <div className="input-section">
                    <label htmlFor="address-input" className="modern-label">
                        {mode === 'single' ? 'Enter Address:' : 'Enter Addresses (one per line):'}
                    </label>
                    <textarea
                        id="address-input"
                        value={inputAddress}
                        onChange={handleInputChange}
                        placeholder={mode === 'single' 
                            ? '123 Main St, New York, NY 10001' 
                            : '123 Main St, New York, NY 10001\nBPTP Capital City, Noida\nAnother Address...'}
                        disabled={processing}
                        className="modern-textarea"
                        rows={mode === 'single' ? 4 : 8}
                    />
                    {mode === 'multi' && (
                        <small className="input-hint">Each non-empty line will be processed. Blank lines are ignored.</small>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                    <button 
                        onClick={handleProcess} 
                        disabled={!inputAddress.trim() || processing} 
                        className="modern-btn modern-btn-primary"
                    >
                        {processing && <span className="modern-btn-spinner" />}
                        <span>{processing ? 'Processing...' : mode === 'single' ? 'Process Address' : 'Process Addresses'}</span>
                    </button>
                    
                    <button
                        onClick={handleReset}
                        disabled={processing}
                        className="modern-btn modern-btn-gray"
                    >
                        Reset
                    </button>
                </div>

                {/* Loading State */}
                {processing && (
                    <div className="processing-indicator">
                        <div className="processing-spinner"></div>
                        <p className="processing-text">Processing your {mode === 'single' ? 'address' : 'addresses'}...</p>
                    </div>
                )}

                {/* Single Result */}
                {processedAddress && !multiResults && (
                    <div className="result-card result-success">
                        <div className="result-header-row">
                            <div>
                                <div className="result-icon">✓</div>
                                <h3 className="result-title">Standardized Address</h3>
                            </div>
                            <button 
                                onClick={() => handleCopyResult()} 
                                className="copy-button"
                                title="Copy standardized address"
                            >
                                📋 Copy
                            </button>
                        </div>
                        <textarea 
                            value={processedAddress} 
                            disabled 
                            className="result-textarea" 
                            rows={3} 
                        />
                    </div>
                )}

                {/* Multi Results */}
                {multiResults && multiResults.length > 0 && (
                    <div className="multi-results-section">
                        <h3 className="multi-results-title">Results ({multiResults.length})</h3>
                        <div className="multi-results-grid">
                            {multiResults.map((r, i) => (
                                <div key={i} className={`multi-result-card status-${r.status}`}>
                                    <div className="card-header">
                                        <span className="result-badge index">#{i + 1}</span>
                                        <span className={`result-badge status ${r.status}`}>{r.status}</span>
                                    </div>
                                    <div className="card-content">
                                        <div className="address-row">
                                            <strong className="address-label">Input:</strong>
                                            <span className="address-value">{r.originalAddress}</span>
                                        </div>
                                        <div className="address-row">
                                            <strong className="address-label">Output:</strong>
                                            <span className="address-value">{r.processedAddress}</span>
                                        </div>
                                    </div>
                                    <div className="card-meta">
                                        <span className="meta-chip source">{r.source}</span>
                                        <span className="meta-chip confidence">Confidence: {r.confidence}</span>
                                    </div>
                                    <div className="card-actions">
                                        <button 
                                            onClick={() => handleCopyResult(r.processedAddress)} 
                                            className="action-copy-btn"
                                        >
                                            📋 Copy
                                        </button>
                                        {r.error && (
                                            <span className="error-badge" title={r.error}>
                                                ⚠ {r.error}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Error Result */}
                {error && (
                    <div className="result-card result-error">
                        <div className="result-icon">✕</div>
                        <h3 className="result-title">Error</h3>
                        <p className="result-message">{error}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AddressProcessing;
