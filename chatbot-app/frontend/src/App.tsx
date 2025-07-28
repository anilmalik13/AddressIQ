import React, { useState } from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import FileUpload from './components/FileUpload';
import AddressProcessing from './components/AddressProcessing';
import RegionCityMap from './components/RegionCityMap';
import './App.css';

type ActiveView = 'upload' | 'processing' | 'map';

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
            default:
                return 'Excel File Upload';
        }
    };

    return (
        <Provider store={store}>
            <div className="App">
                <header className="app-header">
                    <h1>AddressIQ</h1>
                    <p>Intelligent Address Processing System</p>
                    <div className="view-tabs">
                        <button 
                            className={`tab ${activeView === 'upload' ? 'active' : ''}`}
                            onClick={() => setActiveView('upload')}
                        >
                            File Upload
                        </button>
                        <button 
                            className={`tab ${activeView === 'processing' ? 'active' : ''}`}
                            onClick={() => setActiveView('processing')}
                        >
                            Address Processing
                        </button>
                        <button 
                            className={`tab ${activeView === 'map' ? 'active' : ''}`}
                            onClick={() => setActiveView('map')}
                        >
                            Map View
                        </button>
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