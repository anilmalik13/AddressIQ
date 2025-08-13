import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { FileUploadState, ProcessingStatus } from '../../types';

const initialState: FileUploadState = {
    uploading: false,
    uploadProgress: 0,
    uploadResult: null,
    error: null,
    processingId: null,
    processingStatus: null,
};

const fileUploadSlice = createSlice({
    name: 'fileUpload',
    initialState,
    reducers: {
        uploadFileRequest: (state, action: PayloadAction<File>) => {
            state.uploading = true;
            state.uploadProgress = 0;
            state.error = null;
            state.uploadResult = null;
        },
        uploadFileProgress: (state, action: PayloadAction<number>) => {
            state.uploadProgress = action.payload;
        },
        uploadFileSuccess: (state, action: PayloadAction<{message: string, processingId: string}>) => {
            state.uploading = false;
            state.uploadProgress = 100;
            state.uploadResult = action.payload.message;
            state.processingId = action.payload.processingId;
            state.error = null;
        },
        uploadFileFailure: (state, action: PayloadAction<string>) => {
            state.uploading = false;
            state.uploadProgress = 0;
            state.error = action.payload;
            state.uploadResult = null;
            state.processingId = null;
            state.processingStatus = null;
        },
        checkProcessingStatusRequest: (state, action: PayloadAction<string>) => {
            // No state change needed for request
        },
        updateProcessingStatus: (state, action: PayloadAction<ProcessingStatus>) => {
            state.processingStatus = action.payload;
        },
        downloadProcessedFileRequest: (state, action: PayloadAction<string>) => {
            // No state change needed for download request
        },
        resetUploadState: (state) => {
            state.uploading = false;
            state.uploadProgress = 0;
            state.error = null;
            state.uploadResult = null;
            state.processingId = null;
            state.processingStatus = null;
        },
    },
});

export const {
    uploadFileRequest,
    uploadFileProgress,
    uploadFileSuccess,
    uploadFileFailure,
    checkProcessingStatusRequest,
    updateProcessingStatus,
    downloadProcessedFileRequest,
    resetUploadState,
} = fileUploadSlice.actions;

// Action creators for use in epics
export const checkProcessingStatus = (processingId: string) => 
    checkProcessingStatusRequest(processingId);

export const downloadProcessedFile = (filename: string) => 
    downloadProcessedFileRequest(filename);

export default fileUploadSlice.reducer;
