import { configureStore } from '@reduxjs/toolkit';
import { createEpicMiddleware } from 'redux-observable';
import { combineReducers } from 'redux';
import fileUploadReducer from './slices/fileUploadSlice';
import addressProcessingReducer from './slices/addressProcessingSlice';
import { rootEpic } from './epics';
import { RootState } from '../types';
import { AnyAction } from '@reduxjs/toolkit';

const rootReducer = combineReducers({
    fileUpload: fileUploadReducer,
    addressProcessing: addressProcessingReducer,
});

const epicMiddleware = createEpicMiddleware<AnyAction, AnyAction, RootState>();

export const store = configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            thunk: false,
        }).concat(epicMiddleware),
});

epicMiddleware.run(rootEpic);

export type AppDispatch = typeof store.dispatch;
export type { RootState };
