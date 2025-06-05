import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import React, { useState } from 'react';
import './App.css';
import EliteDashboard from './components/EliteDashboard';
import TradingDashboard from './components/TradingDashboard';

const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#dc004e',
        },
    },
});

const App = () => {
    const [activeTab, setActiveTab] = useState('dashboard');

    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'elite', label: 'Elite Trades', icon: '⭐' },
        { id: 'settings', label: 'Settings', icon: '⚙️' }
    ];

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <div className="app">
                <nav className="sidebar">
                    <div className="logo">
                        <h1>Trading System</h1>
                    </div>
                    <div className="tabs">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <span className="tab-icon">{tab.icon}</span>
                                <span className="tab-label">{tab.label}</span>
                            </button>
                        ))}
                    </div>
                </nav>

                <main className="content">
                    {activeTab === 'dashboard' && <TradingDashboard />}
                    {activeTab === 'elite' && <EliteDashboard />}
                    {activeTab === 'settings' && (
                        <div className="placeholder">
                            <h2>Settings</h2>
                            <p>Configure your trading system preferences here.</p>
                        </div>
                    )}
                </main>
            </div>
        </ThemeProvider>
    );
};

export default App; 