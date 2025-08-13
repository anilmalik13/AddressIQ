import React, { useCallback, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { processAddressRequest, processAddressesRequest, resetAddressState } from '../../store/slices/addressProcessingSlice';
import './AddressProcessing.css';

const AddressProcessing: React.FC = () => {
    const dispatch = useAppDispatch();
    const { processing, processedAddress, error, multiResults } = useAppSelector((state) => state.addressProcessing);
    const [inputAddress, setInputAddress] = useState<string>('');
    const [mode, setMode] = useState<'single' | 'multi'>('multi');

    const handleInputChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputAddress(event.target.value);
    }, []);

    const handleProcess = useCallback(() => {
        const trimmed = inputAddress.trim();
        if (!trimmed) return;
        if (mode === 'single') {
            dispatch(processAddressRequest(trimmed));
        } else {
            // Split by newlines, filter empties
            const list = trimmed.split(/\r?\n/).map(a => a.trim()).filter(a => a.length > 0);
            if (list.length === 1) {
                dispatch(processAddressRequest(list[0]));
            } else if (list.length > 1) {
                dispatch(processAddressesRequest(list));
            }
        }
    }, [dispatch, inputAddress, mode]);

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
        <div className="address-processing-container">
            <div className="address-processing-card">
                <h1>Address Processing</h1>
                <p>Enter one or multiple addresses (one per line) to standardize them.</p>
                <div className="mode-toggle">
                    <button className={mode==='single'? 'active': ''} onClick={() => setMode('single')} disabled={processing}>Single</button>
                    <button className={mode==='multi'? 'active': ''} onClick={() => setMode('multi')} disabled={processing}>Multiple</button>
                </div>
                
                <div className="processing-section">
                    <div className="input-section">
                        <label htmlFor="address-input">{mode==='single' ? 'Enter Address:' : 'Enter Addresses (one per line):'}</label>
                        <textarea
                            id="address-input"
                            value={inputAddress}
                            onChange={handleInputChange}
                            placeholder={mode==='single' ? '123 Main St, New York, NY 10001' : '123 Main St, New York, NY 10001\nBPTP Capital City, Noida\nAnother Address...'}
                            disabled={processing}
                            className="address-input"
                            rows={mode==='single' ? 4 : 8}
                        />
                        {mode==='multi' && (
                            <small className="hint">Each non-empty line will be processed. Blank lines are ignored.</small>
                        )}
                    </div>

                    <div className="button-group">
                        <button onClick={handleProcess} disabled={!inputAddress.trim() || processing} className="process-button">
                            {processing ? 'Processing...' : mode==='single' ? 'Process Address' : 'Process Addresses'}
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
                            <div className="loading-spinner" />
                            <p>Processing your address...</p>
                        </div>
                    )}

                    {processedAddress && !multiResults && (
                        <div className="result-section">
                            <div className="result success single-result">
                                <div className="result-header">
                                    <h3>Standardized Address</h3>
                                    <button onClick={() => handleCopyResult()} className="copy-result-button" title="Copy standardized address">📋 Copy</button>
                                </div>
                                <textarea value={processedAddress} disabled className="address-result" rows={3} />
                            </div>
                        </div>
                    )}

                    {multiResults && multiResults.length > 0 && (
                        <div className="multi-results-wrapper">
                            <h3>Results ({multiResults.length})</h3>
                            <div className="multi-results-grid">
                                {multiResults.map((r, i) => (
                                    <div key={i} className={`multi-result-card ${r.status}`}>
                                        <div className="card-top">
                                            <span className="badge index">#{i+1}</span>
                                            <span className={`badge status ${r.status}`}>{r.status}</span>
                                        </div>
                                        <div className="original"><strong>Input:</strong> {r.originalAddress}</div>
                                        <div className="processed"><strong>Output:</strong> {r.processedAddress}</div>
                                        <div className="meta">
                                            <span className="chip source">{r.source}</span>
                                            <span className="chip confidence">conf: {r.confidence}</span>
                                        </div>
                                        <div className="actions-row">
                                            <button onClick={() => handleCopyResult(r.processedAddress)} className="mini-btn">Copy</button>
                                            {r.error && <span className="error-text" title={r.error}>⚠ {r.error}</span>}
                                        </div>
                                    </div>
                                ))}
                            </div>
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

export default AddressProcessing;
