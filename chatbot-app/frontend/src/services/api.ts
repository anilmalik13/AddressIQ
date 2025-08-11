import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});

// File Upload API
export const uploadExcelFile = async (file: File, onProgress?: (progress: number) => void): Promise<string> => {
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

        return response.data.message || 'File uploaded successfully';
    } catch (error: any) {
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('File upload failed. Please try again.');
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
        const response = await api.post('/api/process-address', {
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

// Region-Country Coordinates API
export const getCoordinatesByRegionCountry = async (region: string, country: string) => {
    const response = await api.get('/api/coordinates', {
        params: { region, country }
    });
    return response.data;
};

export default api;