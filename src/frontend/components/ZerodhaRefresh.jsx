import { CheckCircle, Error, Refresh, Warning } from '@mui/icons-material';
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
import './ZerodhaRefresh.css';
// UNIFIED: Import standardized user utilities
import {
    getContextualDisplayName,
    getContextualUserId,
    USER_CONFIG
} from '../utils/userUtils';

const ZerodhaRefresh = () => {
    const [requestToken, setRequestToken] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState({
        connected: false,
        message: '',
        error: null,
        // UNIFIED: Use consistent user identification
        user_id: getContextualUserId('zerodha'),
        display_name: getContextualDisplayName(USER_CONFIG.ZERODHA_USER_ID)
    });

    useEffect(() => {
        checkTokenStatus();
    }, []);

    const checkTokenStatus = async () => {
        try {
            // UNIFIED: Use standardized Zerodha user ID
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch(`/api/zerodha-daily-auth/status?user_id=${zerodhaUserId}`);

            if (response.ok) {
                const data = await response.json();
                setStatus(prev => ({
                    ...prev,
                    connected: data.authenticated || false,
                    message: data.message || '',
                    // UNIFIED: Update with consistent user data
                    user_id: zerodhaUserId,
                    display_name: getContextualDisplayName(zerodhaUserId),
                    token_expiry: data.token_expiry,
                    last_refresh: data.last_refresh
                }));
            } else {
                setStatus(prev => ({
                    ...prev,
                    connected: false,
                    error: 'Failed to check token status'
                }));
            }
        } catch (error) {
            console.error('Error checking token status:', error);
            setStatus(prev => ({
                ...prev,
                connected: false,
                error: 'Network error while checking status'
            }));
        }
    };

    const handleRefreshToken = async () => {
        if (!requestToken.trim()) {
            setStatus(prev => ({
                ...prev,
                error: 'Please enter a request token'
            }));
            return;
        }

        setLoading(true);
        setStatus(prev => ({
            ...prev,
            error: null,
            message: ''
        }));

        try {
            // UNIFIED: Use standardized Zerodha user ID consistently
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch('/api/zerodha-daily-auth/refresh', {
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

            if (response.ok && data.success) {
                setStatus(prev => ({
                    ...prev,
                    connected: true,
                    message: 'Token refreshed successfully! Trading is now active.',
                    // UNIFIED: Update with consistent user data
                    user_id: zerodhaUserId,
                    display_name: getContextualDisplayName(zerodhaUserId),
                    token_expiry: data.token_expiry,
                    last_refresh: new Date().toISOString()
                }));
                setRequestToken('');
            } else {
                setStatus(prev => ({
                    ...prev,
                    connected: false,
                    error: data.message || 'Token refresh failed'
                }));
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            setStatus(prev => ({
                ...prev,
                connected: false,
                error: 'Network error during token refresh'
            }));
        } finally {
            setLoading(false);
        }
    };

    const handleTestConnection = async () => {
        setLoading(true);

        try {
            // UNIFIED: Use standardized Zerodha user ID
            const zerodhaUserId = getContextualUserId('zerodha');
            const response = await fetch(`/api/zerodha-daily-auth/test?user_id=${zerodhaUserId}`);
            const data = await response.json();

            setStatus(prev => ({
                ...prev,
                connected: data.success || false,
                message: data.success ? 'Connection test successful!' : '',
                error: data.success ? null : (data.message || 'Connection test failed')
            }));
        } catch (error) {
            console.error('Error testing connection:', error);
            setStatus(prev => ({
                ...prev,
                connected: false,
                error: 'Failed to test connection'
            }));
        } finally {
            setLoading(false);
        }
    };

    const getLoginUrl = () => {
        // This would typically be generated by your backend
        const apiKey = 'vc9ft4zpknynpm3u'; // This should come from backend config
        return `https://kite.trade/connect/login?api_key=${apiKey}&v=3`;
    };

    return (
        <Container maxWidth="md" className="zerodha-refresh-container">
            <Box sx={{ py: 4 }}>
                <Typography variant="h4" gutterBottom align="center">
                    🔄 Zerodha Token Refresh
                </Typography>

                <Typography variant="subtitle1" align="center" color="text.secondary" sx={{ mb: 4 }}>
                    {/* UNIFIED: Use consistent display name */}
                    Daily authentication refresh for {status.display_name || USER_CONFIG.DISPLAY_NAMES.ZERODHA}
                </Typography>

                {/* Current Status Card */}
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            {status.connected ? (
                                <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
                            ) : (
                                <Error sx={{ color: 'error.main', mr: 1 }} />
                            )}
                            <Typography variant="h6">
                                Authentication Status: {status.connected ? 'Active' : 'Expired'}
                            </Typography>
                        </Box>

                        {/* UNIFIED: Display consistent user information */}
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            <strong>User ID:</strong> {status.user_id}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            <strong>Account:</strong> {status.display_name}
                        </Typography>
                        {status.token_expiry && (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                <strong>Token Expires:</strong> {new Date(status.token_expiry).toLocaleString()}
                            </Typography>
                        )}
                        {status.last_refresh && (
                            <Typography variant="body2" color="text.secondary">
                                <strong>Last Refreshed:</strong> {new Date(status.last_refresh).toLocaleString()}
                            </Typography>
                        )}
                    </CardContent>
                </Card>

                {/* Token Refresh Form */}
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Refresh Authentication Token
                        </Typography>

                        <Alert severity="info" sx={{ mb: 3 }}>
                            <Typography variant="body2">
                                Zerodha tokens expire daily at 6:00 AM IST. You need to refresh your token
                                to continue live trading operations.
                            </Typography>
                        </Alert>

                        <Box sx={{ mb: 3 }}>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                                <strong>Step 1:</strong> Click below to open Zerodha login page
                            </Typography>
                            <Button
                                variant="outlined"
                                href={getLoginUrl()}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{ mb: 3 }}
                            >
                                Open Zerodha Login
                            </Button>

                            <Typography variant="body2" sx={{ mb: 2 }}>
                                <strong>Step 2:</strong> After successful login, copy the request_token from the redirected URL
                            </Typography>

                            <TextField
                                fullWidth
                                label="Request Token"
                                variant="outlined"
                                value={requestToken}
                                onChange={(e) => setRequestToken(e.target.value)}
                                placeholder="Paste the request_token from the URL here"
                                disabled={loading}
                                sx={{ mb: 2 }}
                            />

                            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                <Button
                                    variant="contained"
                                    onClick={handleRefreshToken}
                                    disabled={loading || !requestToken.trim()}
                                    startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
                                >
                                    {loading ? 'Refreshing...' : 'Refresh Token'}
                                </Button>

                                <Button
                                    variant="outlined"
                                    onClick={handleTestConnection}
                                    disabled={loading}
                                    startIcon={loading ? <CircularProgress size={20} /> : null}
                                >
                                    Test Connection
                                </Button>

                                <Button
                                    variant="outlined"
                                    onClick={checkTokenStatus}
                                    disabled={loading}
                                >
                                    Check Status
                                </Button>
                            </Box>
                        </Box>
                    </CardContent>
                </Card>

                {/* Status Messages */}
                {status.error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {status.error}
                    </Alert>
                )}

                {status.message && !status.error && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                        {status.message}
                    </Alert>
                )}

                {/* Instructions */}
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            📝 Daily Authentication Guide
                        </Typography>

                        <Box component="ol" sx={{ pl: 2 }}>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                <strong>Login to Zerodha:</strong> Use the "Open Zerodha Login" button above
                            </Typography>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                <strong>Complete 2FA:</strong> Enter your credentials and complete two-factor authentication
                            </Typography>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                <strong>Copy Token:</strong> After successful login, copy the request_token from the URL
                            </Typography>
                            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                                <strong>Paste & Submit:</strong> Paste the token above and click "Refresh Token"
                            </Typography>
                            <Typography component="li" variant="body2">
                                <strong>Verify:</strong> Use "Test Connection" to ensure everything is working
                            </Typography>
                        </Box>

                        <Alert severity="warning" sx={{ mt: 2 }}>
                            <Typography variant="body2">
                                <Warning sx={{ mr: 1, verticalAlign: 'middle' }} />
                                {/* UNIFIED: Use consistent user identification */}
                                Remember: All trades execute through your live {USER_CONFIG.ZERODHA_USER_ID} account.
                                Ensure you're ready for live trading before refreshing the token.
                            </Typography>
                        </Alert>
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
};

export default ZerodhaRefresh; 