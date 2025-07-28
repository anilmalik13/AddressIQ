import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { FileUploadState } from '../../types';

const initialState: FileUploadState = {
    uploading: false,
    uploadProgress: 0,
    uploadResult: null,
    error: null,
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
        uploadFileSuccess: (state, action: PayloadAction<string>) => {
            state.uploading = false;
            state.uploadProgress = 100;
            state.uploadResult = action.payload;
            state.error = null;
        },
        uploadFileFailure: (state, action: PayloadAction<string>) => {
            state.uploading = false;
            state.uploadProgress = 0;
            state.error = action.payload;
            state.uploadResult = null;
        },
        resetUploadState: (state) => {
            state.uploading = false;
            state.uploadProgress = 0;
            state.error = null;
            state.uploadResult = null;
        },
    },
});

export const {
    uploadFileRequest,
    uploadFileProgress,
    uploadFileSuccess,
    uploadFileFailure,
    resetUploadState,
} = fileUploadSlice.actions;

export default fileUploadSlice.reducer;
