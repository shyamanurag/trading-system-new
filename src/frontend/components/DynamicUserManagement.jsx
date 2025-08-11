import {
    Assessment,
    Delete,
    Edit,
    PersonAdd,
    RefreshRounded,
    Settings,
    ShowChart,
    TrendingUp,
    Visibility
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
    FormControl,
    Grid,
    IconButton,
    InputLabel,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    Tab,
    Tabs,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { API_ENDPOINTS } from '../api/config';
import fetchWithAuth from '../api/fetchWithAuth';

const DynamicUserManagement = () => {
    // State management
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState(0);
    const [openDialog, setOpenDialog] = useState(false);
    const [dialogType, setDialogType] = useState('create'); // 'create', 'edit', 'view'
    const [userForm, setUserForm] = useState({
        username: '',
        email: '',
        password: '',
        full_name: '',
        initial_capital: 50000,
        risk_tolerance: 'medium',
        zerodha_client_id: '',
        zerodha_api_key: '',
        zerodha_api_secret: ''
    });
    const [userAnalytics, setUserAnalytics] = useState({});
    const [userReports, setUserReports] = useState({});
    const [refreshing, setRefreshing] = useState(false);

    // Load users on component mount
    useEffect(() => {
        loadUsers();
    }, []);

    // Load user analytics when users change
    useEffect(() => {
        if (users.length > 0) {
            loadUsersAnalytics();
        }
    }, [users]);

    const loadUsers = async () => {
        try {
            setLoading(true);
            // Fetch broker users directly; no fallbacks
            const response = await fetchWithAuth(API_ENDPOINTS.BROKER_USERS.url);
            if (!response.ok) {
                throw new Error('Broker users endpoint failed');
            }
            const data = await response.json();
            const rawUsers = Array.isArray(data?.users) ? data.users : [];
            const transformedUsers = rawUsers.map(user => ({
                id: user.user_id || user.id,
                username: user.username || user.name || user.user_id,
                email: user.email || '',
                zerodha_client_id: user.zerodha_client_id || '',
                initial_capital: user.initial_capital || 0,
                current_balance: user.current_balance || 0,
                total_trades: user.total_trades || 0,
                total_pnl: user.total_pnl || 0,
                win_rate: user.win_rate || 0,
                status: user.status || 'active',
                created_at: user.created_at || null,
                is_active: (user.status || 'active') === 'active'
            }));
            setUsers(transformedUsers);
            setError(null);
        } catch (err) {
            setError(err.message);
            console.error('Error loading users:', err);
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    const loadUsersAnalytics = async () => {
        try {
            const analytics = {};
            const reports = {};

            for (const user of users.slice(0, 10)) { // Limit to first 10 users for performance
                try {
                    // Load performance metrics from correct endpoint
                    const perfResponse = await fetchWithAuth(`/api/v1/users/performance?user_id=${user.id}&days=30`);
                    if (perfResponse.ok) {
                        const text = await perfResponse.text();
                        try {
                            const perfData = JSON.parse(text);
                            analytics[user.id] = perfData;
                        } catch (jsonErr) {
                            console.error('Non-JSON response for performance:', text);
                        }
                    }

                    // Load dashboard data - assuming correct endpoint
                    const dashResponse = await fetchWithAuth(`/api/v1/users/dashboard?user_id=${user.id}`);
                    if (dashResponse.ok) {
                        const text = await dashResponse.text();
                        try {
                            const dashData = JSON.parse(text);
                            reports[user.id] = dashData;
                        } catch (jsonErr) {
                            console.error('Non-JSON response for dashboard:', text);
                        }
                    }
                } catch (err) {
                    console.warn(`Error loading analytics for user ${user.id}:`, err);
                }
            }

            setUserAnalytics(analytics);
            setUserReports(reports);
        } catch (err) {
            console.error('Error loading user analytics:', err);
        }
    };

    const createUser = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/v1/users/dynamic/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userForm)
            });

            const data = await response.json();

            if (response.ok) {
                await loadUsers();
                setOpenDialog(false);
                resetForm();
                setError(null);
            } else {
                throw new Error(data.detail || 'Failed to create user');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const updateUser = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/api/v1/users/dynamic/${selectedUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    full_name: userForm.full_name,
                    initial_capital: userForm.initial_capital,
                    current_balance: userForm.current_balance,
                    risk_tolerance: userForm.risk_tolerance,
                    zerodha_client_id: userForm.zerodha_client_id,
                    is_active: userForm.is_active
                })
            });

            const data = await response.json();

            if (response.ok) {
                await loadUsers();
                setOpenDialog(false);
                resetForm();
                setError(null);
            } else {
                throw new Error(data.detail || 'Failed to update user');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const deleteUser = async (userId) => {
        if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            return;
        }

        try {
            setLoading(true);
            const response = await fetch(`/api/v1/users/dynamic/${userId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await loadUsers();
                setError(null);
            } else {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to delete user');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const openCreateDialog = () => {
        setDialogType('create');
        resetForm();
        setOpenDialog(true);
    };

    const openEditDialog = (user) => {
        setDialogType('edit');
        setSelectedUser(user);
        setUserForm({
            username: user.username,
            email: user.email,
            password: '',
            full_name: user.full_name,
            initial_capital: user.initial_capital,
            current_balance: user.current_balance,
            risk_tolerance: user.risk_tolerance,
            zerodha_client_id: user.zerodha_client_id || '',
            is_active: user.is_active
        });
        setOpenDialog(true);
    };

    const openViewDialog = (user) => {
        setDialogType('view');
        setSelectedUser(user);
        setOpenDialog(true);
    };

    const resetForm = () => {
        setUserForm({
            username: '',
            email: '',
            password: '',
            full_name: '',
            initial_capital: 50000,
            risk_tolerance: 'medium',
            zerodha_client_id: '',
            zerodha_api_key: '',
            zerodha_api_secret: ''
        });
        setSelectedUser(null);
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        await loadUsers();
        await loadUsersAnalytics();
        setRefreshing(false);
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    };

    const formatPercentage = (value) => {
        return `${value.toFixed(1)}%`;
    };

    const getStatusColor = (user) => {
        if (!user.is_active) return 'error';
        if (user.total_pnl > 0) return 'success';
        if (user.total_pnl < 0) return 'warning';
        return 'info';
    };

    const getStatusText = (user) => {
        if (!user.is_active) return 'Inactive';
        if (user.total_trades === 0) return 'No Trades';
        return 'Active';
    };

    // Tab panels
    const TabPanel = ({ children, value, index }) => (
        <div hidden={value !== index}>
            {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
        </div>
    );

    // User overview card component
    const UserCard = ({ user }) => {
        const analytics = userAnalytics[user.id];
        const report = userReports[user.id];

        return (
            <Card sx={{ mb: 2, position: 'relative' }}>
                <CardContent>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} sm={3}>
                            <Box display="flex" alignItems="center" gap={1}>
                                <Avatar sx={{ bgcolor: getStatusColor(user) === 'success' ? 'green' : 'grey' }}>
                                    {user.username.charAt(0).toUpperCase()}
                                </Avatar>
                                <Box>
                                    <Typography variant="h6">{user.full_name}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        @{user.username}
                                    </Typography>
                                    <Chip
                                        label={getStatusText(user)}
                                        color={getStatusColor(user)}
                                        size="small"
                                    />
                                </Box>
                            </Box>
                        </Grid>

                        <Grid item xs={12} sm={2}>
                            <Typography variant="body2" color="text.secondary">Balance</Typography>
                            <Typography variant="h6">
                                {formatCurrency(user.current_balance)}
                            </Typography>
                        </Grid>

                        <Grid item xs={12} sm={2}>
                            <Typography variant="body2" color="text.secondary">Total P&L</Typography>
                            <Typography
                                variant="h6"
                                color={user.total_pnl >= 0 ? 'success.main' : 'error.main'}
                            >
                                {formatCurrency(user.total_pnl)}
                            </Typography>
                        </Grid>

                        <Grid item xs={12} sm={2}>
                            <Typography variant="body2" color="text.secondary">Win Rate</Typography>
                            <Typography variant="h6">
                                {formatPercentage(user.win_rate)}
                            </Typography>
                        </Grid>

                        <Grid item xs={12} sm={1}>
                            <Typography variant="body2" color="text.secondary">Trades</Typography>
                            <Typography variant="h6">{user.total_trades}</Typography>
                        </Grid>

                        <Grid item xs={12} sm={2}>
                            <Box display="flex" gap={1}>
                                <Tooltip title="View Details">
                                    <IconButton
                                        size="small"
                                        onClick={() => openViewDialog(user)}
                                        color="primary"
                                    >
                                        <Visibility />
                                    </IconButton>
                                </Tooltip>
                                <Tooltip title="Edit User">
                                    <IconButton
                                        size="small"
                                        onClick={() => openEditDialog(user)}
                                        color="primary"
                                    >
                                        <Edit />
                                    </IconButton>
                                </Tooltip>
                                <Tooltip title="Delete User">
                                    <IconButton
                                        size="small"
                                        onClick={() => deleteUser(user.id)}
                                        color="error"
                                    >
                                        <Delete />
                                    </IconButton>
                                </Tooltip>
                            </Box>
                        </Grid>
                    </Grid>

                    {/* Performance indicators */}
                    {analytics && analytics.performance_30d && (
                        <Box mt={2}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                30-Day Performance
                            </Typography>
                            <LinearProgress
                                variant="determinate"
                                value={Math.min(Math.abs(analytics.performance_30d.win_rate), 100)}
                                color={analytics.performance_30d.win_rate > 50 ? 'success' : 'warning'}
                                sx={{ height: 6, borderRadius: 3 }}
                            />
                        </Box>
                    )}
                </CardContent>
            </Card>
        );
    };

    // Analytics overview component
    const AnalyticsOverview = () => {
        const totalUsers = users.length;
        const activeUsers = users.filter(u => u.is_active).length;
        const totalBalance = users.reduce((sum, u) => sum + u.current_balance, 0);
        const totalPnL = users.reduce((sum, u) => sum + u.total_pnl, 0);
        const totalTrades = users.reduce((sum, u) => sum + u.total_trades, 0);
        const avgWinRate = users.length > 0 ? users.reduce((sum, u) => sum + u.win_rate, 0) / users.length : 0;

        return (
            <Grid container spacing={3} mb={3}>
                <Grid item xs={12} sm={6} md={2}>
                    <Card>
                        <CardContent>
                            <Typography variant="h4" color="primary">{totalUsers}</Typography>
                            <Typography variant="body2">Total Users</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                    <Card>
                        <CardContent>
                            <Typography variant="h4" color="success.main">{activeUsers}</Typography>
                            <Typography variant="body2">Active Users</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" color="info.main">
                                {formatCurrency(totalBalance)}
                            </Typography>
                            <Typography variant="body2">Total Balance</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                    <Card>
                        <CardContent>
                            <Typography
                                variant="h6"
                                color={totalPnL >= 0 ? 'success.main' : 'error.main'}
                            >
                                {formatCurrency(totalPnL)}
                            </Typography>
                            <Typography variant="body2">Total P&L</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                    <Card>
                        <CardContent>
                            <Typography variant="h4" color="warning.main">{totalTrades}</Typography>
                            <Typography variant="body2">Total Trades</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" color="secondary.main">
                                {formatPercentage(avgWinRate)}
                            </Typography>
                            <Typography variant="body2">Avg Win Rate</Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        );
    };

    // User form dialog component
    const UserFormDialog = () => (
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
            <DialogTitle>
                {dialogType === 'create' && 'Create New User'}
                {dialogType === 'edit' && 'Edit User'}
                {dialogType === 'view' && 'User Details'}
            </DialogTitle>
            <DialogContent>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                    {dialogType !== 'view' && (
                        <>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth
                                    label="Username"
                                    value={userForm.username}
                                    onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                                    disabled={dialogType === 'edit'}
                                    required
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth
                                    label="Email"
                                    type="email"
                                    value={userForm.email}
                                    onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                                    disabled={dialogType === 'edit'}
                                    required
                                />
                            </Grid>
                            {dialogType === 'create' && (
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        label="Password"
                                        type="password"
                                        value={userForm.password}
                                        onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                                        required
                                    />
                                </Grid>
                            )}
                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Full Name"
                                    value={userForm.full_name}
                                    onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                                    required
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth
                                    label="Initial Capital"
                                    type="number"
                                    value={userForm.initial_capital}
                                    onChange={(e) => setUserForm({ ...userForm, initial_capital: parseFloat(e.target.value) })}
                                    required
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Risk Tolerance</InputLabel>
                                    <Select
                                        value={userForm.risk_tolerance}
                                        onChange={(e) => setUserForm({ ...userForm, risk_tolerance: e.target.value })}
                                        label="Risk Tolerance"
                                    >
                                        <MenuItem value="low">Low</MenuItem>
                                        <MenuItem value="medium">Medium</MenuItem>
                                        <MenuItem value="high">High</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Zerodha Client ID"
                                    value={userForm.zerodha_client_id}
                                    onChange={(e) => setUserForm({ ...userForm, zerodha_client_id: e.target.value })}
                                />
                            </Grid>
                            {dialogType === 'create' && (
                                <>
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Zerodha API Key"
                                            value={userForm.zerodha_api_key}
                                            onChange={(e) => setUserForm({ ...userForm, zerodha_api_key: e.target.value })}
                                        />
                                    </Grid>
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Zerodha API Secret"
                                            type="password"
                                            value={userForm.zerodha_api_secret}
                                            onChange={(e) => setUserForm({ ...userForm, zerodha_api_secret: e.target.value })}
                                        />
                                    </Grid>
                                </>
                            )}
                        </>
                    )}

                    {dialogType === 'view' && selectedUser && (
                        <Grid container spacing={2}>
                            <Grid item xs={12}>
                                <Typography variant="h6" gutterBottom>User Information</Typography>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <Typography variant="body2" color="text.secondary">Username</Typography>
                                <Typography variant="body1">{selectedUser.username}</Typography>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <Typography variant="body2" color="text.secondary">Email</Typography>
                                <Typography variant="body1">{selectedUser.email}</Typography>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <Typography variant="body2" color="text.secondary">Full Name</Typography>
                                <Typography variant="body1">{selectedUser.full_name}</Typography>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <Typography variant="body2" color="text.secondary">Risk Tolerance</Typography>
                                <Typography variant="body1">{selectedUser.risk_tolerance}</Typography>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <Typography variant="body2" color="text.secondary">Current Balance</Typography>
                                <Typography variant="body1">{formatCurrency(selectedUser.current_balance)}</Typography>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <Typography variant="body2" color="text.secondary">Total P&L</Typography>
                                <Typography
                                    variant="body1"
                                    color={selectedUser.total_pnl >= 0 ? 'success.main' : 'error.main'}
                                >
                                    {formatCurrency(selectedUser.total_pnl)}
                                </Typography>
                            </Grid>

                            {userAnalytics[selectedUser.id] && (
                                <>
                                    <Grid item xs={12}>
                                        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                                            Performance Analytics
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                        <Typography variant="body2" color="text.secondary">Win Rate</Typography>
                                        <Typography variant="body1">
                                            {formatPercentage(selectedUser.win_rate)}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                        <Typography variant="body2" color="text.secondary">Total Trades</Typography>
                                        <Typography variant="body1">{selectedUser.total_trades}</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={4}>
                                        <Typography variant="body2" color="text.secondary">Active Positions</Typography>
                                        <Typography variant="body1">{selectedUser.active_positions}</Typography>
                                    </Grid>
                                </>
                            )}
                        </Grid>
                    )}
                </Grid>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
                {dialogType === 'create' && (
                    <Button onClick={createUser} variant="contained" disabled={loading}>
                        Create User
                    </Button>
                )}
                {dialogType === 'edit' && (
                    <Button onClick={updateUser} variant="contained" disabled={loading}>
                        Update User
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );

    return (
        <Box>
            {/* Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" gutterBottom>
                    Dynamic User Management
                </Typography>
                <Box display="flex" gap={1}>
                    <Button
                        variant="outlined"
                        startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshRounded />}
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        Refresh
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<PersonAdd />}
                        onClick={openCreateDialog}
                    >
                        Add User
                    </Button>
                </Box>
            </Box>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Loading */}
            {loading && (
                <Box display="flex" justifyContent="center" p={3}>
                    <CircularProgress />
                </Box>
            )}

            {/* Analytics Overview */}
            {!loading && users.length > 0 && <AnalyticsOverview />}

            {/* Navigation Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs
                    value={activeTab}
                    onChange={(e, newValue) => setActiveTab(newValue)}
                    variant="scrollable"
                    scrollButtons="auto"
                >
                    <Tab icon={<Assessment />} label="User Overview" />
                    <Tab icon={<ShowChart />} label="Performance Analytics" />
                    <Tab icon={<TrendingUp />} label="Leaderboard" />
                    <Tab icon={<Settings />} label="Management Tools" />
                </Tabs>
            </Paper>

            {/* Tab Content */}
            <TabPanel value={activeTab} index={0}>
                {!loading && users.length === 0 && (
                    <Box textAlign="center" py={4}>
                        <Typography variant="h6" color="text.secondary">
                            No users found
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Create your first user to get started
                        </Typography>
                        <Button variant="contained" startIcon={<PersonAdd />} onClick={openCreateDialog}>
                            Add First User
                        </Button>
                    </Box>
                )}

                {users.map((user) => (
                    <UserCard key={user.id} user={user} />
                ))}
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
                <Typography variant="h6" gutterBottom>
                    Performance Analytics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Detailed analytics coming soon...
                </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
                <Typography variant="h6" gutterBottom>
                    User Leaderboard
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Leaderboard functionality coming soon...
                </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
                <Typography variant="h6" gutterBottom>
                    Management Tools
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Bulk operations and advanced management tools coming soon...
                </Typography>
            </TabPanel>

            {/* User Form Dialog */}
            <UserFormDialog />
        </Box>
    );
};

export default DynamicUserManagement; 