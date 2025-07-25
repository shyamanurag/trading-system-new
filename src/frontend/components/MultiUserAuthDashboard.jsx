import {
    CheckCircle,
    Refresh,
    Security,
    Warning
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    TextField,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';

const MultiUserAuthDashboard = ({ onAuthComplete }) => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [tokenInput, setTokenInput] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    useEffect(() => {
        fetchUsers();
        // Auto-refresh every 5 minutes to check token status
        const interval = setInterval(fetchUsers, 300000);
        return () => clearInterval(interval);
    }, []);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError(null);

            // Get users from multi-user auth system
            const response = await fetch('/zerodha-multi/users-status');

            if (response.ok) {
                const data = await response.json();
                console.log('Users data received:', data);
                setUsers(data.users || []);
            } else {
                // Fallback: Create master user entry
                setUsers([{
                    user_id: 'QSW899',
                    display_name: 'Master Trader (QSW899)',
                    authenticated: false,
                    status: 'inactive'
                }]);
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            // Fallback: Create master user entry when complete failure
            setUsers([{
                user_id: 'QSW899',
                display_name: 'Master Trader (QSW899)',
                authenticated: false,
                status: 'inactive'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleTokenSubmission = async (user) => {
        if (!tokenInput.trim()) {
            setError('Please enter your daily request token');
            return;
        }

        setSubmitting(true);
        setError(null);
        setSuccess(null);

        try {
            const response = await fetch('/api/zerodha-daily-auth/submit-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_token: tokenInput,
                    user_id: user.user_id
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setSuccess(`✅ Token submitted successfully for ${user.display_name}`);
                setTokenInput('');
                await fetchUsers(); // Refresh user status
                if (onAuthComplete) {
                    onAuthComplete();
                }
            } else {
                setError(data.error || 'Failed to submit token');
            }
        } catch (error) {
            console.error('Token submission error:', error);
            setError('Network error: Unable to submit token');
        } finally {
            setSubmitting(false);
        }
    };

    const getStatusColor = (user) => {
        if (user.authenticated) return 'success';
        return 'warning';
    };

    const getStatusIcon = (user) => {
        if (user.authenticated) return <CheckCircle />;
        return <Warning />;
    };

    const getStatusText = (user) => {
        if (user.authenticated) return 'Authenticated';
        return 'Not Authenticated';
    };

    const getZerodhaLoginUrl = () => {
        const apiKey = 'vc9ft4zpknynpm3u'; // Your production API key
        return `https://kite.trade/connect/login?api_key=${apiKey}&v=3`;
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Loading authentication status...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Security sx={{ mr: 1, fontSize: 32 }} />
                Daily Token Submission
            </Typography>

            <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
                Submit your daily Zerodha request token to enable trading. Tokens expire daily at 6:00 AM IST.
            </Typography>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                    {success}
                </Alert>
            )}

            {/* Daily Token Submission Section */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Step 1: Get Your Request Token
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                        Click the button below to login to Zerodha Kite and get your daily request token:
                    </Typography>
                    <Button
                        variant="contained"
                        color="primary"
                        href={getZerodhaLoginUrl()}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ mb: 2 }}
                    >
                        Login to Zerodha Kite
                    </Button>

                    <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        Step 2: Submit Your Token
                    </Typography>
                    <TextField
                        fullWidth
                        label="Request Token"
                        value={tokenInput}
                        onChange={(e) => setTokenInput(e.target.value)}
                        placeholder="Enter the request token from Zerodha"
                        sx={{ mb: 2 }}
                        disabled={submitting}
                    />
                </CardContent>
            </Card>

            {/* User Status Cards */}
            {users.map((user) => (
                <Card key={user.user_id} sx={{ mb: 2 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Typography variant="h6" sx={{ mr: 2 }}>
                                    {user.display_name}
                                </Typography>
                                <Chip
                                    icon={getStatusIcon(user)}
                                    label={getStatusText(user)}
                                    color={getStatusColor(user)}
                                    size="small"
                                />
                            </Box>

                            <Button
                                variant="contained"
                                color="primary"
                                onClick={() => handleTokenSubmission(user)}
                                disabled={submitting || !tokenInput.trim()}
                                startIcon={submitting ? <CircularProgress size={16} /> : <Refresh />}
                            >
                                {submitting ? 'Submitting...' : 'Submit Token'}
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            ))}

            {/* Instructions */}
            <Card sx={{ mt: 3, bgcolor: 'background.paper' }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        How Daily Token Submission Works:
                    </Typography>
                    <Typography variant="body2" component="div">
                        • Get your daily request token from Zerodha Kite (link above)
                        <br />
                        • Paste the token in the field and click "Submit Token"
                        <br />
                        • Token enables trading through the master account (QSW899)
                        <br />
                        • Tokens expire daily at 6:00 AM IST and need to be refreshed
                        <br />
                        • All trades execute through master account for regulatory compliance
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
};

export default MultiUserAuthDashboard; 