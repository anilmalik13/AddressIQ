import axios from 'axios';

// Bypass proxy: call backend directly. Allow override via REACT_APP_API_BASE_URL.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});

// File Upload API
export const uploadExcelFile = async (file: File, onProgress?: (progress: number) => void): Promise<{message: string, processing_id: string}> => {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await api.post('/upload-excel', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (onProgress && progressEvent.total) {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    onProgress(progress);
                }
            },
        });

        return {
            message: response.data.message || 'File uploaded successfully',
            processing_id: response.data.processing_id
        };
    } catch (error: any) {
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('File upload failed. Please try again.');
    }
};

// Check processing status
export const checkProcessingStatus = async (processingId: string) => {
    try {
        const response = await api.get(`/processing-status/${processingId}`);
        return response.data;
    } catch (error: any) {
        console.error('Error checking processing status:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Failed to check processing status');
    }
};

// Download processed file
export const downloadFile = async (filename: string) => {
    try {
        const response = await api.get(`/download/${filename}`, {
            responseType: 'blob'
        });
        
        // Create blob link to download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        
        // Clean up
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        return true;
    } catch (error: any) {
        console.error('Error downloading file:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Failed to download file');
    }
};

// Get list of uploaded files
export const getUploadedFiles = async () => {
    try {
        const response = await api.get('/uploaded-files');
        return response.data.files || [];
    } catch (error: any) {
        console.error('Error fetching uploaded files:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Failed to fetch uploaded files');
    }
};

// Address Processing API
export const processAddress = async (address: string): Promise<any> => {
    try {
        // baseURL already '/api', so just use endpoint path without duplicate '/api'
    const response = await api.post('/process-address', {
            address: address,
        });

        return {
            processedAddress: response.data.processedAddress || response.data.message,
            confidence: response.data.confidence || 'unknown',
            components: response.data.components || {},
            source: response.data.source || 'unknown',
            status: response.data.status || 'unknown',
            error: response.data.error || null
        };
    } catch (error: any) {
        console.error('Error processing address:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Address processing failed. Please try again.');
    }
};

// Multiple Addresses Processing API
export const processAddresses = async (addresses: string[]): Promise<any[]> => {
    try {
        const response = await api.post('/process-addresses', { addresses });
        return (response.data.results || []).map((r: any) => ({
            originalAddress: r.originalAddress,
            processedAddress: r.processedAddress,
            status: r.status,
            confidence: r.confidence,
            source: r.source,
            components: r.components || {},
            error: r.error || null
        }));
    } catch (error: any) {
        console.error('Error processing multiple addresses:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Multi-address processing failed.');
    }
};

// Region-Country Coordinates API
export const getCoordinatesByRegionCountry = async (region: string, country: string) => {
    // Remove duplicate '/api' because baseURL is '/api'
    const response = await api.get('/coordinates', {
        params: { region, country }
    });
    return response.data;
};

export default api;