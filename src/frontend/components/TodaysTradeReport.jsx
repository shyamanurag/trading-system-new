import {
    Download as DownloadIcon,
    Refresh as RefreshIcon,
    Warning as WarningIcon
} from '@mui/icons-material';
import { fetchWithAuth } from '../api/fetchWithAuth';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Grid,
    IconButton,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tooltip,
    Typography
} from '@mui/material';
import { format } from 'date-fns';
import React, { useEffect, useState } from 'react';

const TodaysTradeReport = () => {
    const [tradeData, setTradeData] = useState({
        trades: [],
        summary: {
            total_trades: 0,
            daily_pnl: 0,
            active_positions: 0,
            win_rate: 0,
            trading_active: false
        },
        lastUpdate: null
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [dataRecoveryDialog, setDataRecoveryDialog] = useState(false);
    const [recoveryResults, setRecoveryResults] = useState(null);

    // Fetch today's trade data
    const fetchTradeData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Get real trading status from autonomous endpoint
            const autonomousResponse = await fetch('/api/v1/autonomous/status');
            const autonomousData = await autonomousResponse.json();

            let trades = [];
            let summary = {
                total_trades: 0,
                daily_pnl: 0,
                active_positions: 0,
                win_rate: 0,
                trading_active: false
            };

            if (autonomousData.success && autonomousData.data) {
                const trading = autonomousData.data;
                console.log('🎯 Today\'s Trades using REAL DATA:', trading);

                summary = {
                    total_trades: trading.total_trades || 0,
                    daily_pnl: trading.daily_pnl || 0,
                    active_positions: trading.active_positions || 0,
                    win_rate: trading.success_rate || 0,
                    trading_active: trading.is_active || false,
                    session_id: trading.session_id,
                    start_time: trading.start_time,
                    active_strategies: trading.active_strategies || []
                };

                // FIXED: Get REAL trades from the trading system API endpoints
                try {
                    // Fetch real trades from backend live trades endpoint
                    const tradesResponse = await fetchWithAuth('/api/trades/live');
                    if (tradesResponse.ok) {
                        const tradesData = await tradesResponse.json();
                        let rawTrades = [];
                        if (Array.isArray(tradesData)) {
                            rawTrades = tradesData;
                        } else if (tradesData?.success && Array.isArray(tradesData.trades)) {
                            rawTrades = tradesData.trades;
                        } else if (tradesData?.success && Array.isArray(tradesData.data)) {
                            rawTrades = tradesData.data;
                        }

                        if (rawTrades.length > 0) {
                            trades = rawTrades.map(trade => ({
                                id: trade.trade_id || trade.order_id || trade.id,
                                symbol: trade.symbol || trade.tradingsymbol,
                                side: (trade.trade_type || trade.transaction_type || trade.side || '').toUpperCase(),
                                quantity: trade.quantity || trade.qty || 0,
                                entry_price: trade.price || trade.average_price || trade.avg_price || 0,
                                // temporary; will be overwritten by live positions enrichment below
                                current_price: trade.ltp || trade.last_price || trade.current_price || 0,
                                pnl: 0,
                                pnl_percent: 0,
                                status: trade.status || 'EXECUTED',
                                entry_time: trade.executed_at || trade.timestamp || trade.created_at,
                                strategy: trade.strategy || (trade.tag || '').split('_')[0] || 'Manual/Zerodha',
                                commission: trade.commission || 0
                            }));

                            // Enrich with live LTP from positions and compute P&L per trade
                            try {
                                const posRes = await fetchWithAuth('/api/v1/positions');
                                if (posRes.ok) {
                                    const posJson = await posRes.json();
                                    const posLists = [];
                                    if (posJson?.data) posLists.push(...posJson.data);
                                    if (posJson?.positions?.net) posLists.push(...posJson.positions.net);
                                    if (posJson?.positions?.day) posLists.push(...posJson.positions.day);

                                    const ltpMap = new Map();
                                    for (const p of posLists) {
                                        const sym = p.tradingsymbol || p.symbol;
                                        const ltp = p.last_price || p.ltp || p.close || 0;
                                        if (sym && ltp) ltpMap.set(sym, ltp);
                                    }

                                    trades = trades.map(t => {
                                        const ltp = ltpMap.get(t.symbol) ?? t.current_price ?? t.entry_price;
                                        const isBuy = t.side === 'BUY';
                                        const pnl = (isBuy ? (ltp - t.entry_price) : (t.entry_price - ltp)) * t.quantity;
                                        const pnlPct = t.entry_price > 0 ? (pnl / (t.entry_price * t.quantity)) * 100 : 0;
                                        return { ...t, current_price: ltp, pnl, pnl_percent: pnlPct };
                                    });
                                }
                            } catch (posErr) {
                                console.warn('Positions enrichment failed:', posErr);
                            }

                            // Finalize summary from computed P&L
                            const totalPnL = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);
                            const winningTrades = trades.filter(t => (t.pnl || 0) > 0).length;
                            summary.total_trades = trades.length;
                            summary.daily_pnl = totalPnL;
                            summary.win_rate = trades.length > 0 ? ((winningTrades / trades.length) * 100) : 0;
                        }
                    }
                } catch (tradesError) {
                    console.warn('Could not fetch real trades:', tradesError);
                }

                // If no trades from autonomous API, try the search API
                if (trades.length === 0 && summary.total_trades > 0) {
                    try {
                        const searchResponse = await fetch('/api/v1/search/trades?limit=50');
                        if (searchResponse.ok) {
                            const searchData = await searchResponse.json();
                            if (searchData.success && searchData.data && searchData.data.trades) {
                                trades = searchData.data.trades.map(trade => ({
                                    id: trade.trade_id || trade.order_id,
                                    symbol: trade.symbol,
                                    side: (trade.side || trade.transaction_type || '').toUpperCase(), // Ensure uppercase
                                    quantity: trade.quantity,
                                    entry_price: trade.price,
                                    current_price: trade.ltp || trade.current_price || trade.price, // Use LTP if available
                                    pnl: trade.pnl || 0,
                                    pnl_percent: ((trade.pnl || 0) / (trade.price * trade.quantity)) * 100,
                                    status: trade.status || 'EXECUTED',
                                    entry_time: trade.executed_at || trade.created_at,
                                    strategy: trade.strategy || 'Manual/Zerodha',
                                    commission: 0
                                }));
                            }
                        }
                    } catch (searchError) {
                        console.warn('Could not fetch trades from search API:', searchError);
                    }
                }

                // ELIMINATED: All mock trade generation removed - only real data allowed
                console.log(`✅ REAL TRADES ONLY: Found ${trades.length} actual trades`);
            }

            setTradeData({
                trades: trades,
                summary: summary,
                lastUpdate: new Date()
            });

        } catch (err) {
            setError(`Failed to fetch trade data: ${err.message}`);
            console.error('Trade data fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    // Emergency data recovery
    const performDataRecovery = async () => {
        setLoading(true);

        try {
            const recovery_sources = [
                '/api/v1/dashboard/summary',
                '/api/v1/system/status',
                '/api/v1/monitoring/daily-pnl'
            ];

            const results = {};

            for (const endpoint of recovery_sources) {
                try {
                    const response = await fetch(endpoint);
                    if (response.ok) {
                        const data = await response.json();
                        results[endpoint] = { success: true, data };
                    } else {
                        results[endpoint] = { success: false, status: response.status };
                    }
                } catch (err) {
                    results[endpoint] = { success: false, error: err.message };
                }
            }

            setRecoveryResults(results);
            setDataRecoveryDialog(true);

        } catch (err) {
            setError(`Data recovery failed: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Export trade data
    const exportTradeData = () => {
        const exportData = {
            date: new Date().toISOString().split('T')[0],
            timestamp: new Date().toISOString(),
            summary: tradeData.summary,
            trades: tradeData.trades,
            system_info: {
                trading_active: tradeData.summary.trading_active,
                session_id: tradeData.summary.session_id,
                active_strategies: tradeData.summary.active_strategies
            }
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trades_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    useEffect(() => {
        fetchTradeData();

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchTradeData, 30000);
        return () => clearInterval(interval);
    }, []);

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(value);
    };

    const getPnLColor = (pnl) => {
        if (pnl > 0) return '#4CAF50';
        if (pnl < 0) return '#F44336';
        return '#757575';
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" component="h1">
                    Today's Trade Report
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Refresh Data">
                        <IconButton onClick={fetchTradeData} disabled={loading}>
                            <RefreshIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Export Data">
                        <IconButton onClick={exportTradeData}>
                            <DownloadIcon />
                        </IconButton>
                    </Tooltip>
                    <Button
                        variant="outlined"
                        color="warning"
                        onClick={performDataRecovery}
                        startIcon={<WarningIcon />}
                    >
                        Data Recovery
                    </Button>
                </Box>
            </Box>

            {/* Status Alerts */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {!tradeData.summary.trading_active && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                    <Box>
                        <Typography variant="body1" fontWeight="bold">
                            ⚠️ Trading System Inactive
                        </Typography>
                        <Typography variant="body2">
                            The autonomous trading system is currently not active. No new trades are being executed.
                        </Typography>
                    </Box>
                </Alert>
            )}

            {tradeData.summary.total_trades === 0 && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body1">
                        📊 No trades executed today. This could mean:
                        <br />🔴 Live trading system active but no opportunities found
                        <br />• Market conditions don't meet strategy criteria
                        <br />• System was restarted and lost temporary data
                    </Typography>
                </Alert>
            )}

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Total Trades
                            </Typography>
                            <Typography variant="h4">
                                {tradeData.summary.total_trades}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Daily P&L
                            </Typography>
                            <Typography
                                variant="h4"
                                sx={{ color: getPnLColor(tradeData.summary.daily_pnl) }}
                            >
                                {formatCurrency(tradeData.summary.daily_pnl)}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Active Positions
                            </Typography>
                            <Typography variant="h4">
                                {tradeData.summary.active_positions}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Win Rate
                            </Typography>
                            <Typography variant="h4">
                                {tradeData.summary.win_rate.toFixed(1)}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* System Status */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    System Status
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Typography>
                            <strong>Trading Active:</strong> {' '}
                            <Chip
                                label={tradeData.summary.trading_active ? 'YES' : 'NO'}
                                color={tradeData.summary.trading_active ? 'success' : 'error'}
                                size="small"
                            />
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography>
                            <strong>Session ID:</strong> {tradeData.summary.session_id || 'None'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography>
                            <strong>Start Time:</strong> {tradeData.summary.start_time || 'Not started'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography>
                            <strong>Last Update:</strong> {tradeData.lastUpdate ? format(tradeData.lastUpdate, 'HH:mm:ss') : 'Never'}
                        </Typography>
                    </Grid>
                </Grid>

                {tradeData.summary.active_strategies?.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" gutterBottom>
                            <strong>Active Strategies:</strong>
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {tradeData.summary.active_strategies.map((strategy, index) => (
                                <Chip key={index} label={strategy} size="small" />
                            ))}
                        </Box>
                    </Box>
                )}
            </Paper>

            {/* Trades Table */}
            <Paper>
                <Typography variant="h6" sx={{ p: 2 }}>
                    Trade Details ({tradeData.trades.length})
                </Typography>

                {tradeData.trades.length > 0 ? (
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Symbol</TableCell>
                                    <TableCell>Side</TableCell>
                                    <TableCell align="right">Quantity</TableCell>
                                    <TableCell align="right">Entry Price</TableCell>
                                    <TableCell align="right">Current Price</TableCell>
                                    <TableCell align="right">P&L</TableCell>
                                    <TableCell align="right">P&L %</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Strategy</TableCell>
                                    <TableCell>Time</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {tradeData.trades.map((trade, index) => (
                                    <TableRow key={trade.id || index}>
                                        <TableCell>{trade.symbol}</TableCell>
                                        <TableCell>
                                            <Chip
                                                label={trade.side}
                                                color={trade.side === 'BUY' ? 'success' : 'error'}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell align="right">{trade.quantity}</TableCell>
                                        <TableCell align="right">{formatCurrency(trade.entry_price)}</TableCell>
                                        <TableCell align="right">{formatCurrency(trade.current_price)}</TableCell>
                                        <TableCell align="right" sx={{ color: getPnLColor(trade.pnl) }}>
                                            {formatCurrency(trade.pnl)}
                                        </TableCell>
                                        <TableCell align="right" sx={{ color: getPnLColor(trade.pnl_percent) }}>
                                            {trade.pnl_percent?.toFixed(2)}%
                                        </TableCell>
                                        <TableCell>
                                            <Chip label={trade.status} size="small" />
                                        </TableCell>
                                        <TableCell>{trade.strategy}</TableCell>
                                        <TableCell>
                                            {trade.entry_time ? format(new Date(trade.entry_time), 'HH:mm:ss') : 'N/A'}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                ) : (
                    <Box sx={{ p: 3, textAlign: 'center' }}>
                        <Typography color="textSecondary">
                            No trades to display
                        </Typography>
                    </Box>
                )}
            </Paper>

            {/* Data Recovery Dialog */}
            <Dialog
                open={dataRecoveryDialog}
                onClose={() => setDataRecoveryDialog(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Data Recovery Results</DialogTitle>
                <DialogContent>
                    {recoveryResults ? (
                        <Box>
                            {Object.entries(recoveryResults).map(([endpoint, result]) => (
                                <Box key={endpoint} sx={{ mb: 2 }}>
                                    <Typography variant="body2" fontWeight="bold">
                                        {endpoint}
                                    </Typography>
                                    <Typography
                                        variant="body2"
                                        color={result.success ? 'success.main' : 'error.main'}
                                    >
                                        {result.success ? '✅ Available' : '❌ Failed'}
                                    </Typography>
                                    {result.data && (
                                        <Typography variant="caption" component="pre" sx={{ maxHeight: 200, overflow: 'auto' }}>
                                            {JSON.stringify(result.data, null, 2)}
                                        </Typography>
                                    )}
                                </Box>
                            ))}
                        </Box>
                    ) : (
                        <Typography>No recovery data available</Typography>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDataRecoveryDialog(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default TodaysTradeReport; 