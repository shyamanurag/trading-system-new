import {
    AccountCircle,
    Delete,
    PersonAdd,
    Visibility
} from '@mui/icons-material';
import { fetchWithAuth } from '../api/fetchWithAuth';
import {
    Alert,
    Avatar,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    Grid,
    IconButton,
    InputLabel,
    MenuItem,
    Paper,
    Select,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tabs,
    TextField,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { API_ENDPOINTS } from '../api/config';
import fetchWithAuth from '../api/fetchWithAuth';
// UNIFIED: Import standardized user utilities
import {
    buildAPIUrl,
    createStandardUser,
    getContextualUserId,
    isMasterUser,
    standardizeUserData
} from '../utils/userUtils';

const UserManagementDashboard = ({ tradingData }) => {
    const [selectedTab, setSelectedTab] = useState(0);
    const [users, setUsers] = useState([]);
    const [userPositions, setUserPositions] = useState({});
    const [userTrades, setUserTrades] = useState({});
    const [userAnalytics, setUserAnalytics] = useState({});
    const [loading, setLoading] = useState(true);
    const [openDialog, setOpenDialog] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [newUserData, setNewUserData] = useState({
        username: '',
        email: '',
        password: '',
        zerodhaClientId: '',
        zerodhaPassword: '',
        initialCapital: 50000,
        riskLevel: 'medium'
    });
    const [error, setError] = useState(null);
    const [addUserLoading, setAddUserLoading] = useState(false);

    useEffect(() => {
        fetchAllData();
    }, []);

    const fetchAllData = async () => {
        try {
            setLoading(true);

            // UNIFIED: Use standardized user creation
            let realTradingData = tradingData;

            if (!realTradingData) {
                try {
                    const autonomousResponse = await fetchWithAuth('/api/v1/autonomous/status');
                    if (autonomousResponse.ok) {
                        const autonomousResult = await autonomousResponse.json();
                        if (autonomousResult.success) {
                            realTradingData = { systemMetrics: autonomousResult.data };
                        }
                    }
                } catch (autoError) {
                    console.warn('Autonomous endpoint not available:', autoError);
                }
            }

            // UNIFIED: Create master user with standardized structure
            let masterUsers = [];

            if (realTradingData?.systemMetrics?.totalTrades > 0) {
                const trading = realTradingData.systemMetrics;
                console.log('🎯 Creating Master User with REAL data:', trading);

                // UNIFIED: Use createStandardUser with real trading data
                const masterUser = createStandardUser({
                    total_trades: trading.totalTrades || 0,
                    total_pnl: trading.totalPnL || 0,
                    current_balance: trading.currentBalance || 1000000,
                    win_rate: trading.winRate || 0,
                    open_trades: trading.activeTrades || 0
                });

                masterUsers.push(masterUser);

                // UNIFIED: Use consistent user ID for positions/trades
                const masterUserId = getContextualUserId('database');

                // Fetch real positions using unified API building
                try {
                    const positionsUrl = buildAPIUrl(API_ENDPOINTS.POSITIONS.url, 'database');
                    const positionsResponse = await fetchWithAuth(positionsUrl);
                    if (positionsResponse.ok) {
                        const positionsData = await positionsResponse.json();
                        const realPositions = positionsData.positions || [];
                        setUserPositions({ [masterUserId]: realPositions });
                    } else {
                        setUserPositions({ [masterUserId]: [] });
                    }
                } catch (posError) {
                    console.warn('Positions fetch failed:', posError);
                    setUserPositions({ [masterUserId]: [] });
                }

                // Fetch real trades using unified API building
                try {
                    const tradesUrl = buildAPIUrl(API_ENDPOINTS.TRADES.url, 'database', { limit: 10 });
                    const tradesResponse = await fetchWithAuth(tradesUrl);
                    if (tradesResponse.ok) {
                        const tradesData = await tradesResponse.json();
                        const realTrades = tradesData.trades || [];
                        setUserTrades({ [masterUserId]: realTrades });
                    } else {
                        setUserTrades({ [masterUserId]: [] });
                    }
                } catch (tradeError) {
                    console.warn('Trades fetch failed:', tradeError);
                    setUserTrades({ [masterUserId]: [] });
                }

                // UNIFIED: Use standardized analytics structure
                setUserAnalytics({
                    [masterUserId]: {
                        dailyPnL: trading.dailyPnL || 0,
                        monthlyPnL: trading.monthlyPnL || 0,
                        totalReturn: trading.totalReturn || 0,
                        sharpeRatio: trading.sharpeRatio || 0,
                        maxDrawdown: trading.maxDrawdown || 0,
                        winRate: trading.winRate || 0,
                        avgWin: trading.avgWin || 0,
                        avgLoss: trading.avgLoss || 0
                    }
                });
            } else {
                // UNIFIED: Create default master user with standard structure
                const defaultMaster = createStandardUser();
                masterUsers.push(defaultMaster);
            }

            // Try to fetch additional users from API
            try {
                await fetchUsers();
                // UNIFIED: Combine master user with API users, avoiding duplicates
                setUsers(prevUsers => {
                    const apiUsers = prevUsers.filter(u => !isMasterUser(u.id));
                    const standardizedApiUsers = apiUsers.map(u => standardizeUserData(u, 'api'));
                    return [...masterUsers, ...standardizedApiUsers];
                });
            } catch (apiError) {
                console.warn('API users not available, using master user only');
                setUsers(masterUsers);
            }

        } catch (error) {
            console.error('Error fetching data:', error);
            setError('Unable to fetch user data. Showing master user only.');
            // UNIFIED: Always show standardized master user as fallback
            const fallbackUser = createStandardUser();
            setUsers([fallbackUser]);
        } finally {
            setLoading(false);
        }
    };

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const response = await fetchWithAuth(API_ENDPOINTS.BROKER_USERS.url);
            if (!response.ok) {
                throw new Error('Failed to fetch users');
            }
            const data = await response.json();
            if (data.success) {
                // UNIFIED: Transform broker users using standardizeUserData
                const transformedUsers = (data.users || []).map(user =>
                    standardizeUserData(user, 'broker')
                );
                setUsers(transformedUsers);
            } else {
                throw new Error(data.message || 'Failed to fetch users');
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            setError('Failed to fetch users: ' + error.message);
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    const fetchUserPositions = async (userId) => {
        try {
            // UNIFIED: Use buildAPIUrl for consistent parameter handling
            const url = buildAPIUrl(API_ENDPOINTS.POSITIONS.url, 'database', { user_id: userId });
            const response = await fetchWithAuth(url);
            if (response.ok) {
                const data = await response.json();
                setUserPositions(prev => ({
                    ...prev,
                    [userId]: data.positions || []
                }));
            }
        } catch (error) {
            console.error('Error fetching user positions:', error);
        }
    };

    const fetchUserTrades = async (userId) => {
        try {
            // UNIFIED: Use buildAPIUrl for consistent parameter handling
            const url = buildAPIUrl(API_ENDPOINTS.TRADES.url, 'database', { user_id: userId, limit: 10 });
            const response = await fetchWithAuth(url);
            if (response.ok) {
                const data = await response.json();
                setUserTrades(prev => ({
                    ...prev,
                    [userId]: data.trades || []
                }));
            }
        } catch (error) {
            console.error('Error fetching user trades:', error);
        }
    };

    const fetchUserAnalytics = async (userId) => {
        try {
            // UNIFIED: Use buildAPIUrl for consistent parameter handling
            const url = buildAPIUrl(API_ENDPOINTS.USER_PERFORMANCE.url, 'database', { user_id: userId });
            const response = await fetchWithAuth(url);
            if (response.ok) {
                const data = await response.json();
                setUserAnalytics(prev => ({
                    ...prev,
                    [userId]: data.analytics || {}
                }));
            }
        } catch (error) {
            console.error('Error fetching user analytics:', error);
        }
    };

    const handleAddUser = async () => {
        setAddUserLoading(true);
        try {
            // UNIFIED: Use standardized user data structure
            const userData = {
                user_id: newUserData.username,
                name: newUserData.username,
                email: newUserData.email,
                broker: 'zerodha',
                api_key: '',
                api_secret: '',
                client_id: newUserData.zerodhaClientId,
                initial_capital: newUserData.initialCapital,
                risk_tolerance: newUserData.riskLevel,
                paper_trading: false
            };

            const response = await fetchWithAuth(API_ENDPOINTS.BROKER_USERS.url, {
                method: 'POST',
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // UNIFIED: Standardize new user data
                    const standardizedUser = standardizeUserData(userData, 'new');
                    setUsers(prev => [...prev, standardizedUser]);
                    setOpenDialog(false);
                    setNewUserData({
                        username: '',
                        email: '',
                        password: '',
                        zerodhaClientId: '',
                        zerodhaPassword: '',
                        initialCapital: 50000,
                        riskLevel: 'medium'
                    });
                } else {
                    setError(result.message || 'Failed to add user');
                }
            } else {
                throw new Error('Failed to add user');
            }
        } catch (error) {
            console.error('Error adding user:', error);
            setError('Failed to add user: ' + error.message);
        } finally {
            setAddUserLoading(false);
        }
    };

    const handleDeleteUser = async (userId) => {
        // UNIFIED: Don't allow deletion of master user
        if (isMasterUser(userId)) {
            setError('Cannot delete the master user account');
            return;
        }

        try {
            const response = await fetchWithAuth(`${API_ENDPOINTS.BROKER_USERS.url}/${userId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setUsers(prev => prev.filter(user => user.id !== userId));
                setUserPositions(prev => {
                    const updated = { ...prev };
                    delete updated[userId];
                    return updated;
                });
                setUserTrades(prev => {
                    const updated = { ...prev };
                    delete updated[userId];
                    return updated;
                });
                setUserAnalytics(prev => {
                    const updated = { ...prev };
                    delete updated[userId];
                    return updated;
                });
            } else {
                throw new Error('Failed to delete user');
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            setError('Failed to delete user: ' + error.message);
        }
    };

    const handleUserSelect = (user) => {
        setSelectedUser(user);
        // UNIFIED: Use user.id consistently
        if (!userPositions[user.id]) {
            fetchUserPositions(user.id);
        }
        if (!userTrades[user.id]) {
            fetchUserTrades(user.id);
        }
        if (!userAnalytics[user.id]) {
            fetchUserAnalytics(user.id);
        }
    };

    // UNIFIED: Rest of the component remains largely the same but uses standardized user objects
    // The user objects now have consistent structure thanks to standardizeUserData

    return (
        <Box sx={{ width: '100%', p: 3 }}>
            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" gutterBottom>
                    User Management Dashboard
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<PersonAdd />}
                    onClick={() => setOpenDialog(true)}
                    sx={{ bgcolor: '#1976d2' }}
                >
                    Add User
                </Button>
            </Box>

            {/* Tab Navigation - UNIFIED: Uses standardized user data */}
            <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)} sx={{ mb: 3 }}>
                <Tab label="User Overview" />
                <Tab label="User Positions" />
                <Tab label="Performance Analytics" />
                <Tab label="User Management" />
            </Tabs>

            {/* User Overview Tab */}
            {selectedTab === 0 && (
                <Grid container spacing={3}>
                    {users.map((user) => (
                        <Grid item xs={12} md={6} lg={4} key={user.id}>
                            <Card
                                sx={{
                                    cursor: 'pointer',
                                    transition: 'transform 0.2s',
                                    '&:hover': { transform: 'translateY(-4px)' },
                                    // UNIFIED: Highlight master user with consistent identification
                                    border: isMasterUser(user.id) ? '2px solid #1976d2' : '1px solid #e0e0e0'
                                }}
                                onClick={() => handleUserSelect(user)}
                            >
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                        <Avatar sx={{ bgcolor: '#1976d2', mr: 2 }}>
                                            <AccountCircle />
                                        </Avatar>
                                        <Box>
                                            {/* UNIFIED: Use standardized display name */}
                                            <Typography variant="h6">{user.display_name}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {user.email}
                                            </Typography>
                                        </Box>
                                    </Box>

                                    {/* UNIFIED: Status chip with consistent logic */}
                                    <Chip
                                        label={isMasterUser(user.id) ? 'Master Account' : user.status}
                                        color={user.is_active ? 'success' : 'default'}
                                        size="small"
                                        sx={{ mb: 2 }}
                                    />

                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2">Capital:</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            ₹{user.capital?.toLocaleString() || '0'}
                                        </Typography>
                                    </Box>

                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2">Total P&L:</Typography>
                                        <Typography
                                            variant="body2"
                                            fontWeight="bold"
                                            color={user.total_pnl >= 0 ? 'success.main' : 'error.main'}
                                        >
                                            ₹{user.total_pnl?.toLocaleString() || '0'}
                                        </Typography>
                                    </Box>

                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <Typography variant="body2">Total Trades:</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {user.total_trades || 0}
                                        </Typography>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            )}

            {/* Rest of the tabs continue with similar standardization... */}
            {/* User Positions Tab */}
            {selectedTab === 1 && selectedUser && (
                <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                        {/* UNIFIED: Use standardized display name */}
                        {selectedUser.display_name} - Current Positions
                    </Typography>

                    {userPositions[selectedUser.id] && userPositions[selectedUser.id].length > 0 ? (
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Symbol</TableCell>
                                        <TableCell>Quantity</TableCell>
                                        <TableCell>Avg Price</TableCell>
                                        <TableCell>Current Price</TableCell>
                                        <TableCell>P&L</TableCell>
                                        <TableCell>Status</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {userPositions[selectedUser.id].map((position, index) => (
                                        <TableRow key={index}>
                                            <TableCell>{position.symbol}</TableCell>
                                            <TableCell>{position.quantity}</TableCell>
                                            <TableCell>₹{position.avg_price}</TableCell>
                                            <TableCell>₹{position.current_price}</TableCell>
                                            <TableCell
                                                style={{
                                                    color: position.pnl >= 0 ? '#4caf50' : '#f44336'
                                                }}
                                            >
                                                ₹{position.pnl}
                                            </TableCell>
                                            <TableCell>{position.status}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    ) : (
                        <Typography variant="body1" color="text.secondary">
                            No positions found for this user.
                        </Typography>
                    )}
                </Paper>
            )}

            {/* Performance Analytics Tab */}
            {selectedTab === 2 && selectedUser && (
                <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                        {/* UNIFIED: Use standardized display name */}
                        {selectedUser.display_name} - Performance Analytics
                    </Typography>

                    {userAnalytics[selectedUser.id] ? (
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={6}>
                                <Card sx={{ p: 2 }}>
                                    <Typography variant="h6" gutterBottom>
                                        Trading Statistics
                                    </Typography>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography>Win Rate:</Typography>
                                        <Typography fontWeight="bold">
                                            {userAnalytics[selectedUser.id].winRate || 0}%
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography>Sharpe Ratio:</Typography>
                                        <Typography fontWeight="bold">
                                            {userAnalytics[selectedUser.id].sharpeRatio || 0}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <Typography>Max Drawdown:</Typography>
                                        <Typography fontWeight="bold" color="error.main">
                                            {userAnalytics[selectedUser.id].maxDrawdown || 0}%
                                        </Typography>
                                    </Box>
                                </Card>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <Card sx={{ p: 2 }}>
                                    <Typography variant="h6" gutterBottom>
                                        P&L Breakdown
                                    </Typography>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography>Daily P&L:</Typography>
                                        <Typography
                                            fontWeight="bold"
                                            color={userAnalytics[selectedUser.id].dailyPnL >= 0 ? 'success.main' : 'error.main'}
                                        >
                                            ₹{userAnalytics[selectedUser.id].dailyPnL || 0}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography>Monthly P&L:</Typography>
                                        <Typography
                                            fontWeight="bold"
                                            color={userAnalytics[selectedUser.id].monthlyPnL >= 0 ? 'success.main' : 'error.main'}
                                        >
                                            ₹{userAnalytics[selectedUser.id].monthlyPnL || 0}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <Typography>Total Return:</Typography>
                                        <Typography
                                            fontWeight="bold"
                                            color={userAnalytics[selectedUser.id].totalReturn >= 0 ? 'success.main' : 'error.main'}
                                        >
                                            {userAnalytics[selectedUser.id].totalReturn || 0}%
                                        </Typography>
                                    </Box>
                                </Card>
                            </Grid>
                        </Grid>
                    ) : (
                        <Typography variant="body1" color="text.secondary">
                            No analytics data available for this user.
                        </Typography>
                    )}
                </Paper>
            )}

            {/* User Management Tab */}
            {selectedTab === 3 && (
                <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                        User Management
                    </Typography>

                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Username</TableCell>
                                    <TableCell>Email</TableCell>
                                    <TableCell>Capital</TableCell>
                                    <TableCell>Total Trades</TableCell>
                                    <TableCell>Win Rate</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {users.map((user) => (
                                    <TableRow key={user.id}>
                                        {/* UNIFIED: Use standardized user properties */}
                                        <TableCell>{user.username}</TableCell>
                                        <TableCell>{user.email}</TableCell>
                                        <TableCell>₹{user.capital?.toLocaleString()}</TableCell>
                                        <TableCell>{user.total_trades}</TableCell>
                                        <TableCell>{user.win_rate}%</TableCell>
                                        <TableCell>
                                            <Chip
                                                label={user.status}
                                                color={user.is_active ? 'success' : 'default'}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <IconButton
                                                onClick={() => handleUserSelect(user)}
                                                size="small"
                                            >
                                                <Visibility />
                                            </IconButton>
                                            {/* UNIFIED: Don't allow deletion of master user */}
                                            {!isMasterUser(user.id) && (
                                                <IconButton
                                                    onClick={() => handleDeleteUser(user.id)}
                                                    size="small"
                                                    color="error"
                                                >
                                                    <Delete />
                                                </IconButton>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Paper>
            )}

            {/* Add User Dialog - UNIFIED: Uses consistent field names */}
            <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Add New User</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Username"
                        type="text"
                        fullWidth
                        variant="outlined"
                        value={newUserData.username}
                        onChange={(e) => setNewUserData(prev => ({ ...prev, username: e.target.value }))}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        label="Email"
                        type="email"
                        fullWidth
                        variant="outlined"
                        value={newUserData.email}
                        onChange={(e) => setNewUserData(prev => ({ ...prev, email: e.target.value }))}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        label="Password"
                        type="password"
                        fullWidth
                        variant="outlined"
                        value={newUserData.password}
                        onChange={(e) => setNewUserData(prev => ({ ...prev, password: e.target.value }))}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        label="Zerodha Client ID"
                        type="text"
                        fullWidth
                        variant="outlined"
                        value={newUserData.zerodhaClientId}
                        onChange={(e) => setNewUserData(prev => ({ ...prev, zerodhaClientId: e.target.value }))}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        margin="dense"
                        label="Initial Capital"
                        type="number"
                        fullWidth
                        variant="outlined"
                        value={newUserData.initialCapital}
                        onChange={(e) => setNewUserData(prev => ({ ...prev, initialCapital: parseFloat(e.target.value) }))}
                        sx={{ mb: 2 }}
                    />
                    <FormControl fullWidth variant="outlined">
                        <InputLabel>Risk Level</InputLabel>
                        <Select
                            value={newUserData.riskLevel}
                            onChange={(e) => setNewUserData(prev => ({ ...prev, riskLevel: e.target.value }))}
                            label="Risk Level"
                        >
                            <MenuItem value="low">Low</MenuItem>
                            <MenuItem value="medium">Medium</MenuItem>
                            <MenuItem value="high">High</MenuItem>
                        </Select>
                    </FormControl>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
                    <Button
                        onClick={handleAddUser}
                        variant="contained"
                        disabled={addUserLoading}
                    >
                        {addUserLoading ? 'Adding...' : 'Add User'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* User Details Dialog */}
            {selectedUser && (
                <Dialog
                    open={!!selectedUser}
                    onClose={() => setSelectedUser(null)}
                    maxWidth="md"
                    fullWidth
                >
                    {/* UNIFIED: Use standardized display name */}
                    <DialogTitle>{selectedUser.display_name} - Detailed Information</DialogTitle>
                    <DialogContent>
                        <Grid container spacing={2}>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">User ID:</Typography>
                                <Typography variant="body2">{selectedUser.id}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Email:</Typography>
                                <Typography variant="body2">{selectedUser.email}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Zerodha Client ID:</Typography>
                                <Typography variant="body2">{selectedUser.zerodha_client_id}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Current Balance:</Typography>
                                <Typography variant="body2">₹{selectedUser.current_balance?.toLocaleString()}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Total Trades:</Typography>
                                <Typography variant="body2">{selectedUser.total_trades}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Win Rate:</Typography>
                                <Typography variant="body2">{selectedUser.win_rate}%</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Risk Tolerance:</Typography>
                                <Typography variant="body2">{selectedUser.risk_tolerance}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="subtitle2">Join Date:</Typography>
                                <Typography variant="body2">
                                    {new Date(selectedUser.joinDate).toLocaleDateString()}
                                </Typography>
                            </Grid>
                        </Grid>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setSelectedUser(null)}>Close</Button>
                    </DialogActions>
                </Dialog>
            )}
        </Box>
    );
};

export default UserManagementDashboard; 