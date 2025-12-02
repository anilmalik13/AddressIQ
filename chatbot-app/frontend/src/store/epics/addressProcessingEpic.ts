import { Epic } from 'redux-observable';
import { from, of } from 'rxjs';
import { map, mergeMap, catchError, takeUntil } from 'rxjs/operators';
import {
    processAddressRequest,
    processAddressesRequest,
    processAddressSuccess,
    processAddressesSuccess,
    processAddressFailure,
} from '../slices/addressProcessingSlice';
import { processAddress, processAddresses } from '../../services/api';
import { RootState } from '../../types';
import { AnyAction } from '@reduxjs/toolkit';

export const processAddressEpic: Epic<AnyAction, AnyAction, RootState> = (action$) =>
    action$.pipe(
        mergeMap((action) => {
            if (processAddressRequest.match(action)) {
                const { address, model } = action.payload;
                // Single address mode
                return from(processAddress(address, model)).pipe(
                    map((result) => processAddressSuccess({
                        processedAddress: result.processedAddress || address,
                        components: result.components || {},
                        confidence: result.confidence || 'unknown',
                        source: result.source || 'unknown'
                    })),
                    catchError((error) => of(processAddressFailure(error.message || 'Address processing failed'))),
                    takeUntil(action$.pipe(
                        mergeMap((nextAction) => processAddressRequest.match(nextAction) ? of(nextAction) : of())
                    ))
                );
            } else if (processAddressesRequest.match(action)) {
                const { addresses, model } = action.payload;
                return from(processAddresses(addresses, model)).pipe(
                    map((results) => processAddressesSuccess(results)),
                    catchError((error) => of(processAddressFailure(error.message || 'Multi-address processing failed'))),
                    takeUntil(action$.pipe(
                        mergeMap((nextAction) => (processAddressesRequest.match(nextAction) || processAddressRequest.match(nextAction)) ? of(nextAction) : of())
                    ))
                );
            }
            return of();
        })
    );
