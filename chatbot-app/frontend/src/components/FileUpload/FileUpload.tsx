import React, { useCallback, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { uploadFileRequest, resetUploadState } from '../../store/slices/fileUploadSlice';
import './FileUpload.css';

const FileUpload: React.FC = () => {
    const dispatch = useAppDispatch();
    const { uploading, uploadProgress, uploadResult, error } = useAppSelector(
        (state) => state.fileUpload
    );
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

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
    }, [dispatch]);

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
                            disabled={!selectedFile || uploading}
                            className="upload-button"
                        >
                            {uploading ? 'Uploading...' : 'Upload File'}
                        </button>
                        
                        <button
                            onClick={handleReset}
                            disabled={uploading}
                            className="reset-button"
                        >
                            Reset
                        </button>
                    </div>

                    {uploading && (
                        <div className="progress-section">
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill" 
                                    style={{ width: `${uploadProgress}%` }}
                                />
                            </div>
                            <p>{uploadProgress}% uploaded</p>
                        </div>
                    )}

                    {uploadResult && (
                        <div className="result success">
                            <h3>Success!</h3>
                            <p>{uploadResult}</p>
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

export default FileUpload;
