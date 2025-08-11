import React, { useCallback, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { processAddressRequest, resetAddressState } from '../../store/slices/addressProcessingSlice';
import './AddressProcessing.css';

const AddressProcessing: React.FC = () => {
    const dispatch = useAppDispatch();
    const { processing, processedAddress, error } = useAppSelector(
        (state) => state.addressProcessing
    );
    const [inputAddress, setInputAddress] = useState<string>('');

    const handleInputChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputAddress(event.target.value);
    }, []);

    const handleProcessAddress = useCallback(() => {
        if (inputAddress.trim()) {
            dispatch(processAddressRequest(inputAddress.trim()));
        }
    }, [dispatch, inputAddress]);

    const handleReset = useCallback(() => {
        setInputAddress('');
        dispatch(resetAddressState());
    }, [dispatch]);

    const handleCopyResult = useCallback(() => {
        if (processedAddress) {
            navigator.clipboard.writeText(processedAddress);
            alert('✅ Processed address copied to clipboard!');
        }
    }, [processedAddress]);

    return (
        <div className="address-processing-container">
            <div className="address-processing-card">
                <h1>Address Processing</h1>
                <p>Enter an address in free text format to get it processed and standardized</p>
                
                <div className="processing-section">
                    <div className="input-section">
                        <label htmlFor="address-input">Enter Address:</label>
                        <textarea
                            id="address-input"
                            value={inputAddress}
                            onChange={handleInputChange}
                            placeholder="Enter your address here (e.g., 123 Main St, New York, NY 10001)"
                            disabled={processing}
                            className="address-input"
                            rows={4}
                        />
                    </div>

                    <div className="button-group">
                        <button
                            onClick={handleProcessAddress}
                            disabled={!inputAddress.trim() || processing}
                            className="process-button"
                        >
                            {processing ? 'Processing...' : 'Process Address'}
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

                    {processedAddress && (
                        <div className="result-section">
                            <div className="result success">
                                <h3>✅ Address Processed Successfully!</h3>
                                
                                <div className="processed-address-container">
                                    <label className="result-label">Standardized Address:</label>
                                    <div className="result-box">
                                        <textarea
                                            value={processedAddress}
                                            disabled
                                            className="address-result"
                                            rows={3}
                                            placeholder="Your processed address will appear here..."
                                        />
                                        <button 
                                            onClick={handleCopyResult}
                                            className="copy-result-button"
                                            title="Copy to clipboard"
                                        >
                                            📋 Copy
                                        </button>
                                    </div>
                                </div>
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
