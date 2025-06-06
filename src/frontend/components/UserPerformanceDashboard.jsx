import {
    Analytics,
    Assessment,
    Delete,
    PersonAdd
} from '@mui/icons-material';
import {
    Alert,
    Avatar,
    Badge,
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
    FormControlLabel,
    Grid,
    IconButton,
    List,
    ListItem,
    ListItemText,
    Switch,
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
import {
    Area,
    AreaChart,
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const UserPerformanceDashboard = () => {
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [userPerformance, setUserPerformance] = useState({});
    const [dailyPnL, setDailyPnL] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [tabValue, setTabValue] = useState(0);
    const [openUserDialog, setOpenUserDialog] = useState(false);
    const [newUser, setNewUser] = useState({
        user_id: '',
        initial_capital: 100000,
        risk_tolerance: 'medium',
        trading_preferences: {
            max_position_size: 5,
            preferred_strategies: ['breakout', 'momentum'],
            auto_trade: false
        }
    });

    useEffect(() => {
        fetchUsers();
        fetchDailyPnL();
    }, []);

    useEffect(() => {
        if (selectedUser) {
            fetchUserPerformance(selectedUser.user_id);
        }
    }, [selectedUser]);

    const fetchUsers = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/users`);
            const data = await response.json();

            if (data.success) {
                setUsers(data.users || generateMockUsers());
            } else {
                setUsers(generateMockUsers());
            }

            // Set first user as selected by default
            if (data.users && data.users.length > 0) {
                setSelectedUser(data.users[0]);
            } else {
                const mockUsers = generateMockUsers();
                setUsers(mockUsers);
                setSelectedUser(mockUsers[0]);
            }
        } catch (err) {
            console.error('Error fetching users:', err);
            const mockUsers = generateMockUsers();
            setUsers(mockUsers);
            setSelectedUser(mockUsers[0]);
            setError('Using demo data - API not available');
        }
    };

    const fetchUserPerformance = async (userId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/users/${userId}/performance`);
            const data = await response.json();

            if (data.success) {
                setUserPerformance(data.performance || generateMockUserPerformance(userId));
            } else {
                setUserPerformance(generateMockUserPerformance(userId));
            }
        } catch (err) {
            console.error('Error fetching user performance:', err);
            setUserPerformance(generateMockUserPerformance(userId));
        }
    };

    const fetchDailyPnL = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/performance/daily-pnl`);
            const data = await response.json();

            if (data.success) {
                setDailyPnL(data.daily_pnl || generateMockDailyPnL());
            } else {
                setDailyPnL(generateMockDailyPnL());
            }
        } catch (err) {
            console.error('Error fetching daily P&L:', err);
            setDailyPnL(generateMockDailyPnL());
        } finally {
            setLoading(false);
        }
    };

    const generateMockUsers = () => {
        return [
            {
                user_id: 'trader_001',
                name: 'Rajesh Kumar',
                email: 'rajesh@example.com',
                initial_capital: 500000,
                current_capital: 587500,
                is_active: true,
                registration_date: '2024-01-15',
                risk_tolerance: 'medium',
                total_trades: 45,
                winning_trades: 32,
                win_rate: 71.1,
                total_pnl: 87500,
                daily_pnl: 2500,
                open_trades: 3,
                avatar: 'RK'
            },
            {
                user_id: 'trader_002',
                name: 'Priya Sharma',
                email: 'priya@example.com',
                initial_capital: 300000,
                current_capital: 345600,
                is_active: true,
                registration_date: '2024-02-01',
                risk_tolerance: 'conservative',
                total_trades: 28,
                winning_trades: 22,
                win_rate: 78.6,
                total_pnl: 45600,
                daily_pnl: 1200,
                open_trades: 2,
                avatar: 'PS'
            },
            {
                user_id: 'trader_003',
                name: 'Amit Patel',
                email: 'amit@example.com',
                initial_capital: 1000000,
                current_capital: 925000,
                is_active: false,
                registration_date: '2024-01-01',
                risk_tolerance: 'aggressive',
                total_trades: 67,
                winning_trades: 38,
                win_rate: 56.7,
                total_pnl: -75000,
                daily_pnl: -3500,
                open_trades: 0,
                avatar: 'AP'
            }
        ];
    };

    const generateMockUserPerformance = (userId) => {
        const last30Days = Array.from({ length: 30 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - 29 + i);
            return {
                date: date.toISOString().split('T')[0],
                pnl: (Math.random() - 0.4) * 5000,
                cumulative_pnl: (i + 1) * 1000 + (Math.random() - 0.3) * 10000,
                trades_count: Math.floor(Math.random() * 4),
                win_rate: 60 + Math.random() * 30
            };
        });

        const trades = [
            { symbol: 'RELIANCE', entry_date: '2024-06-01', exit_date: '2024-06-05', pnl: 15000, status: 'CLOSED' },
            { symbol: 'TCS', entry_date: '2024-06-03', exit_date: null, pnl: 2500, status: 'OPEN' },
            { symbol: 'HDFC', entry_date: '2024-06-04', exit_date: '2024-06-06', pnl: -3500, status: 'CLOSED' },
            { symbol: 'INFY', entry_date: '2024-06-05', exit_date: null, pnl: 1200, status: 'OPEN' }
        ];

        return {
            daily_performance: last30Days,
            recent_trades: trades,
            risk_metrics: {
                sharpe_ratio: 1.8,
                max_drawdown: 12.5,
                volatility: 18.2,
                var_95: 8500,
                correlation_to_market: 0.65
            },
            strategy_breakdown: [
                { strategy: 'Breakout', trades: 15, win_rate: 80, avg_return: 8.5 },
                { strategy: 'Momentum', trades: 12, win_rate: 75, avg_return: 6.2 },
                { strategy: 'Mean Reversion', trades: 8, win_rate: 62.5, avg_return: 4.1 }
            ]
        };
    };

    const generateMockDailyPnL = () => {
        return Array.from({ length: 30 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - 29 + i);
            return {
                date: date.toISOString().split('T')[0],
                total_pnl: (Math.random() - 0.3) * 50000,
                user_count: 15 + Math.floor(Math.random() * 10),
                trades_count: 20 + Math.floor(Math.random() * 30),
                winning_trades: Math.floor((20 + Math.random() * 30) * (0.6 + Math.random() * 0.3))
            };
        });
    };

    const handleCreateUser = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newUser)
            });

            if (response.ok) {
                setOpenUserDialog(false);
                fetchUsers();
                setNewUser({
                    user_id: '',
                    initial_capital: 100000,
                    risk_tolerance: 'medium',
                    trading_preferences: {
                        max_position_size: 5,
                        preferred_strategies: ['breakout', 'momentum'],
                        auto_trade: false
                    }
                });
            }
        } catch (err) {
            console.error('Error creating user:', err);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    fetchUsers();
                    if (selectedUser?.user_id === userId) {
                        setSelectedUser(null);
                    }
                }
            } catch (err) {
                console.error('Error deleting user:', err);
            }
        }
    };

    const formatCurrency = (value) => `₹${value.toLocaleString()}`;
    const formatPercent = (value) => `${value.toFixed(1)}%`;

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ ml: 2 }}>Loading User Performance...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Assessment />
                        User Performance Dashboard
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                        Comprehensive user analytics, daily P&L tracking, and portfolio management
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<PersonAdd />}
                    onClick={() => setOpenUserDialog(true)}
                >
                    Add New User
                </Button>
            </Box>

            {error && (
                <Alert severity="info" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                    <Tab label="Daily P&L Overview" />
                    <Tab label="User Management" />
                    <Tab label="Individual Performance" />
                    <Tab label="Analytics & Reports" />
                </Tabs>
            </Box>

            {/* Tab Panel 0: Daily P&L Overview */}
            {tabValue === 0 && (
                <Grid container spacing={3}>
                    {/* Summary Cards */}
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Today's P&L
                                </Typography>
                                <Typography variant="h4" color="success.main">
                                    ₹25,750
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    +12.3% from yesterday
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Active Users
                                </Typography>
                                <Typography variant="h4">
                                    23
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    2 new this week
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Total Trades
                                </Typography>
                                <Typography variant="h4">
                                    157
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Win Rate: 68.2%
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    AUM
                                </Typography>
                                <Typography variant="h4">
                                    ₹1.2Cr
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    +8.5% this month
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Daily P&L Chart */}
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Daily P&L Trend (Last 30 Days)
                                </Typography>
                                <ResponsiveContainer width="100%" height={300}>
                                    <AreaChart data={dailyPnL}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis />
                                        <Tooltip formatter={(value) => [formatCurrency(value), 'P&L']} />
                                        <Area
                                            type="monotone"
                                            dataKey="total_pnl"
                                            stroke="#2196f3"
                                            fill="#2196f3"
                                            fillOpacity={0.3}
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Tab Panel 1: User Management */}
            {tabValue === 1 && (
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    All Users
                                    <Badge badgeContent={users.length} color="primary" sx={{ ml: 2 }} />
                                </Typography>
                                <TableContainer>
                                    <Table>
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>User</TableCell>
                                                <TableCell align="right">Initial Capital</TableCell>
                                                <TableCell align="right">Current Capital</TableCell>
                                                <TableCell align="right">Total P&L</TableCell>
                                                <TableCell align="right">Daily P&L</TableCell>
                                                <TableCell align="right">Win Rate</TableCell>
                                                <TableCell align="center">Status</TableCell>
                                                <TableCell align="center">Actions</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {users.map((user) => (
                                                <TableRow key={user.user_id} hover>
                                                    <TableCell>
                                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                            <Avatar>{user.avatar}</Avatar>
                                                            <Box>
                                                                <Typography variant="body1">{user.name}</Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    {user.user_id}
                                                                </Typography>
                                                            </Box>
                                                        </Box>
                                                    </TableCell>
                                                    <TableCell align="right">{formatCurrency(user.initial_capital)}</TableCell>
                                                    <TableCell align="right">{formatCurrency(user.current_capital)}</TableCell>
                                                    <TableCell align="right">
                                                        <Typography color={user.total_pnl > 0 ? 'success.main' : 'error.main'}>
                                                            {formatCurrency(user.total_pnl)}
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell align="right">
                                                        <Typography color={user.daily_pnl > 0 ? 'success.main' : 'error.main'}>
                                                            {formatCurrency(user.daily_pnl)}
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell align="right">{formatPercent(user.win_rate)}</TableCell>
                                                    <TableCell align="center">
                                                        <Chip
                                                            label={user.is_active ? 'Active' : 'Inactive'}
                                                            color={user.is_active ? 'success' : 'default'}
                                                            size="small"
                                                        />
                                                    </TableCell>
                                                    <TableCell align="center">
                                                        <IconButton
                                                            onClick={() => setSelectedUser(user)}
                                                            color="primary"
                                                        >
                                                            <Analytics />
                                                        </IconButton>
                                                        <IconButton
                                                            onClick={() => handleDeleteUser(user.user_id)}
                                                            color="error"
                                                        >
                                                            <Delete />
                                                        </IconButton>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Tab Panel 2: Individual Performance */}
            {tabValue === 2 && selectedUser && userPerformance.daily_performance && (
                <Grid container spacing={3}>
                    {/* User Info Card */}
                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                    <Avatar sx={{ width: 60, height: 60 }}>{selectedUser.avatar}</Avatar>
                                    <Box>
                                        <Typography variant="h6">{selectedUser.name}</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {selectedUser.user_id}
                                        </Typography>
                                        <Chip
                                            label={selectedUser.is_active ? 'Active' : 'Inactive'}
                                            color={selectedUser.is_active ? 'success' : 'default'}
                                            size="small"
                                        />
                                    </Box>
                                </Box>
                                <Divider sx={{ my: 2 }} />
                                <List dense>
                                    <ListItem>
                                        <ListItemText
                                            primary="Total Trades"
                                            secondary={selectedUser.total_trades}
                                        />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText
                                            primary="Win Rate"
                                            secondary={formatPercent(selectedUser.win_rate)}
                                        />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText
                                            primary="Current Capital"
                                            secondary={formatCurrency(selectedUser.current_capital)}
                                        />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText
                                            primary="Open Trades"
                                            secondary={selectedUser.open_trades}
                                        />
                                    </ListItem>
                                </List>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Performance Chart */}
                    <Grid item xs={12} md={8}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Performance Trend (Last 30 Days)
                                </Typography>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={userPerformance.daily_performance}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis />
                                        <Tooltip />
                                        <Line type="monotone" dataKey="cumulative_pnl" stroke="#2196f3" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Recent Trades */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>Recent Trades</Typography>
                                <TableContainer>
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Symbol</TableCell>
                                                <TableCell>Entry</TableCell>
                                                <TableCell>Exit</TableCell>
                                                <TableCell align="right">P&L</TableCell>
                                                <TableCell>Status</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {userPerformance.recent_trades?.map((trade, idx) => (
                                                <TableRow key={idx}>
                                                    <TableCell>{trade.symbol}</TableCell>
                                                    <TableCell>{trade.entry_date}</TableCell>
                                                    <TableCell>{trade.exit_date || '-'}</TableCell>
                                                    <TableCell align="right">
                                                        <Typography color={trade.pnl > 0 ? 'success.main' : 'error.main'}>
                                                            {formatCurrency(trade.pnl)}
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={trade.status}
                                                            color={trade.status === 'OPEN' ? 'warning' : 'default'}
                                                            size="small"
                                                        />
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Risk Metrics */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>Risk Metrics</Typography>
                                <List>
                                    <ListItem>
                                        <ListItemText
                                            primary="Sharpe Ratio"
                                            secondary={userPerformance.risk_metrics?.sharpe_ratio.toFixed(2)}
                                        />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText
                                            primary="Max Drawdown"
                                            secondary={formatPercent(userPerformance.risk_metrics?.max_drawdown)}
                                        />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText
                                            primary="Volatility"
                                            secondary={formatPercent(userPerformance.risk_metrics?.volatility)}
                                        />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText
                                            primary="VaR (95%)"
                                            secondary={formatCurrency(userPerformance.risk_metrics?.var_95)}
                                        />
                                    </ListItem>
                                </List>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Tab Panel 3: Analytics & Reports */}
            {tabValue === 3 && (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>Strategy Performance</Typography>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={userPerformance.strategy_breakdown || []}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="strategy" />
                                        <YAxis />
                                        <Tooltip />
                                        <Bar dataKey="win_rate" fill="#2196f3" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>User Distribution</Typography>
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={[
                                                { name: 'Active', value: users.filter(u => u.is_active).length },
                                                { name: 'Inactive', value: users.filter(u => !u.is_active).length }
                                            ]}
                                            cx="50%"
                                            cy="50%"
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                            label
                                        >
                                            {[
                                                { name: 'Active', value: users.filter(u => u.is_active).length },
                                                { name: 'Inactive', value: users.filter(u => !u.is_active).length }
                                            ].map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Add User Dialog */}
            <Dialog open={openUserDialog} onClose={() => setOpenUserDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Add New User</DialogTitle>
                <DialogContent>
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={12}>
                            <TextField
                                label="User ID"
                                fullWidth
                                value={newUser.user_id}
                                onChange={(e) => setNewUser({ ...newUser, user_id: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                label="Initial Capital"
                                type="number"
                                fullWidth
                                value={newUser.initial_capital}
                                onChange={(e) => setNewUser({ ...newUser, initial_capital: Number(e.target.value) })}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                label="Risk Tolerance"
                                select
                                fullWidth
                                value={newUser.risk_tolerance}
                                onChange={(e) => setNewUser({ ...newUser, risk_tolerance: e.target.value })}
                                SelectProps={{ native: true }}
                            >
                                <option value="conservative">Conservative</option>
                                <option value="medium">Medium</option>
                                <option value="aggressive">Aggressive</option>
                            </TextField>
                        </Grid>
                        <Grid item xs={12}>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={newUser.trading_preferences.auto_trade}
                                        onChange={(e) => setNewUser({
                                            ...newUser,
                                            trading_preferences: {
                                                ...newUser.trading_preferences,
                                                auto_trade: e.target.checked
                                            }
                                        })}
                                    />
                                }
                                label="Enable Auto Trading"
                            />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenUserDialog(false)}>Cancel</Button>
                    <Button onClick={handleCreateUser} variant="contained">Create User</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UserPerformanceDashboard; 