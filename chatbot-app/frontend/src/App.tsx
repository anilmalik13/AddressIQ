import React, { useEffect, useMemo, useState } from 'react';
import FileUpload from './components/FileUpload';
import AddressProcessing from './components/AddressProcessing';
import RegionCityMap from './components/RegionCityMap';
import PublicAPI from './components/PublicAPI/PublicAPI';
import CompareUpload from './components/CompareUpload/CompareUpload';
import DatabaseConnect from './components/DatabaseConnect';
import './App.css';

type ActiveView = 'upload' | 'compare' | 'processing' | 'map' | 'publicapi' | 'dbconnect';
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
        return saved === 'true';
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
            <div style={{ display: activeView === 'map' ? 'block' : 'none' }}>
                <RegionCityMap />
            </div>
            <div style={{ display: activeView === 'publicapi' ? 'block' : 'none' }}>
                <PublicAPI />
            </div>
            <div style={{ display: activeView === 'dbconnect' ? 'block' : 'none' }}>
                <DatabaseConnect />
            </div>
        </>
    );

    // page title is rendered by inner components; no top-level header text needed

    const TABS = useMemo(
        () => [
            { key: 'upload', label: 'File Upload', icon: 'upload' },
            { key: 'compare', label: 'Compare Upload', icon: 'compare' },
            { key: 'processing', label: 'Address Processing', icon: 'process' },
            { key: 'map', label: 'Map View', icon: 'map' },
            { key: 'publicapi', label: 'Public API', icon: 'api' },
            { key: 'dbconnect', label: 'Database connect', icon: 'db' },
        ],
        []
    );

    const Icon: React.FC<{ name: string }> = ({ name }) => {
        switch (name) {
            case 'upload':
                return (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                );
            case 'compare':
                return (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <path d="M10 3H5a2 2 0 0 0-2 2v5h7z" />
                        <path d="M14 21h5a2 2 0 0 0 2-2v-5h-7z" />
                        <path d="M21 8V7a2 2 0 0 0-2-2h-5" />
                        <path d="M3 16v1a2 2 0 0 0 2 2h5" />
                    </svg>
                );
            case 'process':
                return (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <path d="M3 12h3l3 7 4-14 3 7h5" />
                    </svg>
                );
            case 'map':
                return (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <polygon points="1 6 8 3 16 6 23 3 23 18 16 21 8 18 1 21" />
                        <line x1="8" y1="3" x2="8" y2="18" />
                        <line x1="16" y1="6" x2="16" y2="21" />
                    </svg>
                );
            case 'api':
                return (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <polyline points="4 17 10 11 4 5" />
                        <polyline points="20 17 14 11 20 5" />
                    </svg>
                );
            case 'db':
                return (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <ellipse cx="12" cy="5" rx="9" ry="3" />
                        <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" />
                        <path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3" />
                    </svg>
                );
            default:
                return null;
        }
    };

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
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                            <line x1="3" y1="6" x2="21" y2="6" />
                            <line x1="3" y1="12" x2="21" y2="12" />
                            <line x1="3" y1="18" x2="21" y2="18" />
                        </svg>
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
                            {/* Sun and Moon icons */}
                            <span className="theme-toggle__icon theme-toggle__icon--sun" aria-hidden>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="12" cy="12" r="4" />
                                    <line x1="12" y1="2" x2="12" y2="4" />
                                    <line x1="12" y1="20" x2="12" y2="22" />
                                    <line x1="4.93" y1="4.93" x2="6.34" y2="6.34" />
                                    <line x1="17.66" y1="17.66" x2="19.07" y2="19.07" />
                                    <line x1="2" y1="12" x2="4" y2="12" />
                                    <line x1="20" y1="12" x2="22" y2="12" />
                                    <line x1="4.93" y1="19.07" x2="6.34" y2="17.66" />
                                    <line x1="17.66" y1="6.34" x2="19.07" y2="4.93" />
                                </svg>
                            </span>
                            <span className="theme-toggle__icon theme-toggle__icon--moon" aria-hidden>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
                                </svg>
                            </span>
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
                                    <span className="nav__iconbox">
                                        <span className="nav__icon"><Icon name={tab.icon} /></span>
                                    </span>
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