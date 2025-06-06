import {
    CheckCircle,
    Pause,
    PlayArrow,
    Schedule,
    SmartToy,
    Stop,
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
    Divider,
    Grid,
    LinearProgress,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AutonomousTradingDashboard = ({ userInfo }) => {
    const [marketStatus, setMarketStatus] = useState(null);
    const [sessionStats, setSessionStats] = useState(null);
    const [activePositions, setActivePositions] = useState([]);
    const [schedulerStatus, setSchedulerStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchAutonomousData();
        const interval = setInterval(fetchAutonomousData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchAutonomousData = async () => {
        try {
            // Generate comprehensive autonomous trading data
            const mockMarketStatus = {
                is_market_open: true,
                is_trading_day: true,
                current_time: new Date().toLocaleTimeString('en-IN'),
                time_to_close_seconds: 3600 * 3.5, // 3.5 hours
                trading_session_active: true
            };

            const mockSessionStats = {
                session_id: `AUTO_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}`,
                total_trades: 15,
                winning_trades: 11,
                success_rate: 73.3,
                total_pnl: 18750.50,
                realized_pnl: 12500.00,
                unrealized_pnl: 6250.50,
                max_drawdown: 2.8,
                strategies_active: {
                    momentum_surfer: { trades: 6, pnl: 8500 },
                    volatility_explosion: { trades: 4, pnl: 5250 },
                    news_impact_scalper: { trades: 3, pnl: 3200 },
                    confluence_amplifier: { trades: 2, pnl: 1800 }
                },
                auto_actions: {
                    positions_opened: 15,
                    positions_closed: 11,
                    stop_losses_triggered: 3,
                    targets_hit: 8,
                    trailing_stops_moved: 12
                }
            };

            const mockPositions = [
                {
                    position_id: "AUTO_POS_001",
                    symbol: "RELIANCE",
                    strategy: "momentum_surfer",
                    entry_price: 2485.50,
                    current_price: 2492.30,
                    unrealized_pnl: 680.00,
                    auto_managed: true,
                    trailing_stop: true
                },
                {
                    position_id: "AUTO_POS_002",
                    symbol: "TCS",
                    strategy: "volatility_explosion",
                    entry_price: 3658.75,
                    current_price: 3672.20,
                    unrealized_pnl: 672.50,
                    auto_managed: true,
                    trailing_stop: false
                }
            ];

            const mockScheduler = {
                scheduler_active: true,
                auto_start_enabled: true,
                auto_stop_enabled: true,
                scheduled_events: [
                    { time: "09:10:00", event: "Pre-market system check", status: "COMPLETED" },
                    { time: "09:15:00", event: "Auto-start trading session", status: "COMPLETED" },
                    { time: "15:25:00", event: "Begin position closure", status: "SCHEDULED" },
                    { time: "15:30:00", event: "Force close all positions", status: "SCHEDULED" }
                ]
            };

            setMarketStatus(mockMarketStatus);
            setSessionStats(mockSessionStats);
            setActivePositions(mockPositions);
            setSchedulerStatus(mockScheduler);
            setError(null);
        } catch (err) {
            setError('Using demo data for autonomous trading features');
        } finally {
            setLoading(false);
        }
    };

    const handleEmergencyStop = async () => {
        try {
            // In production, this would call the emergency stop API
            alert('Emergency stop would be triggered - All autonomous trading halted');
        } catch (err) {
            console.error('Emergency stop failed:', err);
        }
    };

    const formatCurrency = (value) => `₹${value.toLocaleString()}`;
    const formatTime = (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    };

    if (loading) {
        return (
            <Box sx={{ p: 3 }}>
                <Typography variant="h6">Loading Autonomous Trading Data...</Typography>
                <LinearProgress sx={{ mt: 2 }} />
            </Box>
        );
    }

    return (
        <Grid container spacing={3}>
            {error && (
                <Grid item xs={12}>
                    <Alert severity="info">{error}</Alert>
                </Grid>
            )}

            {/* Header Status */}
            <Grid item xs={12}>
                <Card sx={{ background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)', color: 'white' }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box>
                                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                                    🤖 Autonomous Trading System
                                </Typography>
                                <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
                                    Zero Human Intervention • Market Open to Close Automation
                                </Typography>
                            </Box>
                            <Box sx={{ textAlign: 'right' }}>
                                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                    <Chip
                                        label={marketStatus?.is_market_open ? "Market OPEN" : "Market CLOSED"}
                                        color={marketStatus?.is_market_open ? "success" : "error"}
                                        variant="filled"
                                    />
                                    <Chip
                                        label="Auto Trading ACTIVE"
                                        color="primary"
                                        variant="filled"
                                    />
                                </Box>
                                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                                    {marketStatus?.time_to_close_seconds &&
                                        `Market closes in ${formatTime(marketStatus.time_to_close_seconds)}`
                                    }
                                </Typography>
                            </Box>
                        </Box>
                    </CardContent>
                </Card>
            </Grid>

            {/* Session Performance */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Session Performance
                        </Typography>
                        <Grid container spacing={2}>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Total Trades</Typography>
                                <Typography variant="h5">{sessionStats?.total_trades}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                                <Typography variant="h5" color="success.main">
                                    {sessionStats?.success_rate}%
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Total P&L</Typography>
                                <Typography variant="h5" color="success.main">
                                    {formatCurrency(sessionStats?.total_pnl || 0)}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Max Drawdown</Typography>
                                <Typography variant="h5" color="warning.main">
                                    {sessionStats?.max_drawdown}%
                                </Typography>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            </Grid>

            {/* Active Strategies */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <SmartToy sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Active Strategies
                        </Typography>
                        <List dense>
                            {Object.entries(sessionStats?.strategies_active || {}).map(([strategy, data], index) => (
                                <ListItem key={index} sx={{ px: 0 }}>
                                    <ListItemAvatar>
                                        <Avatar sx={{
                                            bgcolor: ['success.main', 'warning.main', 'info.main', 'secondary.main'][index % 4],
                                            width: 32, height: 32, fontSize: '0.875rem'
                                        }}>
                                            {strategy.split('_').map(word => word[0]).join('').toUpperCase()}
                                        </Avatar>
                                    </ListItemAvatar>
                                    <ListItemText
                                        primary={strategy.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        secondary={`${data.trades} trades • ${formatCurrency(data.pnl)} P&L`}
                                    />
                                    <Chip label="ACTIVE" color="success" size="small" />
                                </ListItem>
                            ))}
                        </List>
                    </CardContent>
                </Card>
            </Grid>

            {/* Auto-Managed Positions */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>Auto-Managed Positions</Typography>
                        <List dense>
                            {activePositions.map((position, index) => (
                                <ListItem key={index} sx={{ px: 0 }}>
                                    <ListItemAvatar>
                                        <Avatar sx={{ bgcolor: position.unrealized_pnl > 0 ? 'success.main' : 'error.main' }}>
                                            {position.symbol[0]}
                                        </Avatar>
                                    </ListItemAvatar>
                                    <ListItemText
                                        primary={position.symbol}
                                        secondary={
                                            <Box>
                                                <Typography variant="body2">
                                                    ₹{position.entry_price} → ₹{position.current_price}
                                                </Typography>
                                                <Typography
                                                    variant="body2"
                                                    color={position.unrealized_pnl > 0 ? 'success.main' : 'error.main'}
                                                >
                                                    P&L: {formatCurrency(position.unrealized_pnl)}
                                                    {position.trailing_stop && ' • Trailing Stop'}
                                                </Typography>
                                            </Box>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </CardContent>
                </Card>
            </Grid>

            {/* Autonomous Actions */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>Autonomous Actions</Typography>
                        <Grid container spacing={2}>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Opened</Typography>
                                <Typography variant="h6" color="primary.main">
                                    {sessionStats?.auto_actions?.positions_opened}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Closed</Typography>
                                <Typography variant="h6" color="secondary.main">
                                    {sessionStats?.auto_actions?.positions_closed}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Stop Losses</Typography>
                                <Typography variant="h6" color="error.main">
                                    {sessionStats?.auto_actions?.stop_losses_triggered}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">Targets Hit</Typography>
                                <Typography variant="h6" color="success.main">
                                    {sessionStats?.auto_actions?.targets_hit}
                                </Typography>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            </Grid>

            {/* Trading Scheduler */}
            <Grid item xs={12}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <Schedule sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Autonomous Trading Scheduler
                        </Typography>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                            <Chip
                                label="Scheduler ACTIVE"
                                color="success"
                                icon={<CheckCircle />}
                            />
                            <Chip
                                label="Auto-Start ENABLED"
                                color="primary"
                                icon={<PlayArrow />}
                            />
                            <Chip
                                label="Auto-Stop ENABLED"
                                color="primary"
                                icon={<Stop />}
                            />
                        </Box>

                        <Typography variant="subtitle2" gutterBottom>Today's Schedule:</Typography>
                        <List dense>
                            {schedulerStatus?.scheduled_events?.map((event, index) => (
                                <ListItem key={index} sx={{ px: 0 }}>
                                    <ListItemAvatar>
                                        <Avatar sx={{
                                            bgcolor: event.status === 'COMPLETED' ? 'success.main' : 'grey.400',
                                            width: 32, height: 32
                                        }}>
                                            {event.status === 'COMPLETED' ? <CheckCircle sx={{ fontSize: 16 }} /> : <Schedule sx={{ fontSize: 16 }} />}
                                        </Avatar>
                                    </ListItemAvatar>
                                    <ListItemText
                                        primary={`${event.time} - ${event.event}`}
                                        secondary={`Status: ${event.status}`}
                                    />
                                </ListItem>
                            ))}
                        </List>

                        <Divider sx={{ my: 2 }} />

                        <Typography variant="subtitle2" gutterBottom>Emergency Controls:</Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <Button
                                variant="outlined"
                                color="error"
                                size="small"
                                startIcon={<Warning />}
                                onClick={handleEmergencyStop}
                                disabled={!userInfo || userInfo.role !== 'admin'}
                            >
                                Emergency Stop
                            </Button>
                            <Button
                                variant="outlined"
                                color="warning"
                                size="small"
                                startIcon={<Pause />}
                                disabled={!userInfo || userInfo.role !== 'admin'}
                            >
                                Pause Trading
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                disabled={!userInfo || userInfo.role !== 'admin'}
                            >
                                View Logs
                            </Button>
                        </Box>

                        {(!userInfo || userInfo.role !== 'admin') && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                Admin privileges required for system controls
                            </Typography>
                        )}
                    </CardContent>
                </Card>
            </Grid>
        </Grid>
    );
};

export default AutonomousTradingDashboard; 