import { Epic } from 'redux-observable';
import { from, of } from 'rxjs';
import { map, mergeMap, catchError, takeUntil } from 'rxjs/operators';
import {
    uploadFileRequest,
    uploadFileSuccess,
    uploadFileFailure,
    checkProcessingStatusRequest,
    updateProcessingStatus,
    downloadProcessedFileRequest,
} from '../slices/fileUploadSlice';
import { uploadExcelFile, checkProcessingStatus, downloadFile } from '../../services/api';
import { RootState } from '../../types';
import { AnyAction } from '@reduxjs/toolkit';

export const uploadFileEpic: Epic<AnyAction, AnyAction, RootState> = (action$) =>
    action$.pipe(
        mergeMap((action) => {
            if (uploadFileRequest.match(action)) {
                const file = action.payload;
                
                return from(
                    uploadExcelFile(file, (progress) => {
                        // This will be handled by a separate observable for progress updates
                    })
                ).pipe(
                    map((result) => {
                        // Expecting result to have { message, processing_id }
                        return uploadFileSuccess({
                            message: result.message,
                            processingId: result.processing_id
                        });
                    }),
                    catchError((error) =>
                        of(uploadFileFailure(error.message || 'File upload failed'))
                    ),
                    takeUntil(action$.pipe(
                        mergeMap((nextAction) => {
                            if (uploadFileRequest.match(nextAction)) {
                                return of(nextAction);
                            }
                            return of();
                        })
                    ))
                );
            }
            return of();
        })
    );

export const checkProcessingStatusEpic: Epic<AnyAction, AnyAction, RootState> = (action$) =>
    action$.pipe(
        mergeMap((action) => {
            if (checkProcessingStatusRequest.match(action)) {
                const processingId = action.payload;
                
                return from(checkProcessingStatus(processingId)).pipe(
                    map((status) => updateProcessingStatus(status)),
                    catchError((error) => {
                        console.error('Failed to check processing status:', error);
                        return of(); // Don't propagate errors for status checks
                    })
                );
            }
            return of();
        })
    );

export const downloadFileEpic: Epic<AnyAction, AnyAction, RootState> = (action$) =>
    action$.pipe(
        mergeMap((action) => {
            if (downloadProcessedFileRequest.match(action)) {
                const filename = action.payload;
                
                return from(downloadFile(filename)).pipe(
                    map(() => {
                        // Download completed successfully
                        return { type: 'DOWNLOAD_SUCCESS' };
                    }),
                    catchError((error) => {
                        console.error('Download failed:', error);
                        return of({ type: 'DOWNLOAD_FAILURE', payload: error.message });
                    })
                );
            }
            return of();
        })
    );
