import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import FileUpload from './components/FileUpload';
import AddressProcessing from './components/AddressProcessing';
import './App.css';

const App: React.FC = () => {
    return (
        <Provider store={store}>
            <Router>
                <div className="App">
                    <header className="app-header">
                        <h1>AddressIQ</h1>
                        <p>Intelligent Address Processing System</p>
                    </header>
                    
                    <main className="app-main">
                        <Routes>
                            <Route path="/" element={<Navigate to="/file-upload" replace />} />
                            <Route path="/file-upload" element={<FileUpload />} />
                            <Route path="/address-processing" element={<AddressProcessing />} />
                        </Routes>
                    </main>
                </div>
            </Router>
        </Provider>
    );
};

export default App;