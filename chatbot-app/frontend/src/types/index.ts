export interface User {
    id: string;
    name: string;
}

export interface FileUploadState {
    uploading: boolean;
    uploadProgress: number;
    uploadResult: string | null;
    error: string | null;
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