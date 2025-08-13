export interface User {
    id: string;
    name: string;
}

export interface ProcessingStatus {
    status: 'uploaded' | 'processing' | 'completed' | 'error';
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
    logs?: { ts: string; message: string; progress?: number }[];
    steps?: { name: string; label: string; target: number }[];
}

export interface FileUploadState {
    uploading: boolean;
    uploadProgress: number;
    uploadResult: string | null;
    error: string | null;
    processingId: string | null;
    processingStatus: ProcessingStatus | null;
}

export interface AddressProcessingState {
    processing: boolean;
    originalAddress: string;
    processedAddress: string | null;
    addressComponents: Record<string, string> | null;
    confidence: string | null;
    source: string | null;
    error: string | null;
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