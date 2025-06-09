import {
    CheckCircle,
    Error,
    Refresh,
    ShowChart,
    TrendingDown,
    TrendingUp,
    Warning
} from '@mui/icons-material';
import {
    Alert,
    alpha,
    Box,
    Card,
    CardContent,
    Chip,
    Container,
    Divider,
    Grid,
    IconButton,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
    Paper,
    Tab,
    Tabs,
    Typography,
    useTheme
} from '@mui/material';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import {
    ResponsiveContainer,
    Tooltip,
    Treemap
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EnhancedDashboard = () => {
    const theme = useTheme();
    const [tabValue, setTabValue] = useState(0);
    const [marketIndices, setMarketIndices] = useState({});
    const [systemHealth, setSystemHealth] = useState({});
    const [tradingMetrics, setTradingMetrics] = useState({});
    const [topMovers, setTopMovers] = useState({ gainers: [], losers: [] });
    const [sectorData, setSectorData] = useState([]);
    const [marketActivity, setMarketActivity] = useState([]);
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [wsConnected, setWsConnected] = useState(false);
    const [apiError, setApiError] = useState(null);

    // Fetch data functions
    const fetchMarketIndices = async () => {
        try {
            console.log('Fetching market indices from:', `${API_BASE_URL}/market/indices`);
            const response = await axios.get(`${API_BASE_URL}/market/indices`);
            setMarketIndices(response.data.data || {});
            setApiError(null); // Clear error on success
        } catch (error) {
            console.error('Error fetching market indices:', error.response?.data || error.message);
            if (error.response?.status === 404) {
                console.error('Market indices endpoint not found. Check if the API routes are correctly configured.');
            }
            setApiError(`API Connection Error: ${error.message}`);
        }
    };

    const fetchSystemHealth = async () => {
        try {
            console.log('Fetching system health from:', `${API_BASE_URL}/api/health/detailed`);
            const response = await axios.get(`${API_BASE_URL}/api/health/detailed`);
            setSystemHealth(response.data.data || {});
        } catch (error) {
            console.error('Error fetching system health:', error.response?.data || error.message);
            if (error.response?.status === 404) {
                console.error('System health endpoint not found. Check if the API routes are correctly configured.');
            }
        }
    };

    const fetchTradingMetrics = async () => {
        try {
            console.log('Fetching trading metrics from:', `${API_BASE_URL}/api/trading/metrics`);
            const response = await axios.get(`${API_BASE_URL}/api/trading/metrics`);
            setTradingMetrics(response.data.data || {});
        } catch (error) {
            console.error('Error fetching trading metrics:', error.response?.data || error.message);
        }
    };

    const fetchTopMovers = async () => {
        try {
            console.log('Fetching top movers from:', `${API_BASE_URL}/market/movers`);
            const response = await axios.get(`${API_BASE_URL}/market/movers`);
            setTopMovers(response.data.data || { gainers: [], losers: [] });
        } catch (error) {
            console.error('Error fetching top movers:', error.response?.data || error.message);
        }
    };

    const fetchSectorData = async () => {
        try {
            console.log('Fetching sector data from:', `${API_BASE_URL}/market/sectors`);
            const response = await axios.get(`${API_BASE_URL}/market/sectors`);
            setSectorData(response.data.data || []);
        } catch (error) {
            console.error('Error fetching sector data:', error.response?.data || error.message);
        }
    };

    const fetchMarketActivity = async () => {
        try {
            console.log('Fetching market activity from:', `${API_BASE_URL}/market/activity`);
            const response = await axios.get(`${API_BASE_URL}/market/activity`);
            setMarketActivity(response.data.data || []);
        } catch (error) {
            console.error('Error fetching market activity:', error.response?.data || error.message);
        }
    };

    const fetchNotifications = async () => {
        try {
            console.log('Fetching notifications from:', `${API_BASE_URL}/api/notifications`);
            const response = await axios.get(`${API_BASE_URL}/api/notifications`);
            setNotifications(response.data.data || []);
        } catch (error) {
            console.error('Error fetching notifications:', error.response?.data || error.message);
        }
    };

    // Initial data fetch
    useEffect(() => {
        const fetchAllData = async () => {
            setLoading(true);
            await Promise.all([
                fetchMarketIndices(),
                fetchSystemHealth(),
                fetchTradingMetrics(),
                fetchTopMovers(),
                fetchSectorData(),
                fetchMarketActivity(),
                fetchNotifications()
            ]);
            setLoading(false);
        };

        fetchAllData();

        // Set up polling for real-time updates
        const interval = setInterval(() => {
            fetchMarketIndices();
            fetchSystemHealth();
            fetchMarketActivity();
        }, 5000); // Update every 5 seconds

        return () => clearInterval(interval);
    }, []);

    // WebSocket connection
    useEffect(() => {
        // Extract hostname from API_BASE_URL for WebSocket
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const apiUrl = new URL(API_BASE_URL);
        // Use a default user_id for dashboard connection (you can replace with actual user_id if available)
        const userId = 'dashboard'; // or get from auth context/props
        const wsUrl = `${wsProtocol}//${apiUrl.host}/ws/${userId}`;

        console.log('Attempting WebSocket connection to:', wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected successfully');
            setWsConnected(true);
            // Subscribe to market data updates
            ws.send(JSON.stringify({
                type: 'subscribe',
                room: 'market_data'
            }));
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data);
                // Handle real-time updates
                if (data.type === 'market_data') {
                    setMarketIndices(prev => ({ ...prev, [data.symbol]: data.data }));
                } else if (data.type === 'system_alert') {
                    // Handle system alerts
                    setNotifications(prev => [...prev, data.data]);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            setWsConnected(false);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setWsConnected(false);
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, []);

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    const getHealthColor = (status) => {
        switch (status) {
            case 'healthy': return theme.palette.success.main;
            case 'degraded': return theme.palette.warning.main;
            case 'unhealthy': return theme.palette.error.main;
            default: return theme.palette.grey[500];
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    };

    const formatPercent = (value) => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    // Render Market Indices
    const renderMarketIndices = () => (
        <Box>
            <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
                Live Market Indices
            </Typography>
            <Grid container spacing={3}>
                {Object.entries(marketIndices).map(([symbol, data]) => (
                    <Grid item xs={12} sm={6} md={3} key={symbol}>
                        <Card
                            sx={{
                                height: '100%',
                                background: 'rgba(255, 255, 255, 0.05)',
                                backdropFilter: 'blur(10px)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                transition: 'all 0.3s ease',
                                '&:hover': {
                                    transform: 'translateY(-4px)',
                                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                                }
                            }}
                        >
                            <CardContent>
                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                        {symbol}
                                    </Typography>
                                    <ShowChart sx={{ color: alpha(theme.palette.primary.main, 0.7) }} />
                                </Box>
                                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                                    {data.value?.toLocaleString() || '0'}
                                </Typography>
                                <Box display="flex" alignItems="center" gap={1}>
                                    {data.change >= 0 ? (
                                        <TrendingUp sx={{ color: theme.palette.success.main }} />
                                    ) : (
                                        <TrendingDown sx={{ color: theme.palette.error.main }} />
                                    )}
                                    <Typography
                                        variant="body1"
                                        sx={{
                                            color: data.change >= 0 ? theme.palette.success.main : theme.palette.error.main,
                                            fontWeight: 600
                                        }}
                                    >
                                        {formatPercent(data.changePercent || 0)}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        ({data.change >= 0 ? '+' : ''}{data.change?.toFixed(2) || '0'})
                                    </Typography>
                                </Box>
                                <Divider sx={{ my: 1.5 }} />
                                <Grid container spacing={1}>
                                    <Grid item xs={6}>
                                        <Typography variant="caption" color="text.secondary">High</Typography>
                                        <Typography variant="body2" fontWeight={500}>{data.high?.toLocaleString() || '0'}</Typography>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="caption" color="text.secondary">Low</Typography>
                                        <Typography variant="body2" fontWeight={500}>{data.low?.toLocaleString() || '0'}</Typography>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* Top Movers */}
            <Grid container spacing={3} sx={{ mt: 3 }}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                        <Typography variant="h6" gutterBottom sx={{ color: theme.palette.success.main }}>
                            Top Gainers
                        </Typography>
                        <List>
                            {topMovers.gainers.slice(0, 5).map((stock, index) => (
                                <ListItem key={index} divider>
                                    <ListItemText
                                        primary={stock.symbol}
                                        secondary={stock.name}
                                    />
                                    <Box textAlign="right">
                                        <Typography variant="body2" fontWeight={600}>
                                            ₹{stock.price?.toFixed(2) || '0'}
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: theme.palette.success.main }}>
                                            {formatPercent(stock.changePercent || 0)}
                                        </Typography>
                                    </Box>
                                </ListItem>
                            ))}
                        </List>
                    </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                        <Typography variant="h6" gutterBottom sx={{ color: theme.palette.error.main }}>
                            Top Losers
                        </Typography>
                        <List>
                            {topMovers.losers.slice(0, 5).map((stock, index) => (
                                <ListItem key={index} divider>
                                    <ListItemText
                                        primary={stock.symbol}
                                        secondary={stock.name}
                                    />
                                    <Box textAlign="right">
                                        <Typography variant="body2" fontWeight={600}>
                                            ₹{stock.price?.toFixed(2) || '0'}
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: theme.palette.error.main }}>
                                            {formatPercent(stock.changePercent || 0)}
                                        </Typography>
                                    </Box>
                                </ListItem>
                            ))}
                        </List>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );

    // Render System Health
    const renderSystemHealth = () => (
        <Box>
            <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
                System Health Monitor
            </Typography>
            <Grid container spacing={3}>
                {Object.entries(systemHealth).map(([service, data]) => (
                    <Grid item xs={12} md={6} lg={4} key={service}>
                        <Card sx={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            backdropFilter: 'blur(10px)',
                            border: `1px solid ${getHealthColor(data.status)}`
                        }}>
                            <CardContent>
                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                                    <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                                        {service.replace('_', ' ')}
                                    </Typography>
                                    {data.status === 'healthy' ? (
                                        <CheckCircle sx={{ color: theme.palette.success.main }} />
                                    ) : data.status === 'degraded' ? (
                                        <Warning sx={{ color: theme.palette.warning.main }} />
                                    ) : (
                                        <Error sx={{ color: theme.palette.error.main }} />
                                    )}
                                </Box>
                                <Chip
                                    label={data.status?.toUpperCase() || 'UNKNOWN'}
                                    size="small"
                                    sx={{
                                        backgroundColor: alpha(getHealthColor(data.status), 0.1),
                                        color: getHealthColor(data.status),
                                        fontWeight: 600,
                                        mb: 2
                                    }}
                                />
                                {Object.entries(data).filter(([key]) => key !== 'status').map(([key, value]) => (
                                    <Box key={key} display="flex" justifyContent="space-between" mb={1}>
                                        <Typography variant="body2" color="text.secondary">
                                            {key.replace(/_/g, ' ')}:
                                        </Typography>
                                        <Typography variant="body2" fontWeight={500}>
                                            {value}
                                        </Typography>
                                    </Box>
                                ))}
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );

    // Render Trading Analytics
    const renderTradingAnalytics = () => (
        <Box>
            <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
                Trading Performance Analytics
            </Typography>
            <Grid container spacing={3}>
                {/* Key Metrics */}
                <Grid item xs={12} md={3}>
                    <Card sx={{ background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                        <CardContent>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Total P&L
                            </Typography>
                            <Typography variant="h4" sx={{
                                color: tradingMetrics.totalPnL >= 0 ? theme.palette.success.main : theme.palette.error.main,
                                fontWeight: 700
                            }}>
                                {formatCurrency(tradingMetrics.totalPnL || 0)}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                    <Card sx={{ background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                        <CardContent>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Win Rate
                            </Typography>
                            <Typography variant="h4" sx={{ fontWeight: 700 }}>
                                {tradingMetrics.winRate?.toFixed(1) || '0'}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                    <Card sx={{ background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                        <CardContent>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Sharpe Ratio
                            </Typography>
                            <Typography variant="h4" sx={{ fontWeight: 700 }}>
                                {tradingMetrics.sharpeRatio?.toFixed(2) || '0'}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                    <Card sx={{ background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                        <CardContent>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                Max Drawdown
                            </Typography>
                            <Typography variant="h4" sx={{
                                color: theme.palette.error.main,
                                fontWeight: 700
                            }}>
                                -{tradingMetrics.maxDrawdown?.toFixed(1) || '0'}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );

    // Render Market Heatmap
    const renderMarketHeatmap = () => (
        <Box>
            <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
                Sector Performance Heatmap
            </Typography>
            <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)' }}>
                <ResponsiveContainer width="100%" height={400}>
                    <Treemap
                        data={sectorData}
                        dataKey="size"
                        aspectRatio={4 / 3}
                        stroke="#fff"
                        fill="#8884d8"
                    >
                        <Tooltip
                            content={({ active, payload }) => {
                                if (active && payload && payload[0]) {
                                    const data = payload[0].payload;
                                    return (
                                        <Paper sx={{ p: 1 }}>
                                            <Typography variant="body2">{data.name}</Typography>
                                            <Typography variant="body2" sx={{
                                                color: data.value >= 0 ? theme.palette.success.main : theme.palette.error.main
                                            }}>
                                                {formatPercent(data.value)}
                                            </Typography>
                                        </Paper>
                                    );
                                }
                                return null;
                            }}
                        />
                    </Treemap>
                </ResponsiveContainer>
            </Paper>
        </Box>
    );

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
                <LinearProgress sx={{ width: '50%' }} />
            </Box>
        );
    }

    return (
        <Container maxWidth="xl" sx={{ py: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    Enhanced Trading Dashboard
                </Typography>
                <Box display="flex" gap={2} alignItems="center">
                    <Chip
                        icon={wsConnected ? <CheckCircle /> : <Error />}
                        label={wsConnected ? 'Connected' : 'Disconnected'}
                        color={wsConnected ? 'success' : 'error'}
                        variant="outlined"
                    />
                    <IconButton onClick={() => window.location.reload()}>
                        <Refresh />
                    </IconButton>
                </Box>
            </Box>

            {/* API Connection Info */}
            <Box mb={2}>
                <Typography variant="caption" color="text.secondary">
                    API URL: {API_BASE_URL}
                </Typography>
            </Box>

            {/* Error Display */}
            {apiError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {apiError}
                </Alert>
            )}

            <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 4 }}>
                <Tab label="Market Overview" />
                <Tab label="System Health" />
                <Tab label="Trading Analytics" />
                <Tab label="Market Heatmap" />
            </Tabs>

            <Box>
                {tabValue === 0 && renderMarketIndices()}
                {tabValue === 1 && renderSystemHealth()}
                {tabValue === 2 && renderTradingAnalytics()}
                {tabValue === 3 && renderMarketHeatmap()}
            </Box>
        </Container>
    );
};

export default EnhancedDashboard;
