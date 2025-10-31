import { combineEpics } from 'redux-observable';
import { 
    uploadFileEpic, 
    checkProcessingStatusEpic, 
    downloadFileEpic,
    loadJobHistoryEpic
} from './fileUploadEpic';
import { processAddressEpic } from './addressProcessingEpic';

export const rootEpic = combineEpics(
    uploadFileEpic,
    checkProcessingStatusEpic,
    downloadFileEpic,
    loadJobHistoryEpic,
    processAddressEpic
);
