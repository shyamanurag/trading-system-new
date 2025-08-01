import {
    Download as DownloadIcon,
    Refresh as RefreshIcon,
    Warning as WarningIcon
} from '@mui/icons-material';
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
            is_active: false
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
            const response = await fetchWithAuth('/api/v1/trades');
            if (response.ok) {
                const data = await response.json();
                setTradeData(data.trades || []);
                setError(null);
            } else {
                setError('Failed to fetch real trades');
                setTradeData([]);
            }
        } catch (err) {
            setError('Error fetching trades: ' + err.message);
            setTradeData([]);
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
                trading_active: tradeData.summary.is_active,
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

            {!tradeData.summary.is_active && (
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
                                                        label={tradeData.summary.is_active ? 'YES' : 'NO'}
                        color={tradeData.summary.is_active ? 'success' : 'error'}
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