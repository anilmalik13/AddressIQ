import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { FileUploadState, ProcessingStatus, Job } from '../../types';

const initialState: FileUploadState = {
    uploading: false,
    uploadProgress: 0,
    uploadResult: null,
    error: null,
    processingId: null,
    processingStatus: null,
    // Job history tracking
    jobHistory: [],
    loadingJobs: false,
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
        // Job history actions
        loadJobHistoryRequest: (state) => {
            state.loadingJobs = true;
        },
        loadJobHistorySuccess: (state, action: PayloadAction<Job[]>) => {
            state.jobHistory = action.payload;
            state.loadingJobs = false;
        },
        loadJobHistoryFailure: (state) => {
            state.loadingJobs = false;
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
    loadJobHistoryRequest,
    loadJobHistorySuccess,
    loadJobHistoryFailure,
} = fileUploadSlice.actions;

// Action creators for use in epics
export const checkProcessingStatus = (processingId: string) => 
    checkProcessingStatusRequest(processingId);

export const downloadProcessedFile = (filename: string) => 
    downloadProcessedFileRequest(filename);

export const loadJobHistory = () => loadJobHistoryRequest();

export default fileUploadSlice.reducer;
