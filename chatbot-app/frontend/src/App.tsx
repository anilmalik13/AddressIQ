import React, { useState, useMemo } from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import FileUpload from './components/FileUpload';
import AddressProcessing from './components/AddressProcessing';
import RegionCityMap from './components/RegionCityMap';
import PublicAPI from './components/PublicAPI/PublicAPI';
import CompareUpload from './components/CompareUpload/CompareUpload';
import './App.css';

type ActiveView = 'upload' | 'processing' | 'map' | 'publicapi' | 'compare';

const App: React.FC = () => {
    const [activeView, setActiveView] = useState<ActiveView>('upload');

    const renderActiveView = () => {
        switch (activeView) {
            case 'upload':
                return <FileUpload />;
            case 'processing':
                return <AddressProcessing />;
            case 'map':
                return <RegionCityMap />;
            case 'publicapi':
                return <PublicAPI />;
            case 'compare':
                return <CompareUpload />;
            default:
                return <FileUpload />;
        }
    };

    const getViewTitle = () => {
        switch (activeView) {
            case 'upload':
                return 'Excel File Upload';
            case 'processing':
                return 'Address Processing';
            case 'map':
                return 'Region & City Map View';
            case 'publicapi':
                return 'Public API';
            case 'compare':
                return 'Compare Upload';
            default:
                return 'Excel File Upload';
        }
    };

    const TABS = useMemo(
        () => [
            { key: 'upload', label: 'File Upload' },
            { key: 'compare', label: 'Compare Upload' },
            { key: 'processing', label: 'Address Processing' },
            { key: 'map', label: 'Map View' },
            { key: 'publicapi', label: 'Public API' },
        ],
        []
    );

    return (
        <Provider store={store}>
            <div className="App">
                <header className="app-header">
                    <h1>AddressIQ</h1>
                    <p>Intelligent Address Processing System</p>
                    <div className="view-tabs">
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                className={`tab ${
                                    activeView === tab.key ? 'active' : ''
                                }`}
                                onClick={() => setActiveView(tab.key as ActiveView)}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </header>

                <main className="app-main">
                    <div className="current-view">
                        <h2>{getViewTitle()}</h2>
                        {renderActiveView()}
                    </div>
                </main>
            </div>
        </Provider>
    );
};

export default App;