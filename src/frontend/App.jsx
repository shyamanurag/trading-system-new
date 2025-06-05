import React, { useState } from 'react';
import EliteDashboard from './components/EliteDashboard';
import './App.css';

const App = () => {
    const [activeTab, setActiveTab] = useState('elite');

    const tabs = [
        { id: 'elite', label: 'Elite Trades', icon: '⭐' },
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'settings', label: 'Settings', icon: '⚙️' }
    ];

    return (
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
                {activeTab === 'elite' && <EliteDashboard />}
                {activeTab === 'dashboard' && (
                    <div className="placeholder">
                        <h2>Dashboard Coming Soon</h2>
                        <p>This section will contain your main trading dashboard.</p>
                    </div>
                )}
                {activeTab === 'settings' && (
                    <div className="placeholder">
                        <h2>Settings</h2>
                        <p>Configure your trading system preferences here.</p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default App; 