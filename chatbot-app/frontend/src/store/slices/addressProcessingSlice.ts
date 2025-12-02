import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AddressProcessingState, ProcessedAddressResult } from '../../types';

const initialState: AddressProcessingState = {
    processing: false,
    originalAddress: '',
    processedAddress: null,
    addressComponents: null,
    confidence: null,
    source: null,
    error: null,
    multiResults: null,
};

const addressProcessingSlice = createSlice({
    name: 'addressProcessing',
    initialState,
    reducers: {
        processAddressRequest: (state, action: PayloadAction<{address: string, model: string}>) => {
            state.processing = true;
            state.originalAddress = action.payload.address;
            state.processedAddress = null;
            state.addressComponents = null;
            state.confidence = null;
            state.source = null;
            state.error = null;
            state.multiResults = null;
        },
        processAddressesRequest: (state, action: PayloadAction<{addresses: string[], model: string}>) => {
            state.processing = true;
            state.originalAddress = action.payload.addresses.join('\n');
            state.processedAddress = null;
            state.addressComponents = null;
            state.confidence = null;
            state.source = null;
            state.error = null;
            state.multiResults = null;
        },
        processAddressSuccess: (state, action: PayloadAction<{
            processedAddress: string;
            components: Record<string, string>;
            confidence: string;
            source: string;
        }>) => {
            state.processing = false;
            state.processedAddress = action.payload.processedAddress;
            state.addressComponents = action.payload.components;
            state.confidence = action.payload.confidence;
            state.source = action.payload.source;
            state.error = null;
        },
        processAddressesSuccess: (state, action: PayloadAction<ProcessedAddressResult[]>) => {
            state.processing = false;
            state.multiResults = action.payload;
            state.processedAddress = null;
            state.addressComponents = null;
            state.confidence = null;
            state.source = null;
            state.error = null;
        },
        processAddressFailure: (state, action: PayloadAction<string>) => {
            state.processing = false;
            state.error = action.payload;
            state.processedAddress = null;
            state.addressComponents = null;
            state.confidence = null;
            state.source = null;
            state.multiResults = null;
        },
        resetAddressState: (state) => {
            state.processing = false;
            state.originalAddress = '';
            state.processedAddress = null;
            state.addressComponents = null;
            state.confidence = null;
            state.source = null;
            state.error = null;
            state.multiResults = null;
        },
    },
});

export const {
    processAddressRequest,
    processAddressesRequest,
    processAddressSuccess,
    processAddressesSuccess,
    processAddressFailure,
    resetAddressState,
} = addressProcessingSlice.actions;

export default addressProcessingSlice.reducer;
