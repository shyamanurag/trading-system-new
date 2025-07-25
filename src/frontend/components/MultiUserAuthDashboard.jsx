import {
    AccountCircle,
    CheckCircle,
    Error,
    PersonAdd,
    Refresh,
    Security,
    TrendingUp,
    Warning
} from '@mui/icons-material';
import {
    Alert,
    Avatar,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    Grid,
    TextField,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';

const MultiUserAuthDashboard = ({ onAuthComplete }) => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [authDialog, setAuthDialog] = useState({ open: false, user: null });
    const [addUserDialog, setAddUserDialog] = useState(false);
    const [tokenInput, setTokenInput] = useState('');
    const [newUserData, setNewUserData] = useState({
        user_id: '',
        display_name: '',
        email: '',
        daily_limit: 100000
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchUsers();
        // Auto-refresh every 5 minutes to check token status
        const interval = setInterval(fetchUsers, 300000);
        return () => clearInterval(interval);
    }, []);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError(null); // Clear previous errors

            // Get users from multi-user auth system
            const response = await fetch('/zerodha-multi/users-status');

            if (response.ok) {
                const data = await response.json();
                console.log('Users data received:', data);
                setUsers(data.users || []);
            } else {
                console.error('API response not OK:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error response body:', errorText);

                // Try health check to diagnose connectivity
                try {
                    const healthResponse = await fetch('/zerodha-multi/health');
                    if (healthResponse.ok) {
                        const healthData = await healthResponse.json();
                        console.log('Health check passed:', healthData);
                        setError(`API Error: ${response.status} ${response.statusText} (Service is healthy)`);
                    } else {
                        setError(`API Error: ${response.status} ${response.statusText} (Health check also failed)`);
                    }
                } catch (healthError) {
                    console.error('Health check failed:', healthError);
                    setError(`API Error: ${response.status} ${response.statusText} (Cannot reach service)`);
                }

                // Fallback: Create master user entry
                setUsers([{
                    user_id: 'QSW899',
                    display_name: 'Master Trader (QSW899)',
                    email: 'master@algoauto.com',
                    is_master: true,
                    authenticated: false,
                    token_expiry: null,
                    last_refresh: null,
                    daily_limit: 1000000,
                    status: 'inactive'
                }]);
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            setError(`Failed to load user authentication status: ${error.message || error}`);

            // Fallback: Create master user entry when complete failure
            setUsers([{
                user_id: 'QSW899',
                display_name: 'Master Trader (QSW899)',
                email: 'master@algoauto.com',
                is_master: true,
                authenticated: false,
                token_expiry: null,
                last_refresh: null,
                daily_limit: 1000000,
                status: 'inactive'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleAuthUser = async (user) => {
        if (!tokenInput.trim()) {
            setError('Please enter your daily request token');
            return;
        }

        setSubmitting(true);
        setError(null);

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
                // Update user status locally
                setUsers(prevUsers =>
                    prevUsers.map(u =>
                        u.user_id === user.user_id
                            ? { ...u, authenticated: true, last_refresh: new Date().toISOString(), status: 'active' }
                            : u
                    )
                );

                setAuthDialog({ open: false, user: null });
                setTokenInput('');

                if (onAuthComplete) {
                    onAuthComplete(user.user_id);
                }
            } else {
                setError(data.message || 'Authentication failed');
            }
        } catch (error) {
            setError('Network error during authentication');
        } finally {
            setSubmitting(false);
        }
    };

    const handleAddUser = async () => {
        if (!newUserData.user_id || !newUserData.display_name || !newUserData.email) {
            setError('Please fill in all required fields');
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const response = await fetch('/zerodha-multi/add-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newUserData)
            });

            if (response.ok) {
                await fetchUsers(); // Refresh user list
                setAddUserDialog(false);
                setNewUserData({
                    user_id: '',
                    display_name: '',
                    email: '',
                    daily_limit: 100000
                });
            } else {
                setError('Failed to add user');
            }
        } catch (error) {
            setError('Network error while adding user');
        } finally {
            setSubmitting(false);
        }
    };

    const getStatusColor = (user) => {
        if (user.authenticated) return 'success';
        if (user.token_expiry && new Date(user.token_expiry) < new Date()) return 'error';
        return 'warning';
    };

    const getStatusIcon = (user) => {
        if (user.authenticated) return <CheckCircle />;
        if (user.token_expiry && new Date(user.token_expiry) < new Date()) return <Error />;
        return <Warning />;
    };

    const getStatusText = (user) => {
        if (user.authenticated) return 'Authenticated';
        if (user.token_expiry && new Date(user.token_expiry) < new Date()) return 'Token Expired';
        return 'Not Authenticated';
    };

    const getZerodhaLoginUrl = (user) => {
        const apiKey = 'vc9ft4zpknynpm3u'; // Your production API key
        return `https://kite.trade/connect/login?api_key=${apiKey}&v=3`;
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Loading user authentication status...</Typography>
            </Box>
        );
    }

    return (
        <Box>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center' }}>
                    <Security sx={{ mr: 1 }} />
                    Multi-User Authentication Center
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={fetchUsers}
                        disabled={loading}
                    >
                        Refresh Status
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<PersonAdd />}
                        onClick={() => setAddUserDialog(true)}
                    >
                        Add User
                    </Button>
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* System Info */}
            <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                    <strong>How Multi-User Authentication Works:</strong><br />
                    • Each user authenticates with their own Zerodha credentials daily<br />
                    • All trades execute through the master account (QSW899) for regulatory compliance<br />
                    • Individual user permissions and limits are managed at the application level<br />
                    • Tokens expire daily at 6:00 AM IST and need to be refreshed
                </Typography>
            </Alert>

            {/* Users List */}
            <Grid container spacing={2}>
                {users.map((user, index) => (
                    <Grid item xs={12} md={6} lg={4} key={user.user_id}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <Avatar sx={{ mr: 2, bgcolor: user.is_master ? 'primary.main' : 'secondary.main' }}>
                                        {user.is_master ? <TrendingUp /> : <AccountCircle />}
                                    </Avatar>
                                    <Box sx={{ flexGrow: 1 }}>
                                        <Typography variant="h6" noWrap>
                                            {user.display_name}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" noWrap>
                                            ID: {user.user_id}
                                        </Typography>
                                    </Box>
                                    <Chip
                                        icon={getStatusIcon(user)}
                                        label={getStatusText(user)}
                                        color={getStatusColor(user)}
                                        size="small"
                                    />
                                </Box>

                                <Divider sx={{ mb: 2 }} />

                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="body2" color="text.secondary">
                                        <strong>Email:</strong> {user.email}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        <strong>Daily Limit:</strong> ₹{(user.daily_limit || 0).toLocaleString()}
                                    </Typography>
                                    {user.last_refresh && (
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>Last Auth:</strong> {new Date(user.last_refresh).toLocaleString()}
                                        </Typography>
                                    )}
                                    {user.token_expiry && (
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>Expires:</strong> {new Date(user.token_expiry).toLocaleString()}
                                        </Typography>
                                    )}
                                </Box>

                                <Box sx={{ display: 'flex', gap: 1 }}>
                                    <Button
                                        variant={user.authenticated ? 'outlined' : 'contained'}
                                        color={user.authenticated ? 'success' : 'primary'}
                                        fullWidth
                                        onClick={() => setAuthDialog({ open: true, user })}
                                        startIcon={user.authenticated ? <CheckCircle /> : <Security />}
                                    >
                                        {user.authenticated ? 'Refresh Token' : 'Authenticate'}
                                    </Button>
                                </Box>

                                {user.is_master && (
                                    <Alert severity="warning" sx={{ mt: 2 }}>
                                        <Typography variant="caption">
                                            Master Account - All trades execute through this account
                                        </Typography>
                                    </Alert>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* User Authentication Dialog */}
            <Dialog open={authDialog.open} onClose={() => setAuthDialog({ open: false, user: null })} maxWidth="md">
                <DialogTitle>
                    Authenticate User: {authDialog.user?.display_name}
                </DialogTitle>
                <DialogContent>
                    <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                            <strong>Step 1:</strong> Click the link below to login to Zerodha<br />
                            <strong>Step 2:</strong> Complete your 2FA authentication<br />
                            <strong>Step 3:</strong> Copy the request_token from the redirected URL<br />
                            <strong>Step 4:</strong> Paste the token below and submit
                        </Typography>
                    </Alert>

                    <Button
                        variant="outlined"
                        href={authDialog.user ? getZerodhaLoginUrl(authDialog.user) : '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ mb: 2, display: 'block' }}
                    >
                        🔗 Open Zerodha Login for {authDialog.user?.display_name}
                    </Button>

                    <TextField
                        autoFocus
                        margin="dense"
                        label="Daily Request Token"
                        type="text"
                        fullWidth
                        variant="outlined"
                        value={tokenInput}
                        onChange={(e) => setTokenInput(e.target.value)}
                        placeholder="Paste your request_token here..."
                        disabled={submitting}
                        helperText="Copy the request_token parameter from the URL after successful Zerodha login"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAuthDialog({ open: false, user: null })} disabled={submitting}>
                        Cancel
                    </Button>
                    <Button
                        onClick={() => handleAuthUser(authDialog.user)}
                        variant="contained"
                        disabled={submitting || !tokenInput.trim()}
                    >
                        {submitting ? <CircularProgress size={20} /> : 'Authenticate'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Add User Dialog */}
            <Dialog open={addUserDialog} onClose={() => setAddUserDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Add New User</DialogTitle>
                <DialogContent>
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={12}>
                            <TextField
                                label="Zerodha User ID"
                                fullWidth
                                value={newUserData.user_id}
                                onChange={(e) => setNewUserData({ ...newUserData, user_id: e.target.value })}
                                placeholder="e.g., AB1234"
                                required
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                label="Display Name"
                                fullWidth
                                value={newUserData.display_name}
                                onChange={(e) => setNewUserData({ ...newUserData, display_name: e.target.value })}
                                placeholder="e.g., John Trader"
                                required
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                label="Email"
                                type="email"
                                fullWidth
                                value={newUserData.email}
                                onChange={(e) => setNewUserData({ ...newUserData, email: e.target.value })}
                                placeholder="e.g., john@example.com"
                                required
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                label="Daily Trading Limit (₹)"
                                type="number"
                                fullWidth
                                value={newUserData.daily_limit}
                                onChange={(e) => setNewUserData({ ...newUserData, daily_limit: parseFloat(e.target.value) || 0 })}
                                required
                            />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAddUserDialog(false)} disabled={submitting}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleAddUser}
                        variant="contained"
                        disabled={submitting}
                    >
                        {submitting ? <CircularProgress size={20} /> : 'Add User'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default MultiUserAuthDashboard; 