import React, { useEffect, useMemo, useState } from 'react';
import FileUpload from './components/FileUpload';
import AddressProcessing from './components/AddressProcessing';
import AddressSplit from './components/AddressSplit';
import RegionCityMap from './components/RegionCityMap';
import PublicAPI from './components/PublicAPI/PublicAPI';
import CompareUpload from './components/CompareUpload/CompareUpload';
import DatabaseConnect from './components/DatabaseConnect';
import JobHistory from './components/JobHistory/JobHistory';
import './App.css';

type ActiveView = 'upload' | 'compare' | 'processing' | 'split' | 'map' | 'publicapi' | 'dbconnect' | 'jobs';
type Theme = 'light' | 'dark';

const App: React.FC = () => {
    const [activeView, setActiveView] = useState<ActiveView>('upload');
    const [theme, setTheme] = useState<Theme>(() => {
        const saved = typeof window !== 'undefined' ? (localStorage.getItem('aiq-theme') as Theme | null) : null;
        if (saved === 'light' || saved === 'dark') return saved;
        const prefersDark = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        return prefersDark ? 'dark' : 'light';
    });

    useEffect(() => {
        // Apply theme to root for CSS variable overrides
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('aiq-theme', theme);
    }, [theme]);

    const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

    // Collapsible sidebar state (persisted)
    const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
        const saved = typeof window !== 'undefined' ? localStorage.getItem('aiq-sidebar-collapsed') : null;
        return saved !== null ? saved === 'true' : true; // Default to collapsed (true)
    });
    useEffect(() => {
        localStorage.setItem('aiq-sidebar-collapsed', String(sidebarCollapsed));
    }, [sidebarCollapsed]);
    const toggleSidebar = () => setSidebarCollapsed((v) => !v);

    // Render all views but hide inactive ones to preserve state across tab switches.
    // This approach keeps components mounted so that:
    // - Upload/processing state is retained when switching tabs
    // - Background polling continues for active operations
    // - User can switch tabs and come back without losing progress
    // Components are hidden with display:none but remain in the DOM
    const renderAllViews = () => (
        <>
            <div style={{ display: activeView === 'upload' ? 'block' : 'none' }}>
                <FileUpload />
            </div>
            <div style={{ display: activeView === 'compare' ? 'block' : 'none' }}>
                <CompareUpload />
            </div>
            <div style={{ display: activeView === 'processing' ? 'block' : 'none' }}>
                <AddressProcessing />
            </div>
            <div style={{ display: activeView === 'split' ? 'block' : 'none' }}>
                <AddressSplit />
            </div>
            <div style={{ display: activeView === 'map' ? 'block' : 'none' }}>
                <RegionCityMap />
            </div>
            <div style={{ display: activeView === 'publicapi' ? 'block' : 'none' }}>
                <PublicAPI />
            </div>
            <div style={{ display: activeView === 'dbconnect' ? 'block' : 'none' }}>
                <DatabaseConnect />
            </div>
            <div style={{ display: activeView === 'jobs' ? 'block' : 'none' }}>
                <JobHistory />
            </div>
        </>
    );

    // page title is rendered by inner components; no top-level header text needed

    const TABS = useMemo(
        () => [
            { key: 'upload', label: 'File Upload' },
            { key: 'compare', label: 'Compare Upload' },
            { key: 'processing', label: 'Address Processing' },
            { key: 'split', label: 'Address Splitting' },
            { key: 'map', label: 'Map View' },
            { key: 'publicapi', label: 'Public API' },
            { key: 'dbconnect', label: 'Database connect' },
            { key: 'jobs', label: 'Processing History' },
        ],
        []
    );

    return (
        <div className="app-shell">
                {/* Top bar */}
                <header className="topbar" role="banner" aria-label="Application header">
                    <button
                        className="topbar__menu"
                        onClick={toggleSidebar}
                        aria-label={sidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'}
                        title={sidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'}
                    >
                        <span aria-hidden>☰</span>
                    </button>
                    <div className="topbar__brand" aria-label="Brand">CBRE AddressIQ</div>
                    <div className="topbar__actions">
                        <button
                            className="theme-toggle"
                            onClick={toggleTheme}
                            role="switch"
                            aria-checked={theme === 'dark'}
                            aria-label="Toggle dark mode"
                            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            <span aria-hidden>{theme === 'dark' ? '☀' : '☾'}</span>
                        </button>
                    </div>
                </header>

                {/* Main layout */}
                <div className={`layout ${sidebarCollapsed ? 'layout--collapsed' : ''}`}>
                    {/* Sidebar */}
                    <aside className="sidebar" role="navigation" aria-label="Primary">
                        <nav className="nav">
                {TABS.map((tab) => (
                                <button
                                    key={tab.key}
                                    className={`nav__item ${activeView === (tab.key as ActiveView) ? 'active' : ''}`}
                                    onClick={() => setActiveView(tab.key as ActiveView)}
                                    aria-current={activeView === (tab.key as ActiveView) ? 'page' : undefined}
                    data-tooltip={tab.label}
                                >
                                    <span className="nav__label">{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                        <div className="sidebar__footer">© {new Date().getFullYear()} CBRE, Inc.</div>
                    </aside>

                    {/* Content */}
                    <main className="content" role="main">
                        <div className="content__container">
                            <section className="card card--fill">
                                {renderAllViews()}
                            </section>
                        </div>
                    </main>
                </div>

                {/* Footer removed as per requirement */}
            </div>
    );
};

export default App;