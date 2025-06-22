import { Refresh as RefreshIcon } from '@mui/icons-material';
import {
    Box,
    Chip,
    CircularProgress,
    IconButton,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tooltip,
    Typography,
} from '@mui/material';
import { format } from 'date-fns';
import React, { useEffect, useState } from 'react';
import usePolling from '../hooks/usePolling';

const LiveTradesDashboardPolling = () => {
    const [trades, setTrades] = useState([]);
    const [userMetrics, setUserMetrics] = useState({});
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState(new Date());

    // Use polling for real-time updates (every 3 seconds for trading data)
    const { data: liveTradesData, error: tradesError } = usePolling('/api/trades/live', 3000);
    const { data: metricsData, error: metricsError } = usePolling('/api/users/metrics', 5000);

    // Update trades when polling data changes
    useEffect(() => {
        if (liveTradesData) {
            setTrades(liveTradesData);
            setLastUpdated(new Date());
            setLoading(false);
        }
    }, [liveTradesData]);

    // Update metrics when polling data changes
    useEffect(() => {
        if (metricsData) {
            setUserMetrics(metricsData);
        }
    }, [metricsData]);

    const fetchData = async () => {
        try {
            setLoading(true);
            // Fetch trades
            const tradesResponse = await fetch('/api/trades/live');
            const tradesData = await tradesResponse.json();
            setTrades(tradesData);

            // Fetch user metrics
            const metricsResponse = await fetch('/api/users/metrics');
            const metricsData = await metricsResponse.json();
            setUserMetrics(metricsData);

            setLastUpdated(new Date());
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Initial fetch
    useEffect(() => {
        fetchData();
    }, []);

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'INR'
        }).format(value);
    };

    const formatPercentage = (value) => {
        return `${value.toFixed(2)}%`;
    };

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" component="h1">
                    Live Trading Dashboard
                    <Typography variant="caption" sx={{ ml: 2, color: 'text.secondary' }}>
                        (Auto-refresh every 3s)
                    </Typography>
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                        Last updated: {format(lastUpdated, 'HH:mm:ss')}
                    </Typography>
                    <Tooltip title="Refresh Now">
                        <IconButton onClick={fetchData} disabled={loading}>
                            <RefreshIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {(tradesError || metricsError) && (
                <Box sx={{ mb: 2 }}>
                    <Typography color="error">
                        Error loading data: {tradesError || metricsError}
                    </Typography>
                </Box>
            )}

            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress />
                </Box>
            ) : (
                <>
                    {/* User Metrics Summary */}
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h6" sx={{ mb: 2 }}>User Performance Summary</Typography>
                        <TableContainer component={Paper}>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>User ID</TableCell>
                                        <TableCell align="right">Current Capital</TableCell>
                                        <TableCell align="right">Opening Capital</TableCell>
                                        <TableCell align="right">Daily P&L</TableCell>
                                        <TableCell align="right">Daily P&L %</TableCell>
                                        <TableCell align="right">Open Trades</TableCell>
                                        <TableCell align="center">Status</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {Object.entries(userMetrics).map(([userId, metrics]) => (
                                        <TableRow key={userId}>
                                            <TableCell>{userId}</TableCell>
                                            <TableCell align="right">{formatCurrency(metrics.current_capital)}</TableCell>
                                            <TableCell align="right">{formatCurrency(metrics.opening_capital)}</TableCell>
                                            <TableCell
                                                align="right"
                                                sx={{
                                                    color: metrics.daily_pnl >= 0 ? 'success.main' : 'error.main',
                                                    fontWeight: 'bold'
                                                }}
                                            >
                                                {formatCurrency(metrics.daily_pnl)}
                                            </TableCell>
                                            <TableCell
                                                align="right"
                                                sx={{
                                                    color: metrics.daily_pnl_percentage >= 0 ? 'success.main' : 'error.main',
                                                    fontWeight: 'bold'
                                                }}
                                            >
                                                {formatPercentage(metrics.daily_pnl_percentage)}
                                            </TableCell>
                                            <TableCell align="right">{metrics.open_trades}</TableCell>
                                            <TableCell align="center">
                                                <Chip
                                                    label={metrics.hard_stop_status ? 'STOPPED' : 'ACTIVE'}
                                                    color={metrics.hard_stop_status ? 'error' : 'success'}
                                                    size="small"
                                                />
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Box>

                    {/* Live Trades Table */}
                    <Box>
                        <Typography variant="h6" sx={{ mb: 2 }}>Live Trades</Typography>
                        <TableContainer component={Paper}>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Trade ID</TableCell>
                                        <TableCell>User ID</TableCell>
                                        <TableCell>Symbol</TableCell>
                                        <TableCell align="right">Quantity</TableCell>
                                        <TableCell align="right">Entry Price</TableCell>
                                        <TableCell align="right">Current Price</TableCell>
                                        <TableCell align="right">P&L</TableCell>
                                        <TableCell align="right">P&L %</TableCell>
                                        <TableCell align="center">Status</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {trades.map((trade) => (
                                        <TableRow key={trade.trade_id}>
                                            <TableCell>{trade.trade_id}</TableCell>
                                            <TableCell>{trade.user_id}</TableCell>
                                            <TableCell>{trade.symbol}</TableCell>
                                            <TableCell align="right">{trade.quantity}</TableCell>
                                            <TableCell align="right">{formatCurrency(trade.entry_price)}</TableCell>
                                            <TableCell align="right">{formatCurrency(trade.current_price)}</TableCell>
                                            <TableCell
                                                align="right"
                                                sx={{
                                                    color: trade.pnl >= 0 ? 'success.main' : 'error.main',
                                                    fontWeight: 'bold'
                                                }}
                                            >
                                                {formatCurrency(trade.pnl)}
                                            </TableCell>
                                            <TableCell
                                                align="right"
                                                sx={{
                                                    color: trade.pnl_percentage >= 0 ? 'success.main' : 'error.main',
                                                    fontWeight: 'bold'
                                                }}
                                            >
                                                {formatPercentage(trade.pnl_percentage)}
                                            </TableCell>
                                            <TableCell align="center">
                                                <Chip
                                                    label={trade.status}
                                                    color={trade.status === 'OPEN' ? 'primary' : 'default'}
                                                    size="small"
                                                />
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Box>
                </>
            )}
        </Box>
    );
};

export default LiveTradesDashboardPolling; 