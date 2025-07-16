import { CheckCircle, Error, Info, Warning } from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Container,
    TextField,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import './ZerodhaManualAuth.css';
// UNIFIED: Import standardized user utilities
import {
    getContextualDisplayName,
    getContextualUserId,
    USER_CONFIG
} from '../utils/userUtils';

const ZerodhaManualAuth = () => {
    const [requestToken, setRequestToken] = useState('');
    const [status, setStatus] = useState({
        connected: false,
        loading: false,
        error: null,
        success: null,
        // UNIFIED: Use consistent user identification
        user_id: getContextualUserId('zerodha'),
        display_name: getContextualDisplayName(USER_CONFIG.ZERODHA_USER_ID)
    });
    const [authUrl, setAuthUrl] = useState('');

    useEffect(() => {
        checkConnectionStatus();
        generateAuthUrl();
    }, []);

    const checkConnectionStatus = async () => {
        try {
            // UNIFIED: Use standardized Zerodha user ID
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch(`/auth/zerodha/status?user_id=${zerodhaUserId}`);
            const data = await response.json();

            setStatus(prev => ({
                ...prev,
                connected: data.connected || false,
                // UNIFIED: Use consistent user identification
                user_id: zerodhaUserId,
                display_name: getContextualDisplayName(zerodhaUserId),
                token_expiry: data.token_expiry,
                last_update: data.last_update
            }));
        } catch (error) {
            console.error('Error checking connection status:', error);
            setStatus(prev => ({
                ...prev,
                error: 'Failed to check connection status'
            }));
        }
    };

    const generateAuthUrl = async () => {
        try {
            const response = await fetch('/auth/zerodha/auth-url');
            const data = await response.json();
            if (data.auth_url) {
                setAuthUrl(data.auth_url);
            }
        } catch (error) {
            console.error('Error generating auth URL:', error);
        }
    };

    const handleSubmitToken = async () => {
        if (!requestToken.trim()) {
            setStatus(prev => ({
                ...prev,
                error: 'Please enter a request token'
            }));
            return;
        }

        setStatus(prev => ({
            ...prev,
            loading: true,
            error: null,
            success: null
        }));

        try {
            // UNIFIED: Use standardized Zerodha user ID consistently
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch('/auth/zerodha/submit-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_token: requestToken,
                    // UNIFIED: Use consistent user identification
                    user_id: zerodhaUserId
                })
            });

            const data = await response.json();

            if (data.success) {
                setStatus(prev => ({
                    ...prev,
                    loading: false,
                    connected: true,
                    success: 'Authentication successful! Token saved.',
                    // UNIFIED: Update with consistent user data
                    user_id: zerodhaUserId,
                    display_name: getContextualDisplayName(zerodhaUserId),
                    token_expiry: data.token_expiry,
                    last_update: new Date().toISOString()
                }));
                setRequestToken('');
            } else {
                setStatus(prev => ({
                    ...prev,
                    loading: false,
                    error: data.message || 'Authentication failed'
                }));
            }
        } catch (error) {
            console.error('Error submitting token:', error);
            setStatus(prev => ({
                ...prev,
                loading: false,
                error: 'Network error. Please try again.'
            }));
        }
    };

    const handleTestConnection = async () => {
        setStatus(prev => ({
            ...prev,
            loading: true,
            error: null
        }));

        try {
            // UNIFIED: Use standardized Zerodha user ID
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch(`/auth/zerodha/test-connection?user_id=${zerodhaUserId}`);
            const data = await response.json();

            setStatus(prev => ({
                ...prev,
                loading: false,
                success: data.success ? 'Connection test successful!' : null,
                error: data.success ? null : (data.message || 'Connection test failed'),
                connected: data.success
            }));
        } catch (error) {
            console.error('Error testing connection:', error);
            setStatus(prev => ({
                ...prev,
                loading: false,
                error: 'Failed to test connection'
            }));
        }
    };

    const handleLogout = async () => {
        try {
            // UNIFIED: Use standardized Zerodha user ID
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch(`/auth/zerodha/logout?user_id=${zerodhaUserId}`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                setStatus(prev => ({
                    ...prev,
                    connected: false,
                    success: 'Logged out successfully',
                    error: null,
                    user_id: zerodhaUserId,
                    display_name: getContextualDisplayName(zerodhaUserId)
                }));
            } else {
                setStatus(prev => ({
                    ...prev,
                    error: data.message || 'Logout failed'
                }));
            }
        } catch (error) {
            console.error('Error logging out:', error);
            setStatus(prev => ({
                ...prev,
                error: 'Failed to logout'
            }));
        }
    };

    return (
        <Container maxWidth="md" className="zerodha-auth-container">
            <Box sx={{ py: 4 }}>
                <Typography variant="h4" gutterBottom align="center" className="auth-title">
                    🔐 Zerodha Manual Authentication
                </Typography>

                <Typography variant="subtitle1" align="center" color="text.secondary" sx={{ mb: 4 }}>
                    {/* UNIFIED: Use consistent display name */}
                    Secure daily authentication for {status.display_name || USER_CONFIG.DISPLAY_NAMES.ZERODHA}
                </Typography>

                {/* Status Display */}
                <Card sx={{ mb: 3 }} className="status-card">
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            {status.connected ? (
                                <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
                            ) : (
                                <Error sx={{ color: 'error.main', mr: 1 }} />
                            )}
                            <Typography variant="h6">
                                Status: {status.connected ? 'Connected' : 'Disconnected'}
                            </Typography>
                        </Box>

                        {/* UNIFIED: Display consistent user information */}
                        {status.user_id && (
                            <Typography variant="body2" color="text.secondary">
                                <strong>User ID:</strong> {status.user_id}
                            </Typography>
                        )}
                        {status.display_name && (
                            <Typography variant="body2" color="text.secondary">
                                <strong>Account:</strong> {status.display_name}
                            </Typography>
                        )}
                        {status.token_expiry && (
                            <Typography variant="body2" color="text.secondary">
                                <strong>Token Expires:</strong> {new Date(status.token_expiry).toLocaleString()}
                            </Typography>
                        )}
                        {status.last_update && (
                            <Typography variant="body2" color="text.secondary">
                                <strong>Last Updated:</strong> {new Date(status.last_update).toLocaleString()}
                            </Typography>
                        )}
                    </CardContent>
                </Card>

                {/* Authentication Form */}
                {!status.connected && (
                    <Card sx={{ mb: 3 }} className="auth-form-card">
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Daily Authentication Required
                            </Typography>

                            <Box sx={{ mb: 3 }}>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    1. Click the button below to open Zerodha login
                                </Typography>
                                <Button
                                    variant="outlined"
                                    href={authUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    disabled={!authUrl}
                                    sx={{ mb: 2 }}
                                >
                                    Open Zerodha Login
                                </Button>

                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    2. After logging in, copy the request_token from the URL and paste below:
                                </Typography>

                                <TextField
                                    fullWidth
                                    label="Request Token"
                                    variant="outlined"
                                    value={requestToken}
                                    onChange={(e) => setRequestToken(e.target.value)}
                                    placeholder="Enter request_token from Zerodha URL"
                                    disabled={status.loading}
                                    sx={{ mb: 2 }}
                                />

                                <Button
                                    variant="contained"
                                    onClick={handleSubmitToken}
                                    disabled={status.loading || !requestToken.trim()}
                                    startIcon={status.loading ? <CircularProgress size={20} /> : null}
                                    fullWidth
                                >
                                    {status.loading ? 'Authenticating...' : 'Submit Token'}
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                )}

                {/* Connected Actions */}
                {status.connected && (
                    <Card sx={{ mb: 3 }} className="connected-actions-card">
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Connection Actions
                            </Typography>

                            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                <Button
                                    variant="outlined"
                                    onClick={handleTestConnection}
                                    disabled={status.loading}
                                    startIcon={status.loading ? <CircularProgress size={20} /> : null}
                                >
                                    Test Connection
                                </Button>

                                <Button
                                    variant="outlined"
                                    color="error"
                                    onClick={handleLogout}
                                >
                                    Logout
                                </Button>

                                <Button
                                    variant="outlined"
                                    onClick={checkConnectionStatus}
                                >
                                    Refresh Status
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                )}

                {/* Status Messages */}
                {status.error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {status.error}
                    </Alert>
                )}

                {status.success && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                        {status.success}
                    </Alert>
                )}

                {/* Instructions */}
                <Card className="instructions-card">
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <Info sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Important Instructions
                        </Typography>

                        <Box component="ul" sx={{ pl: 2 }}>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                Zerodha tokens expire daily at 6:00 AM IST
                            </Typography>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                You need to authenticate once per day for live trading
                            </Typography>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                {/* UNIFIED: Use consistent user identification */}
                                All trades will be executed through your {USER_CONFIG.ZERODHA_USER_ID} account
                            </Typography>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                Keep your login credentials secure and never share tokens
                            </Typography>
                        </Box>

                        <Alert severity="warning" sx={{ mt: 2 }}>
                            <Typography variant="body2">
                                <Warning sx={{ mr: 1, verticalAlign: 'middle' }} />
                                This is your live trading account. All orders will be real trades.
                            </Typography>
                        </Alert>
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
};

export default ZerodhaManualAuth; 