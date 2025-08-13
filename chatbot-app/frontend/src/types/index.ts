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