import { combineEpics } from 'redux-observable';
import { uploadFileEpic } from './fileUploadEpic';
import { processAddressEpic } from './addressProcessingEpic';

export const rootEpic = combineEpics(
    uploadFileEpic,
    processAddressEpic
);
