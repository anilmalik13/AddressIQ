import React, { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { processAddressRequest, resetAddressState } from '../../store/slices/addressProcessingSlice';
import './AddressProcessing.css';

const AddressProcessing: React.FC = () => {
    const dispatch = useAppDispatch();
    const { processing, originalAddress, processedAddress, error } = useAppSelector(
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
            alert('Processed address copied to clipboard!');
        }
    }, [processedAddress]);

    return (
        <div className="address-processing-container">
            <div className="navigation">
                <Link to="/file-upload" className="nav-link">
                    ← Go to File Upload
                </Link>
            </div>
            
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

                    {originalAddress && processedAddress && (
                        <div className="result-section">
                            <div className="result success">
                                <h3>Processing Complete!</h3>
                                
                                <div className="address-comparison">
                                    <div className="original-address">
                                        <h4>Original Address:</h4>
                                        <p>{originalAddress}</p>
                                    </div>
                                    
                                    <div className="processed-address">
                                        <h4>Processed Address:</h4>
                                        <p>{processedAddress}</p>
                                        <button 
                                            onClick={handleCopyResult}
                                            className="copy-button"
                                        >
                                            Copy to Clipboard
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
