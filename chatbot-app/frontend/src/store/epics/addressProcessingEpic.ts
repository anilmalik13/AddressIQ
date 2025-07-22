import { Epic } from 'redux-observable';
import { from, of } from 'rxjs';
import { map, mergeMap, catchError, takeUntil } from 'rxjs/operators';
import {
    processAddressRequest,
    processAddressSuccess,
    processAddressFailure,
} from '../slices/addressProcessingSlice';
import { processAddress } from '../../services/api';
import { RootState } from '../../types';
import { AnyAction } from '@reduxjs/toolkit';

export const processAddressEpic: Epic<AnyAction, AnyAction, RootState> = (action$) =>
    action$.pipe(
        mergeMap((action) => {
            if (processAddressRequest.match(action)) {
                const address = action.payload;
                
                return from(processAddress(address)).pipe(
                    map((result) => processAddressSuccess(result)),
                    catchError((error) =>
                        of(processAddressFailure(error.message || 'Address processing failed'))
                    ),
                    takeUntil(action$.pipe(
                        mergeMap((nextAction) => {
                            if (processAddressRequest.match(nextAction)) {
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
