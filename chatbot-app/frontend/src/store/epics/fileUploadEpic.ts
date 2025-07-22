import { Epic } from 'redux-observable';
import { from, of } from 'rxjs';
import { map, mergeMap, catchError, takeUntil } from 'rxjs/operators';
import {
    uploadFileRequest,
    uploadFileSuccess,
    uploadFileFailure,
} from '../slices/fileUploadSlice';
import { uploadExcelFile } from '../../services/api';
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
                    map((result) => uploadFileSuccess(result)),
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
