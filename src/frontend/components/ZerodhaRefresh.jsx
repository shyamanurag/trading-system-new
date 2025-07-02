import React, { useEffect, useState } from 'react';
import './ZerodhaRefresh.css';

const ZerodhaRefresh = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [requestToken, setRequestToken] = useState('');
    const [authUrl, setAuthUrl] = useState('');
    const [showTokenForm, setShowTokenForm] = useState(false);
    const [message, setMessage] = useState('');

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/zerodha/refresh/status');
            const data = await response.json();
            setStatus(data);
        } catch (error) {
            console.error('Status check failed:', error);
            setMessage('Failed to check status');
        } finally {
            setLoading(false);
        }
    };

    const refreshToken = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/zerodha/refresh/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    force_refresh: false,
                    user_id: 'QSW899'
                })
            });
            const data = await response.json();

            if (data.success && data.auth_url) {
                setAuthUrl(data.auth_url);
                setShowTokenForm(true);
                setMessage('Please login to Zerodha and provide the request token');
            } else {
                setMessage(data.message || 'Refresh failed');
            }
        } catch (error) {
            console.error('Refresh failed:', error);
            setMessage('Refresh failed');
        } finally {
            setLoading(false);
        }
    };

    const submitToken = async () => {
        if (!requestToken.trim()) {
            setMessage('Please enter a request token');
            return;
        }

        try {
            setLoading(true);
            const response = await fetch('/api/zerodha/refresh/submit-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_token: requestToken,
                    user_id: 'QSW899'
                })
            });
            const data = await response.json();

            if (data.success) {
                setMessage('Token refreshed successfully!');
                setShowTokenForm(false);
                setRequestToken('');
                checkStatus(); // Refresh status
            } else {
                setMessage(data.error || 'Token submission failed');
            }
        } catch (error) {
            console.error('Token submission failed:', error);
            setMessage('Token submission failed');
        } finally {
            setLoading(false);
        }
    };

    const testConnection = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/zerodha/refresh/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: 'QSW899'
                })
            });
            const data = await response.json();

            if (data.success) {
                setMessage('Connection test successful!');
            } else {
                setMessage(data.message || 'Connection test failed');
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            setMessage('Connection test failed');
        } finally {
            setLoading(false);
        }
    };

    const openAuthUrl = () => {
        if (authUrl) {
            window.open(authUrl, '_blank');
        }
    };

    return (
        <div className="zerodha-refresh">
            <h2>🔄 Zerodha Connection Refresh</h2>

            {message && (
                <div className={`message ${message.includes('successful') ? 'success' : 'error'}`}>
                    {message}
                </div>
            )}

            <div className="status-section">
                <h3>Current Status</h3>
                {loading ? (
                    <div className="loading">Loading...</div>
                ) : status ? (
                    <div className="status-details">
                        <div className="status-item">
                            <span className="label">Token Valid:</span>
                            <span className={`value ${status.token_valid ? 'valid' : 'invalid'}`}>
                                {status.token_valid ? '✅ Yes' : '❌ No'}
                            </span>
                        </div>
                        {status.token_expires_at && (
                            <div className="status-item">
                                <span className="label">Expires At:</span>
                                <span className="value">{new Date(status.token_expires_at).toLocaleString()}</span>
                            </div>
                        )}
                        <div className="status-item">
                            <span className="label">Trading Ready:</span>
                            <span className={`value ${status.trading_ready ? 'ready' : 'not-ready'}`}>
                                {status.trading_ready ? '✅ Ready' : '❌ Not Ready'}
                            </span>
                        </div>
                        {status.profile && (
                            <div className="status-item">
                                <span className="label">User:</span>
                                <span className="value">{status.profile.user_name || 'Unknown'}</span>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="error">Failed to load status</div>
                )}
            </div>

            <div className="actions-section">
                <h3>Actions</h3>
                <div className="action-buttons">
                    <button
                        onClick={checkStatus}
                        disabled={loading}
                        className="btn btn-secondary"
                    >
                        🔄 Refresh Status
                    </button>

                    <button
                        onClick={refreshToken}
                        disabled={loading}
                        className="btn btn-primary"
                    >
                        🔑 Refresh Token
                    </button>

                    <button
                        onClick={testConnection}
                        disabled={loading}
                        className="btn btn-info"
                    >
                        🧪 Test Connection
                    </button>
                </div>
            </div>

            {showTokenForm && (
                <div className="token-form">
                    <h3>Submit Request Token</h3>
                    <div className="form-group">
                        <label htmlFor="requestToken">Request Token:</label>
                        <input
                            type="text"
                            id="requestToken"
                            value={requestToken}
                            onChange={(e) => setRequestToken(e.target.value)}
                            placeholder="Enter request token from Zerodha"
                            className="form-control"
                        />
                    </div>
                    <div className="form-actions">
                        <button
                            onClick={openAuthUrl}
                            className="btn btn-secondary"
                        >
                            🔗 Open Zerodha Login
                        </button>
                        <button
                            onClick={submitToken}
                            disabled={loading || !requestToken.trim()}
                            className="btn btn-success"
                        >
                            ✅ Submit Token
                        </button>
                        <button
                            onClick={() => setShowTokenForm(false)}
                            className="btn btn-danger"
                        >
                            ❌ Cancel
                        </button>
                    </div>
                </div>
            )}

            {status && status.connection_status && (
                <div className="connection-details">
                    <h3>Connection Details</h3>
                    <div className="connection-grid">
                        <div className="connection-item">
                            <span className="label">Token Exists:</span>
                            <span className={`value ${status.connection_status.token_exists ? 'yes' : 'no'}`}>
                                {status.connection_status.token_exists ? '✅' : '❌'}
                            </span>
                        </div>
                        <div className="connection-item">
                            <span className="label">API Accessible:</span>
                            <span className={`value ${status.connection_status.api_accessible ? 'yes' : 'no'}`}>
                                {status.connection_status.api_accessible ? '✅' : '❌'}
                            </span>
                        </div>
                        <div className="connection-item">
                            <span className="label">WebSocket Connected:</span>
                            <span className={`value ${status.connection_status.websocket_connected ? 'yes' : 'no'}`}>
                                {status.connection_status.websocket_connected ? '✅' : '❌'}
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ZerodhaRefresh; 