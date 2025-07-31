import React, { useEffect, useState } from 'react';
import './ZerodhaManualAuth.css';

const ZerodhaManualAuth = () => {
    const [authUrl, setAuthUrl] = useState('');
    const [requestToken, setRequestToken] = useState('');
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [instructions, setInstructions] = useState([]);
    const [componentLoading, setComponentLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchAuthUrl = async () => {
        try {
            const response = await fetch('/auth/zerodha/auth-url');

            if (response.status === 404) {
                // Fallback when endpoints not deployed yet
                setAuthUrl(`https://kite.zerodha.com/connect/login?api_key=${import.meta.env.VITE_ZERODHA_API_KEY || 'vc9ft4zpknynpm3u'}`);
                setInstructions([
                    "1. Click the authorization URL below",
                    "2. Login to Zerodha with your credentials",
                    "3. After login, you'll be redirected to a URL",
                    "4. Copy the 'request_token' parameter from the redirected URL",
                    "5. Paste the token in the manual token entry below"
                ]);
                return;
            }

            const data = await response.json();
            if (data.success) {
                setAuthUrl(data.auth_url);
                setInstructions(data.instructions);
            }
        } catch (error) {
            console.error('Failed to fetch auth URL:', error);
            // Fallback URL
            setAuthUrl('https://kite.zerodha.com/connect/login?api_key=vc9ft4zpknynpm3u');
            setInstructions([
                "1. Click the authorization URL below",
                "2. Login to Zerodha with your credentials",
                "3. Copy the 'request_token' from the redirect URL",
                "4. Paste it below"
            ]);
        }
    };

    const checkStatus = async () => {
        try {
            const response = await fetch('/auth/zerodha/status');

            if (response.status === 404) {
                // Fallback status when endpoints not deployed yet
                setStatus({
                    success: true,
                    message: "Auth system starting up - endpoints deploying...",
                    authenticated: false,
                    user_id: "QSW899",
                    note: "Backend deployment in progress"
                });
                return;
            }

            const data = await response.json();
            setStatus(data);
        } catch (error) {
            console.error('Failed to check status:', error);
            setStatus({
                success: false,
                message: "Connection error - check network",
                authenticated: false,
                user_id: "QSW899"
            });
        }
    };

    const submitToken = async () => {
        if (!requestToken.trim()) {
            alert('Please enter a request token');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/auth/zerodha/submit-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_token: requestToken.trim(),
                    user_id: 'QSW899'
                })
            });

            if (response.status === 404) {
                alert('Auth endpoints are deploying... Please try again in a few minutes when deployment completes.');
                setLoading(false);
                return;
            }

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
            alert('Error submitting token: ' + error.message + ' - Check if endpoints are deployed');
        }
        setLoading(false);
    };

    const testConnection = async () => {
        setLoading(true);
        try {
            const response = await fetch('/auth/zerodha/test-connection');
            const data = await response.json();

            if (data.success) {
                alert(`🔴 LIVE CONNECTION SUCCESSFUL!\nUser: ${data.profile.user_name}\nReal-time market access enabled`);
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
            const response = await fetch('/auth/zerodha/logout', {
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

    useEffect(() => {
        let isMounted = true;

        const initializeComponent = async () => {
            try {
                if (!isMounted) return;

                await fetchAuthUrl();
                if (!isMounted) return;

                await checkStatus();
                if (!isMounted) return;

                setComponentLoading(false);
            } catch (err) {
                if (!isMounted) return;
                setError('Failed to initialize auth component: ' + (err?.message || 'Unknown error'));
                setComponentLoading(false);
            }
        };

        initializeComponent();

        return () => {
            isMounted = false;
        };
    }, []);

    if (componentLoading) {
        return (
            <div className="zerodha-manual-auth">
                <div className="auth-container">
                    <h2>🔐 Loading Zerodha Auth...</h2>
                    <p>Initializing authentication interface...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="zerodha-manual-auth">
                <div className="auth-container">
                    <h2>🔐 Zerodha Manual Authentication</h2>
                    <div className="status-card not-authenticated">
                        <h3>⚠️ Initialization Error</h3>
                        <p>{error}</p>
                        <p><strong>Note:</strong> Backend might still be deploying. Please try again in a few minutes.</p>
                        <button
                            onClick={() => window.location.reload()}
                            className="refresh-button"
                            style={{ marginTop: '10px' }}
                        >
                            🔄 Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="zerodha-manual-auth">
            <div className="auth-container">
                <h2>🔐 Zerodha Manual Authentication</h2>

                {/* Status Display */}
                {status ? (
                    <div className={`status-card ${status.authenticated ? 'authenticated' : 'not-authenticated'}`}>
                        <h3>Current Status</h3>
                        <p><strong>Authenticated:</strong> {status.authenticated ? '✅ Yes' : '❌ No'}</p>
                        {status.user_id && <p><strong>User ID:</strong> {status.user_id}</p>}
                        {status.token_expires_at && <p><strong>Expires:</strong> {status.token_expires_at}</p>}
                        <p><strong>Message:</strong> {status.message}</p>
                    </div>
                ) : (
                    <div className="status-card not-authenticated">
                        <h3>⏳ Checking Status...</h3>
                        <p>Connecting to authentication server...</p>
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