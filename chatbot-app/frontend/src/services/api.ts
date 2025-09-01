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

// Upload for batch compare
export const uploadCompareFile = async (file: File, onProgress?: (progress: number) => void): Promise<{message: string, processing_id: string}> => {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await api.post('/upload-compare', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (pe) => {
                if (onProgress && pe.total) {
                    const progress = Math.round((pe.loaded * 100) / pe.total);
                    onProgress(progress);
                }
            },
        });
        return {
            message: response.data.message || 'Compare started',
            processing_id: response.data.processing_id
        };
    } catch (error: any) {
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Compare upload failed. Please try again.');
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

// Preview processed file rows for display in UI
export const previewResultFile = async (
    filename: string,
    pageOrLimit: number = 1,
    pageSize?: number
): Promise<{columns: string[]; rows: any[]; rowCount: number; filename: string; page?: number; pageSize?: number; totalRows?: number}> => {
    try {
        const params: any = {};
        if (pageSize != null) {
            params.page = pageOrLimit;
            params.page_size = pageSize;
        } else {
            // backward compat: send as limit
            params.limit = pageOrLimit;
        }
        const response = await api.get(`/preview/${encodeURIComponent(filename)}`, { params });
        return {
            columns: response.data.columns || [],
            rows: response.data.rows || [],
            rowCount: response.data.rowCount ?? (response.data.rows?.length || 0),
            filename: response.data.filename || filename,
            page: response.data.page,
            pageSize: response.data.pageSize,
            totalRows: response.data.totalRows,
        };
    } catch (error: any) {
        console.error('Error previewing file:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Failed to load preview data');
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

// Public standardization API (single/multiple)
export const processPublicStandardize = async (addresses: string[], apiKey?: string): Promise<{results: any[]}> => {
    try {
        const headers: any = {};
        if (apiKey) headers['X-API-Key'] = apiKey;
        const response = await api.post('/public/standardize', { addresses }, { headers });
        return response.data;
    } catch (error: any) {
        console.error('Error calling public standardize:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Public standardization failed.');
    }
};

// Database connect - frontend stubbed API
// This will call backend endpoints when available. For now, we simulate success.
export const submitDatabaseTask = async (payload: {
    mode: 'compare' | 'format';
    connectionString: string;
    sourceType: 'table' | 'query';
    tableName?: string; // optional database table name
    // Table mode
    uniqueId?: string; // optional primary key
    columnNames?: string[]; // required names, at least one
    // Query mode
    query?: string;
    action: 'format' | 'download';
}): Promise<{ message: string; output_file?: string }> => {
    try {
        // Kick off DB job
        const response = await api.post('/db/connect', {
            mode: payload.mode,
            connectionString: payload.connectionString,
            sourceType: payload.sourceType,
            tableName: payload.tableName,
            uniqueId: payload.uniqueId,
            columnNames: payload.columnNames,
            query: payload.query,
            // limit default 10 on backend
            action: payload.action,
        });
        return response.data;
    } catch (error: any) {
        console.error('Error submitting database task:', error);
        if (error.response?.data?.error) {
            throw new Error(error.response.data.error);
        }
        throw new Error('Failed to submit database task');
    }
};

// Poll DB processing status
export const getDbProcessingStatus = async (processingId: string) => {
    const res = await api.get(`/processing-status/${processingId}`);
    return res.data;
};

// Get processing logs (shared endpoint)
export const getProcessingLogs = async (processingId: string) => {
    const res = await api.get(`/processing-status/${processingId}/logs`);
    return res.data.logs as Array<{ ts: string; message: string; progress?: number }>;
};

// Download inbound file (reuses same download route)
export const downloadInboundFile = async (filename: string) => {
    return downloadFile(filename);
};

export default api;