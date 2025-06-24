import React, { useEffect, useState } from 'react';
import './ZerodhaManualAuth.css';

const ZerodhaManualAuth = () => {
    const [authUrl, setAuthUrl] = useState('');
    const [requestToken, setRequestToken] = useState('');
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [instructions, setInstructions] = useState([]);

    useEffect(() => {
        fetchAuthUrl();
        checkStatus();
    }, []);

    const fetchAuthUrl = async () => {
        try {
            const response = await fetch('/zerodha-manual/auth-url');
            const data = await response.json();

            if (data.success) {
                setAuthUrl(data.auth_url);
                setInstructions(data.instructions);
            }
        } catch (error) {
            console.error('Failed to fetch auth URL:', error);
        }
    };

    const checkStatus = async () => {
        try {
            const response = await fetch('/zerodha-manual/status');
            const data = await response.json();
            setStatus(data);
        } catch (error) {
            console.error('Failed to check status:', error);
        }
    };

    const submitToken = async () => {
        if (!requestToken.trim()) {
            alert('Please enter a request token');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/zerodha-manual/submit-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_token: requestToken.trim(),
                    user_id: 'ZERODHA_DEFAULT'
                })
            });

            const data = await response.json();

            if (data.success) {
                alert('Token submitted successfully! Processing...');
                setRequestToken('');

                // Check status after a delay
                setTimeout(() => {
                    checkStatus();
                }, 3000);
            } else {
                alert('Failed to submit token: ' + data.message);
            }
        } catch (error) {
            alert('Error submitting token: ' + error.message);
        }
        setLoading(false);
    };

    const testConnection = async () => {
        setLoading(true);
        try {
            const response = await fetch('/zerodha-manual/test-connection');
            const data = await response.json();

            if (data.success) {
                alert(`Connection successful!\nUser: ${data.profile.user_name}\nSample NIFTY LTP: ${data.sample_data.ltp}`);
            } else {
                alert('Connection test failed: ' + data.message);
            }
        } catch (error) {
            alert('Connection test error: ' + error.message);
        }
        setLoading(false);
    };

    const logout = async () => {
        setLoading(true);
        try {
            const response = await fetch('/zerodha-manual/logout', {
                method: 'DELETE'
            });
            const data = await response.json();

            if (data.success) {
                alert('Logged out successfully');
                setStatus(null);
                checkStatus();
            }
        } catch (error) {
            alert('Logout failed: ' + error.message);
        }
        setLoading(false);
    };

    return (
        <div className="zerodha-manual-auth">
            <div className="auth-container">
                <h2>🔐 Zerodha Manual Authentication</h2>

                {/* Status Display */}
                {status && (
                    <div className={`status-card ${status.authenticated ? 'authenticated' : 'not-authenticated'}`}>
                        <h3>Current Status</h3>
                        <p><strong>Authenticated:</strong> {status.authenticated ? '✅ Yes' : '❌ No'}</p>
                        {status.user_id && <p><strong>User ID:</strong> {status.user_id}</p>}
                        {status.token_expires_at && <p><strong>Expires:</strong> {status.token_expires_at}</p>}
                        <p><strong>Message:</strong> {status.message}</p>
                    </div>
                )}

                {/* Authentication Steps */}
                {!status?.authenticated && (
                    <div className="auth-steps">
                        <h3>📋 Authentication Steps</h3>
                        <div className="instructions">
                            {instructions.map((instruction, index) => (
                                <div key={index} className="instruction-step">
                                    <span className="step-number">{index + 1}</span>
                                    <span className="step-text">{instruction}</span>
                                </div>
                            ))}
                        </div>

                        {/* Auth URL Button */}
                        <div className="auth-url-section">
                            <h4>Step 1: Get Authorization URL</h4>
                            {authUrl && (
                                <a
                                    href={authUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="auth-url-button"
                                >
                                    🔗 Open Zerodha Authorization
                                </a>
                            )}
                            <p className="note">
                                <strong>Note:</strong> After login, copy the 'request_token' from the redirected URL
                            </p>
                        </div>

                        {/* Token Input */}
                        <div className="token-input-section">
                            <h4>Step 2: Enter Request Token</h4>
                            <div className="token-input-group">
                                <input
                                    type="text"
                                    value={requestToken}
                                    onChange={(e) => setRequestToken(e.target.value)}
                                    placeholder="Paste your request_token here..."
                                    className="token-input"
                                    disabled={loading}
                                />
                                <button
                                    onClick={submitToken}
                                    disabled={loading || !requestToken.trim()}
                                    className="submit-button"
                                >
                                    {loading ? '⏳ Processing...' : '🚀 Submit Token'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Authenticated Actions */}
                {status?.authenticated && (
                    <div className="authenticated-actions">
                        <h3>✅ Authenticated Successfully</h3>
                        <div className="action-buttons">
                            <button
                                onClick={testConnection}
                                disabled={loading}
                                className="test-button"
                            >
                                {loading ? '⏳ Testing...' : '🧪 Test Connection'}
                            </button>
                            <button
                                onClick={logout}
                                disabled={loading}
                                className="logout-button"
                            >
                                {loading ? '⏳ Logging out...' : '🚪 Logout'}
                            </button>
                        </div>

                        <div className="info-box">
                            <h4>📊 Data Sources</h4>
                            <p><strong>TrueData:</strong> Primary (Fast, Real-time)</p>
                            <p><strong>Zerodha:</strong> Secondary (Slower, for trading)</p>
                            <p><strong>Note:</strong> Zerodha tokens expire daily at 6:00 AM IST</p>
                        </div>
                    </div>
                )}

                {/* Refresh Button */}
                <div className="refresh-section">
                    <button
                        onClick={checkStatus}
                        disabled={loading}
                        className="refresh-button"
                    >
                        {loading ? '⏳ Checking...' : '🔄 Refresh Status'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ZerodhaManualAuth; 