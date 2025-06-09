import {
    Air,
    Analytics,
    Assessment,
    BubbleChart,
    CheckCircle,
    Error,
    MonetizationOn,
    Notifications,
    Refresh,
    Security,
    ShowChart,
    Speed,
    Timeline,
    TrendingDown,
    TrendingUp,
    Warning,
    WaterDrop,
    Wifi,
    WifiOff
} from '@mui/icons-material';
import {
    Alert,
    alpha,
    Avatar,
    Badge,
    Box,
    Button,
    ButtonGroup,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Container,
    Fade,
    Grid,
    IconButton,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Paper,
    Skeleton,
    Stack,
    Tab,
    Tabs,
    Typography,
    useTheme
} from '@mui/material';
import axios from 'axios';
import { AnimatePresence, motion } from 'framer-motion';
import React, { useEffect, useRef, useState } from 'react';
import {
    CartesianGrid,
    Line,
    LineChart,
    PolarAngleAxis,
    PolarGrid,
    PolarRadiusAxis,
    Radar,
    RadarChart,
    Tooltip as RechartsTooltip,
    ResponsiveContainer,
    Treemap,
    XAxis,
    YAxis
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Custom styled components
const GlowingCard = ({ children, glow = 'primary', ...props }) => {
    const theme = useTheme();
    return (
        <Card
            {...props}
            sx={{
                position: 'relative',
                overflow: 'visible',
                transition: 'all 0.3s ease',
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: `0 12px 24px ${alpha(theme.palette[glow].main, 0.3)}`,
                },
                '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    borderRadius: 1,
                    padding: '2px',
                    background: `linear-gradient(135deg, ${theme.palette[glow].main}, ${theme.palette[glow].dark})`,
                    mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                    maskComposite: 'exclude',
                    opacity: 0.1,
                    transition: 'opacity 0.3s ease',
                },
                '&:hover::before': {
                    opacity: 0.3,
                },
                ...props.sx
            }}
        >
            {children}
        </Card>
    );
};

const PulsingDot = ({ color = 'success' }) => {
    const theme = useTheme();
    return (
        <Box
            sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: theme.palette[color].main,
                position: 'relative',
                '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '100%',
                    height: '100%',
                    borderRadius: '50%',
                    backgroundColor: theme.palette[color].main,
                    animation: 'pulse 2s infinite',
                },
                '@keyframes pulse': {
                    '0%': {
                        transform: 'translate(-50%, -50%) scale(1)',
                        opacity: 1,
                    },
                    '100%': {
                        transform: 'translate(-50%, -50%) scale(2.5)',
                        opacity: 0,
                    },
                },
            }}
        />
    );
};

const AnimatedNumber = ({ value, prefix = '', suffix = '', decimals = 2 }) => {
    const [displayValue, setDisplayValue] = useState(0);

    useEffect(() => {
        const duration = 1000;
        const steps = 60;
        const stepValue = (value - displayValue) / steps;
        let currentStep = 0;

        const timer = setInterval(() => {
            currentStep++;
            if (currentStep <= steps) {
                setDisplayValue(prev => prev + stepValue);
            } else {
                setDisplayValue(value);
                clearInterval(timer);
            }
        }, duration / steps);

        return () => clearInterval(timer);
    }, [value]);

    return (
        <Typography variant="h4" component="span">
            {prefix}{displayValue.toFixed(decimals)}{suffix}
        </Typography>
    );
};

const EnhancedDashboard = () => {
    const theme = useTheme();
    const wsRef = useRef(null);
    const [activeTab, setActiveTab] = useState(0);
    const [timeRange, setTimeRange] = useState('1D');

    // State management
    const [marketIndices, setMarketIndices] = useState({
        NIFTY50: { value: 0, change: 0, changePercent: 0, volume: 0, high: 0, low: 0 },
        SENSEX: { value: 0, change: 0, changePercent: 0, volume: 0, high: 0, low: 0 },
        BANKNIFTY: { value: 0, change: 0, changePercent: 0, volume: 0, high: 0, low: 0 },
        FINNIFTY: { value: 0, change: 0, changePercent: 0, volume: 0, high: 0, low: 0 }
    });

    const [systemHealth, setSystemHealth] = useState({
        api: { status: 'checking', latency: 0 },
        database: { status: 'checking', connections: 0 },
        redis: { status: 'checking', memory: 0 },
        websocket: { status: 'disconnected', connections: 0 },
        truedata: { status: 'checking', symbols: 0 }
    });

    const [tradingMetrics, setTradingMetrics] = useState({
        totalPositions: 0,
        openPositions: 0,
        todayPnL: 0,
        totalPnL: 0,
        winRate: 0,
        avgReturn: 0,
        sharpeRatio: 0,
        maxDrawdown: 0
    });

    const [marketActivity, setMarketActivity] = useState([]);
    const [topMovers, setTopMovers] = useState({ gainers: [], losers: [] });
    const [sectorPerformance, setSectorPerformance] = useState([]);
    const [heatmapData, setHeatmapData] = useState([]);
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [wsConnected, setWsConnected] = useState(false);

    // WebSocket connection
    useEffect(() => {
        const connectWebSocket = () => {
            const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws';
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                console.log('WebSocket connected');
                setWsConnected(true);
                setSystemHealth(prev => ({
                    ...prev,
                    websocket: { status: 'connected', connections: 1 }
                }));

                // Subscribe to market data
                wsRef.current.send(JSON.stringify({
                    type: 'subscribe',
                    room: 'market_indices'
                }));
            };

            wsRef.current.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setWsConnected(false);
            };

            wsRef.current.onclose = () => {
                console.log('WebSocket disconnected');
                setWsConnected(false);
                setSystemHealth(prev => ({
                    ...prev,
                    websocket: { status: 'disconnected', connections: 0 }
                }));

                // Reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const handleWebSocketMessage = (data) => {
        switch (data.type) {
            case 'market_indices':
                setMarketIndices(data.data);
                break;
            case 'system_health':
                setSystemHealth(data.data);
                break;
            case 'trading_metrics':
                setTradingMetrics(data.data);
                break;
            case 'market_activity':
                setMarketActivity(prev => [...data.data, ...prev].slice(0, 50));
                break;
            case 'notification':
                setNotifications(prev => [data.data, ...prev].slice(0, 10));
                break;
            default:
                break;
        }
    };

    // Fetch initial data
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                setLoading(true);

                // Fetch system health
                const healthRes = await axios.get(`${API_BASE_URL}/api/health/detailed`);
                if (healthRes.data.success) {
                    setSystemHealth(healthRes.data.data);
                }

                // Fetch market indices
                const indicesRes = await axios.get(`${API_BASE_URL}/api/market/indices`);
                if (indicesRes.data.success) {
                    setMarketIndices(indicesRes.data.data);
                }

                // Fetch trading metrics
                const metricsRes = await axios.get(`${API_BASE_URL}/api/trading/metrics`);
                if (metricsRes.data.success) {
                    setTradingMetrics(metricsRes.data.data);
                }

                // Fetch top movers
                const moversRes = await axios.get(`${API_BASE_URL}/api/market/movers`);
                if (moversRes.data.success) {
                    setTopMovers(moversRes.data.data);
                }

                // Fetch sector performance
                const sectorRes = await axios.get(`${API_BASE_URL}/api/market/sectors`);
                if (sectorRes.data.success) {
                    setSectorPerformance(sectorRes.data.data);
                }

            } catch (error) {
                console.error('Error fetching initial data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchInitialData();
        const interval = setInterval(fetchInitialData, 60000); // Refresh every minute

        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy':
            case 'connected':
            case 'ok':
                return 'success';
            case 'warning':
            case 'degraded':
                return 'warning';
            case 'error':
            case 'disconnected':
            case 'down':
                return 'error';
            default:
                return 'default';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'healthy':
            case 'connected':
            case 'ok':
                return <CheckCircle />;
            case 'warning':
            case 'degraded':
                return <Warning />;
            case 'error':
            case 'disconnected':
            case 'down':
                return <Error />;
            default:
                return <CircularProgress size={16} />;
        }
    };

    if (loading) {
        return (
            <Container maxWidth="xl" sx={{ mt: 4 }}>
                <Grid container spacing={3}>
                    {[1, 2, 3, 4, 5, 6].map((item) => (
                        <Grid item xs={12} md={6} lg={4} key={item}>
                            <Skeleton variant="rectangular" height={200} />
                        </Grid>
                    ))}
                </Grid>
            </Container>
        );
    }

    return (
        <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
            {/* Header Section */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Paper
                    sx={{
                        p: 3,
                        mb: 3,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                        backdropFilter: 'blur(10px)',
                        border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                    }}
                >
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={6}>
                            <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
                                Trading Command Center
                            </Typography>
                            <Stack direction="row" spacing={2} alignItems="center">
                                <Chip
                                    icon={wsConnected ? <Wifi /> : <WifiOff />}
                                    label={wsConnected ? 'Live Data' : 'Reconnecting...'}
                                    color={wsConnected ? 'success' : 'error'}
                                    size="small"
                                />
                                <Typography variant="body2" color="text.secondary">
                                    Last updated: {new Date().toLocaleTimeString()}
                                </Typography>
                            </Stack>
                        </Grid>
                        <Grid item xs={12} md={6} textAlign="right">
                            <ButtonGroup variant="outlined" size="small">
                                {['1D', '1W', '1M', '3M', '1Y'].map((range) => (
                                    <Button
                                        key={range}
                                        onClick={() => setTimeRange(range)}
                                        variant={timeRange === range ? 'contained' : 'outlined'}
                                    >
                                        {range}
                                    </Button>
                                ))}
                            </ButtonGroup>
                            <IconButton sx={{ ml: 2 }} onClick={() => window.location.reload()}>
                                <Refresh />
                            </IconButton>
                        </Grid>
                    </Grid>
                </Paper>
            </motion.div>

            {/* Market Indices Section */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                {Object.entries(marketIndices).map(([index, data], idx) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.3, delay: idx * 0.1 }}
                        >
                            <GlowingCard glow={data.change >= 0 ? 'success' : 'error'}>
                                <CardContent>
                                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                                        <Typography variant="h6" color="text.secondary">
                                            {index}
                                        </Typography>
                                        <Avatar
                                            sx={{
                                                bgcolor: data.change >= 0 ? 'success.main' : 'error.main',
                                                width: 32,
                                                height: 32
                                            }}
                                        >
                                            {data.change >= 0 ? <TrendingUp /> : <TrendingDown />}
                                        </Avatar>
                                    </Stack>
                                    <AnimatedNumber value={data.value} decimals={2} />
                                    <Stack direction="row" spacing={1} alignItems="center" mt={1}>
                                        <Chip
                                            label={`${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}`}
                                            color={data.change >= 0 ? 'success' : 'error'}
                                            size="small"
                                        />
                                        <Typography
                                            variant="body2"
                                            color={data.change >= 0 ? 'success.main' : 'error.main'}
                                        >
                                            {data.changePercent.toFixed(2)}%
                                        </Typography>
                                    </Stack>
                                    <Box mt={2}>
                                        <LinearProgress
                                            variant="determinate"
                                            value={((data.value - data.low) / (data.high - data.low)) * 100}
                                            sx={{ height: 6, borderRadius: 3 }}
                                        />
                                        <Stack direction="row" justifyContent="space-between" mt={0.5}>
                                            <Typography variant="caption">L: {data.low}</Typography>
                                            <Typography variant="caption">H: {data.high}</Typography>
                                        </Stack>
                                    </Box>
                                </CardContent>
                            </GlowingCard>
                        </motion.div>
                    </Grid>
                ))}
            </Grid>

            {/* Main Content Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} variant="fullWidth">
                    <Tab label="System Health" icon={<Speed />} />
                    <Tab label="Trading Analytics" icon={<Analytics />} />
                    <Tab label="Market Heatmap" icon={<BubbleChart />} />
                    <Tab label="Risk Monitor" icon={<Security />} />
                </Tabs>
            </Paper>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
                {activeTab === 0 && (
                    <motion.div
                        key="health"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        <Grid container spacing={3}>
                            {/* System Health Cards */}
                            {Object.entries(systemHealth).map(([service, data]) => (
                                <Grid item xs={12} sm={6} md={4} lg={2.4} key={service}>
                                    <Card>
                                        <CardContent>
                                            <Stack direction="row" justifyContent="space-between" alignItems="center">
                                                <Typography variant="subtitle2" textTransform="capitalize">
                                                    {service}
                                                </Typography>
                                                {getStatusIcon(data.status)}
                                            </Stack>
                                            <Box mt={2}>
                                                <Stack direction="row" alignItems="center" spacing={1}>
                                                    <PulsingDot color={getStatusColor(data.status)} />
                                                    <Typography variant="body2" color={`${getStatusColor(data.status)}.main`}>
                                                        {data.status}
                                                    </Typography>
                                                </Stack>
                                                {data.latency && (
                                                    <Typography variant="caption" color="text.secondary">
                                                        Latency: {data.latency}ms
                                                    </Typography>
                                                )}
                                                {data.connections !== undefined && (
                                                    <Typography variant="caption" color="text.secondary">
                                                        Connections: {data.connections}
                                                    </Typography>
                                                )}
                                                {data.memory && (
                                                    <Typography variant="caption" color="text.secondary">
                                                        Memory: {data.memory}MB
                                                    </Typography>
                                                )}
                                            </Box>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>

                        {/* Performance Metrics */}
                        <Grid container spacing={3} sx={{ mt: 2 }}>
                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            API Response Times
                                        </Typography>
                                        <ResponsiveContainer width="100%" height={300}>
                                            <LineChart data={marketActivity.slice(0, 20)}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="time" />
                                                <YAxis />
                                                <RechartsTooltip />
                                                <Line
                                                    type="monotone"
                                                    dataKey="latency"
                                                    stroke={theme.palette.primary.main}
                                                    strokeWidth={2}
                                                    dot={false}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </CardContent>
                                </Card>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Resource Usage
                                        </Typography>
                                        <ResponsiveContainer width="100%" height={300}>
                                            <RadarChart data={[
                                                { metric: 'CPU', value: 65 },
                                                { metric: 'Memory', value: 78 },
                                                { metric: 'Disk', value: 45 },
                                                { metric: 'Network', value: 82 },
                                                { metric: 'Cache', value: 91 },
                                            ]}>
                                                <PolarGrid />
                                                <PolarAngleAxis dataKey="metric" />
                                                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                                                <Radar
                                                    name="Usage"
                                                    dataKey="value"
                                                    stroke={theme.palette.primary.main}
                                                    fill={theme.palette.primary.main}
                                                    fillOpacity={0.6}
                                                />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    </CardContent>
                                </Card>
                            </Grid>
                        </Grid>
                    </motion.div>
                )}

                {activeTab === 1 && (
                    <motion.div
                        key="trading"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        <Grid container spacing={3}>
                            {/* Trading Metrics Cards */}
                            <Grid item xs={12} md={3}>
                                <Card sx={{ background: alpha(theme.palette.success.main, 0.1) }}>
                                    <CardContent>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                                            <Typography variant="subtitle2">Today's P&L</Typography>
                                            <MonetizationOn color="success" />
                                        </Stack>
                                        <Typography variant="h4" sx={{ mt: 2 }}>
                                            ₹{tradingMetrics.todayPnL.toLocaleString()}
                                        </Typography>
                                        <Typography variant="body2" color="success.main">
                                            +{((tradingMetrics.todayPnL / 100000) * 100).toFixed(2)}%
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Card>
                                    <CardContent>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                                            <Typography variant="subtitle2">Win Rate</Typography>
                                            <Timeline color="primary" />
                                        </Stack>
                                        <Typography variant="h4" sx={{ mt: 2 }}>
                                            {tradingMetrics.winRate}%
                                        </Typography>
                                        <LinearProgress
                                            variant="determinate"
                                            value={tradingMetrics.winRate}
                                            sx={{ mt: 1 }}
                                        />
                                    </CardContent>
                                </Card>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Card>
                                    <CardContent>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                                            <Typography variant="subtitle2">Sharpe Ratio</Typography>
                                            <Assessment color="secondary" />
                                        </Stack>
                                        <Typography variant="h4" sx={{ mt: 2 }}>
                                            {tradingMetrics.sharpeRatio.toFixed(2)}
                                        </Typography>
                                        <Chip
                                            label={tradingMetrics.sharpeRatio > 1 ? 'Excellent' : 'Good'}
                                            color={tradingMetrics.sharpeRatio > 1 ? 'success' : 'warning'}
                                            size="small"
                                            sx={{ mt: 1 }}
                                        />
                                    </CardContent>
                                </Card>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Card sx={{ background: alpha(theme.palette.error.main, 0.1) }}>
                                    <CardContent>
                                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                                            <Typography variant="subtitle2">Max Drawdown</Typography>
                                            <TrendingDown color="error" />
                                        </Stack>
                                        <Typography variant="h4" sx={{ mt: 2 }}>
                                            {tradingMetrics.maxDrawdown}%
                                        </Typography>
                                        <Typography variant="body2" color="error.main">
                                            Risk Level: Moderate
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Top Movers */}
                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Top Gainers
                                        </Typography>
                                        <List dense>
                                            {topMovers.gainers.slice(0, 5).map((stock, idx) => (
                                                <ListItem key={idx}>
                                                    <ListItemIcon>
                                                        <Avatar sx={{ bgcolor: 'success.main', width: 32, height: 32 }}>
                                                            <TrendingUp fontSize="small" />
                                                        </Avatar>
                                                    </ListItemIcon>
                                                    <ListItemText
                                                        primary={stock.symbol}
                                                        secondary={stock.name}
                                                    />
                                                    <Chip
                                                        label={`+${stock.changePercent}%`}
                                                        color="success"
                                                        size="small"
                                                    />
                                                </ListItem>
                                            ))}
                                        </List>
                                    </CardContent>
                                </Card>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Top Losers
                                        </Typography>
                                        <List dense>
                                            {topMovers.losers.slice(0, 5).map((stock, idx) => (
                                                <ListItem key={idx}>
                                                    <ListItemIcon>
                                                        <Avatar sx={{ bgcolor: 'error.main', width: 32, height: 32 }}>
                                                            <TrendingDown fontSize="small" />
                                                        </Avatar>
                                                    </ListItemIcon>
                                                    <ListItemText
                                                        primary={stock.symbol}
                                                        secondary={stock.name}
                                                    />
                                                    <Chip
                                                        label={`${stock.changePercent}%`}
                                                        color="error"
                                                        size="small"
                                                    />
                                                </ListItem>
                                            ))}
                                        </List>
                                    </CardContent>
                                </Card>
                            </Grid>
                        </Grid>
                    </motion.div>
                )}

                {activeTab === 2 && (
                    <motion.div
                        key="heatmap"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Sector Performance Heatmap
                                </Typography>
                                <ResponsiveContainer width="100%" height={500}>
                                    <Treemap
                                        data={sectorPerformance}
                                        dataKey="value"
                                        aspectRatio={4 / 3}
                                        stroke="#fff"
                                        fill={theme.palette.primary.main}
                                    >
                                        <RechartsTooltip />
                                    </Treemap>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}

                {activeTab === 3 && (
                    <motion.div
                        key="risk"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                    >
                        <Grid container spacing={3}>
                            <Grid item xs={12}>
                                <Alert severity="info" icon={<Security />}>
                                    Risk monitoring is active. All positions are within defined risk parameters.
                                </Alert>
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Portfolio Risk Score
                                        </Typography>
                                        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                            <CircularProgress
                                                variant="determinate"
                                                value={75}
                                                size={200}
                                                thickness={4}
                                            />
                                            <Box
                                                sx={{
                                                    top: 0,
                                                    left: 0,
                                                    bottom: 0,
                                                    right: 0,
                                                    position: 'absolute',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                }}
                                            >
                                                <Typography variant="h2" component="div" color="text.secondary">
                                                    75
                                                </Typography>
                                            </Box>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                                            Risk level: Moderate
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>
                            <Grid item xs={12} md={8}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Risk Factors
                                        </Typography>
                                        <Grid container spacing={2}>
                                            {[
                                                { name: 'Market Risk', value: 65, icon: <ShowChart /> },
                                                { name: 'Liquidity Risk', value: 30, icon: <WaterDrop /> },
                                                { name: 'Volatility Risk', value: 80, icon: <Air /> },
                                                { name: 'Concentration Risk', value: 45, icon: <BubbleChart /> },
                                            ].map((risk) => (
                                                <Grid item xs={12} sm={6} key={risk.name}>
                                                    <Stack direction="row" spacing={2} alignItems="center">
                                                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                                                            {risk.icon}
                                                        </Avatar>
                                                        <Box sx={{ flexGrow: 1 }}>
                                                            <Typography variant="body2">{risk.name}</Typography>
                                                            <LinearProgress
                                                                variant="determinate"
                                                                value={risk.value}
                                                                sx={{ mt: 1 }}
                                                                color={risk.value > 70 ? 'error' : risk.value > 40 ? 'warning' : 'success'}
                                                            />
                                                        </Box>
                                                        <Typography variant="body2">{risk.value}%</Typography>
                                                    </Stack>
                                                </Grid>
                                            ))}
                                        </Grid>
                                    </CardContent>
                                </Card>
                            </Grid>
                        </Grid>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Live Activity Feed */}
            <Grid container spacing={3} sx={{ mt: 3 }}>
                <Grid item xs={12} md={8}>
                    <Card>
                        <CardContent>
                            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                                <Typography variant="h6">
                                    Live Market Activity
                                </Typography>
                                <Badge color="error" variant="dot">
                                    <Notifications />
                                </Badge>
                            </Stack>
                            <List dense sx={{ maxHeight: 400, overflow: 'auto' }}>
                                {marketActivity.map((activity, idx) => (
                                    <Fade in={true} timeout={500} key={idx}>
                                        <ListItem>
                                            <ListItemIcon>
                                                <Avatar sx={{ width: 32, height: 32, bgcolor: activity.type === 'buy' ? 'success.main' : 'error.main' }}>
                                                    {activity.type === 'buy' ? <TrendingUp /> : <TrendingDown />}
                                                </Avatar>
                                            </ListItemIcon>
                                            <ListItemText
                                                primary={`${activity.symbol} - ${activity.type.toUpperCase()}`}
                                                secondary={`${activity.quantity} @ ₹${activity.price}`}
                                            />
                                            <Typography variant="caption" color="text.secondary">
                                                {activity.time}
                                            </Typography>
                                        </ListItem>
                                    </Fade>
                                ))}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                System Notifications
                            </Typography>
                            <List dense>
                                {notifications.map((notif, idx) => (
                                    <ListItem key={idx}>
                                        <ListItemIcon>
                                            <Badge color={notif.type} variant="dot">
                                                <Notifications />
                                            </Badge>
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={notif.title}
                                            secondary={notif.message}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Container>
    );
};

export default EnhancedDashboard; 