import { combineEpics } from 'redux-observable';
import { uploadFileEpic, checkProcessingStatusEpic, downloadFileEpic } from './fileUploadEpic';
import { processAddressEpic } from './addressProcessingEpic';

export const rootEpic = combineEpics(
    uploadFileEpic,
    checkProcessingStatusEpic,
    downloadFileEpic,
    processAddressEpic
);
