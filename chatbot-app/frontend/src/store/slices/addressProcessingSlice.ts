import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AddressProcessingState } from '../../types';

const initialState: AddressProcessingState = {
    processing: false,
    originalAddress: '',
    processedAddress: null,
    error: null,
};

const addressProcessingSlice = createSlice({
    name: 'addressProcessing',
    initialState,
    reducers: {
        processAddressRequest: (state, action: PayloadAction<string>) => {
            state.processing = true;
            state.originalAddress = action.payload;
            state.processedAddress = null;
            state.error = null;
        },
        processAddressSuccess: (state, action: PayloadAction<string>) => {
            state.processing = false;
            state.processedAddress = action.payload;
            state.error = null;
        },
        processAddressFailure: (state, action: PayloadAction<string>) => {
            state.processing = false;
            state.error = action.payload;
            state.processedAddress = null;
        },
        resetAddressState: (state) => {
            state.processing = false;
            state.originalAddress = '';
            state.processedAddress = null;
            state.error = null;
        },
    },
});

export const {
    processAddressRequest,
    processAddressSuccess,
    processAddressFailure,
    resetAddressState,
} = addressProcessingSlice.actions;

export default addressProcessingSlice.reducer;
