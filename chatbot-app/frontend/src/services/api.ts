import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});

export const sendMessage = async (userContent: string, systemPrompt?: string) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat`, {
            message: userContent,
            system_prompt: systemPrompt
        }, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        return response.data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
};

// File Upload API
export const uploadExcelFile = async (file: File, onProgress?: (progress: number) => void): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);

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
};

// Address Processing API
export const processAddress = async (address: string): Promise<string> => {
    const response = await api.post('/process-address', {
        address: address,
    });

    return response.data.processedAddress || response.data.message;
};

// Region-Country Coordinates API
export const getCoordinatesByRegionCountry = async (region: string, country: string) => {
    const response = await api.get('/coordinates', {
        params: { region, country }
    });
    return response.data;
};

export default api;