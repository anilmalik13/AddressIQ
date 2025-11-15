export interface User {
    id: string;
    name: string;
}

export interface ProcessingStatus {
    status: 'uploaded' | 'queued' | 'processing' | 'completed' | 'error' | 'failed';
    message: string;
    progress: number;
    output_file?: string;
    error?: string;
    filename?: string;
    original_filename?: string;
    file_info?: { rows: number; columns: number; column_names: string[] };
    started_at?: string;
    updated_at?: string;
    finished_at?: string | null;
    expires_at?: string | null;
    logs?: { ts: string; message: string; progress?: number }[];
    steps?: { name: string; label: string; target: number }[];
}

export interface Job {
    job_id: string;
    status: 'queued' | 'processing' | 'completed' | 'failed' | 'error';
    filename: string;
    component?: string;
    progress: number;
    created_at: string;
    updated_at?: string;
    finished_at?: string;
    expires_at?: string;
    download_url?: string;
    output_file?: string;
    error?: string;
}

export interface FileUploadState {
    uploading: boolean;
    uploadProgress: number;
    uploadResult: string | null;
    error: string | null;
    processingId: string | null;
    processingStatus: ProcessingStatus | null;
    // Job history tracking
    jobHistory: Job[];
    loadingJobs: boolean;
}

export interface AddressProcessingState {
    processing: boolean;
    originalAddress: string;
    processedAddress: string | null;
    addressComponents: Record<string, string> | null;
    confidence: string | null;
    source: string | null;
    error: string | null;
    multiResults?: ProcessedAddressResult[] | null;
}

export interface ProcessedAddressResult {
    originalAddress: string;
    processedAddress: string;
    status: string;
    confidence: string;
    source: string;
    components: Record<string, string>;
    error?: string | null;
}

export interface RootState {
    fileUpload: FileUploadState;
    addressProcessing: AddressProcessingState;
}

export interface ApiResponse {
    choices: {
        message: {
            content: string;
            role: string;
        };
    }[];
}