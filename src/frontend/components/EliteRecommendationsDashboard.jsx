import {
    CheckCircle,
    Info,
    Refresh,
    Star,
    TrendingDown,
    TrendingUp
} from '@mui/icons-material';
import {
    Alert,
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
    Grid,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableRow,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EliteRecommendationsDashboard = () => {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedTrade, setSelectedTrade] = useState(null);
    const [refreshing, setRefreshing] = useState(false);
    const [performanceData, setPerformanceData] = useState(null);

    const fetchRecommendations = async () => {
        try {
            setRefreshing(true);

            // Fetch elite recommendations
            const response = await fetch(`${API_BASE_URL}/api/recommendations/elite`);
            const data = await response.json();

            if (data.success) {
                setRecommendations(data.recommendations || generateMockRecommendations());
            } else {
                setRecommendations(generateMockRecommendations());
            }

            // Fetch performance data
            const perfResponse = await fetch(`${API_BASE_URL}/api/performance/elite-trades`);
            const perfData = await perfResponse.json();

            if (perfData.success) {
                setPerformanceData(perfData.data);
            } else {
                setPerformanceData(generateMockPerformanceData());
            }

            setError(null);
        } catch (err) {
            console.error('Error fetching recommendations:', err);
            setRecommendations(generateMockRecommendations());
            setPerformanceData(generateMockPerformanceData());
            setError('Using demo data - API not available');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchRecommendations();
        const interval = setInterval(fetchRecommendations, 300000); // Refresh every 5 minutes
        return () => clearInterval(interval);
    }, []);

    const generateMockRecommendations = () => {
        const symbols = ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'ITC', 'SBIN', 'BAJAJFINSV', 'LT'];
        const strategies = ['Breakout Play', 'Support Bounce', 'Momentum Surge', 'Mean Reversion', 'Trend Following'];

        return Array.from({ length: 6 }, (_, i) => {
            const symbol = symbols[i % symbols.length];
            const strategy = strategies[i % strategies.length];
            const entryPrice = 1000 + Math.random() * 2000;
            const stopLoss = entryPrice * (0.92 + Math.random() * 0.05);
            const target1 = entryPrice * (1.08 + Math.random() * 0.07);
            const target2 = entryPrice * (1.15 + Math.random() * 0.10);
            const target3 = entryPrice * (1.25 + Math.random() * 0.15);
            const validDays = 10 + Math.floor(Math.random() * 6); // 10-15 days

            return {
                recommendation_id: `ELITE_${Date.now()}_${i}`,
                symbol,
                strategy,
                direction: Math.random() > 0.3 ? 'LONG' : 'SHORT',
                entry_price: entryPrice,
                stop_loss: stopLoss,
                primary_target: target1,
                secondary_target: target2,
                tertiary_target: target3,
                confidence_score: 10.0,
                timeframe: `${validDays} Days`,
                timestamp: new Date(Date.now() - i * 3600000),
                valid_until: new Date(Date.now() + validDays * 24 * 3600000),
                risk_reward_ratio: (target1 - entryPrice) / (entryPrice - stopLoss),
                confluence_factors: [
                    'Perfect Support/Resistance levels',
                    'Volume surge with smart money flow',
                    'Technical pattern completion',
                    'Sector momentum alignment',
                    'Market regime confirmation'
                ],
                entry_conditions: [
                    'Break above previous high with volume',
                    'RSI above 60 with momentum',
                    'Price above 20 EMA'
                ],
                risk_metrics: {
                    risk_percent: Math.abs(entryPrice - stopLoss) / entryPrice * 100,
                    reward_percent: Math.abs(target1 - entryPrice) / entryPrice * 100,
                    position_size: 2 + Math.random() * 3
                },
                status: ['ACTIVE', 'TRIGGERED', 'TARGET_1_HIT'][Math.floor(Math.random() * 3)],
                current_price: entryPrice + (Math.random() - 0.5) * entryPrice * 0.1
            };
        });
    };

    const generateMockPerformanceData = () => {
        const last30Days = Array.from({ length: 30 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - 29 + i);
            return {
                date: date.toISOString().split('T')[0],
                elite_trades: Math.floor(Math.random() * 3),
                success_rate: 85 + Math.random() * 10,
                avg_return: 8 + Math.random() * 7,
                total_return: (Math.random() - 0.1) * 20
            };
        });

        return {
            summary: {
                total_trades: 89,
                success_rate: 91.2,
                avg_return_per_trade: 12.8,
                total_return_30d: 15.7,
                active_trades: 4
            },
            daily_performance: last30Days
        };
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'ACTIVE': return 'primary';
            case 'TRIGGERED': return 'warning';
            case 'TARGET_1_HIT': return 'success';
            case 'STOPPED_OUT': return 'error';
            default: return 'default';
        }
    };

    const getRiskRewardColor = (ratio) => {
        if (ratio >= 3) return 'success';
        if (ratio >= 2) return 'warning';
        return 'error';
    };

    const formatCurrency = (value) => `₹${value.toFixed(2)}`;
    const formatPercent = (value) => `${value.toFixed(1)}%`;

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ ml: 2 }}>Loading Elite Recommendations...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Star sx={{ color: 'gold' }} />
                        Elite Trade Recommendations
                        <Chip label="10/10 Only" color="success" size="small" />
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                        High-conviction trades with 10-15 day windows • Perfect confluence setups only
                    </Typography>
                </Box>
                <Button
                    variant="outlined"
                    startIcon={refreshing ? <CircularProgress size={16} /> : <Refresh />}
                    onClick={fetchRecommendations}
                    disabled={refreshing}
                >
                    {refreshing ? 'Refreshing...' : 'Refresh'}
                </Button>
            </Box>

            {error && (
                <Alert severity="info" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {/* Performance Summary */}
            {performanceData && (
                <Grid container spacing={3} sx={{ mb: 4 }}>
                    <Grid item xs={12} md={2.4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Total Trades
                                </Typography>
                                <Typography variant="h4">
                                    {performanceData.summary.total_trades}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={2.4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Success Rate
                                </Typography>
                                <Typography variant="h4" color="success.main">
                                    {formatPercent(performanceData.summary.success_rate)}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={2.4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Avg Return/Trade
                                </Typography>
                                <Typography variant="h4" color="primary.main">
                                    {formatPercent(performanceData.summary.avg_return_per_trade)}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={2.4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    30D Return
                                </Typography>
                                <Typography variant="h4" color={performanceData.summary.total_return_30d > 0 ? 'success.main' : 'error.main'}>
                                    {formatPercent(performanceData.summary.total_return_30d)}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={2.4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <Typography color="text.secondary" gutterBottom>
                                    Active Trades
                                </Typography>
                                <Typography variant="h4" color="warning.main">
                                    {performanceData.summary.active_trades}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Active Recommendations */}
            <Typography variant="h5" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp />
                Active Elite Recommendations
                <Badge badgeContent={recommendations.length} color="primary" />
            </Typography>

            <Grid container spacing={3}>
                {recommendations.map((rec) => (
                    <Grid item xs={12} lg={6} key={rec.recommendation_id}>
                        <Card
                            sx={{
                                border: '2px solid',
                                borderColor: rec.status === 'TARGET_1_HIT' ? 'success.main' : 'primary.main',
                                position: 'relative',
                                '&:hover': { elevation: 8, cursor: 'pointer' }
                            }}
                            onClick={() => setSelectedTrade(rec)}
                        >
                            {/* Elite Badge */}
                            <Box sx={{
                                position: 'absolute',
                                top: 8,
                                right: 8,
                                display: 'flex',
                                gap: 1
                            }}>
                                <Chip
                                    label="10/10"
                                    color="success"
                                    size="small"
                                    icon={<Star />}
                                />
                                <Chip
                                    label={rec.status}
                                    color={getStatusColor(rec.status)}
                                    size="small"
                                />
                            </Box>

                            <CardContent sx={{ pt: 5 }}>
                                {/* Header */}
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                    <Typography variant="h6">{rec.symbol}</Typography>
                                    <Chip
                                        label={rec.direction}
                                        color={rec.direction === 'LONG' ? 'success' : 'error'}
                                        size="small"
                                        icon={rec.direction === 'LONG' ? <TrendingUp /> : <TrendingDown />}
                                    />
                                    <Typography variant="body2" color="text.secondary">
                                        {rec.strategy}
                                    </Typography>
                                </Box>

                                {/* Price Levels */}
                                <Grid container spacing={2} sx={{ mb: 2 }}>
                                    <Grid item xs={6}>
                                        <Typography variant="body2" color="text.secondary">Entry</Typography>
                                        <Typography variant="h6">{formatCurrency(rec.entry_price)}</Typography>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="body2" color="text.secondary">Current</Typography>
                                        <Typography
                                            variant="h6"
                                            color={rec.current_price > rec.entry_price ? 'success.main' : 'error.main'}
                                        >
                                            {formatCurrency(rec.current_price)}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Typography variant="body2" color="text.secondary">Stop Loss</Typography>
                                        <Typography variant="body1" color="error.main">
                                            {formatCurrency(rec.stop_loss)}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={8}>
                                        <Typography variant="body2" color="text.secondary">Targets</Typography>
                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                            <Typography variant="body2" color="success.main">
                                                T1: {formatCurrency(rec.primary_target)}
                                            </Typography>
                                            <Typography variant="body2" color="success.main">
                                                T2: {formatCurrency(rec.secondary_target)}
                                            </Typography>
                                            <Typography variant="body2" color="success.main">
                                                T3: {formatCurrency(rec.tertiary_target)}
                                            </Typography>
                                        </Box>
                                    </Grid>
                                </Grid>

                                {/* Risk Metrics */}
                                <Box sx={{ mb: 2 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2">
                                            Risk/Reward: 1:{rec.risk_reward_ratio.toFixed(1)}
                                        </Typography>
                                        <Chip
                                            label={getRiskRewardColor(rec.risk_reward_ratio)}
                                            color={getRiskRewardColor(rec.risk_reward_ratio)}
                                            size="small"
                                        />
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <Typography variant="body2">
                                            Risk: {formatPercent(rec.risk_metrics.risk_percent)}
                                        </Typography>
                                        <Typography variant="body2">
                                            Reward: {formatPercent(rec.risk_metrics.reward_percent)}
                                        </Typography>
                                    </Box>
                                </Box>

                                {/* Time Window */}
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Valid: {rec.timeframe}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Until: {new Date(rec.valid_until).toLocaleDateString()}
                                    </Typography>
                                </Box>

                                {/* Confluence Factors Preview */}
                                <Box sx={{ mt: 2 }}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Perfect Confluence ({rec.confluence_factors.length} factors)
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                        {rec.confluence_factors.slice(0, 2).map((factor, idx) => (
                                            <Chip
                                                key={idx}
                                                label={factor}
                                                size="small"
                                                variant="outlined"
                                                color="success"
                                            />
                                        ))}
                                        {rec.confluence_factors.length > 2 && (
                                            <Chip
                                                label={`+${rec.confluence_factors.length - 2} more`}
                                                size="small"
                                                variant="outlined"
                                            />
                                        )}
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* Trade Details Dialog */}
            <Dialog
                open={!!selectedTrade}
                onClose={() => setSelectedTrade(null)}
                maxWidth="md"
                fullWidth
            >
                {selectedTrade && (
                    <>
                        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Star sx={{ color: 'gold' }} />
                            Elite Trade Details - {selectedTrade.symbol}
                            <Chip label="10/10" color="success" size="small" />
                        </DialogTitle>
                        <DialogContent>
                            <Grid container spacing={3}>
                                {/* Left Column - Trade Setup */}
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" gutterBottom>Trade Setup</Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">Strategy</Typography>
                                        <Typography variant="body1">{selectedTrade.strategy}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">Direction & Entry</Typography>
                                        <Typography variant="body1">
                                            {selectedTrade.direction} @ {formatCurrency(selectedTrade.entry_price)}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">Stop Loss</Typography>
                                        <Typography variant="body1" color="error.main">
                                            {formatCurrency(selectedTrade.stop_loss)}
                                            ({formatPercent(selectedTrade.risk_metrics.risk_percent)} risk)
                                        </Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">Profit Targets</Typography>
                                        <Typography variant="body1" color="success.main">
                                            T1: {formatCurrency(selectedTrade.primary_target)}<br />
                                            T2: {formatCurrency(selectedTrade.secondary_target)}<br />
                                            T3: {formatCurrency(selectedTrade.tertiary_target)}
                                        </Typography>
                                    </Box>
                                </Grid>

                                {/* Right Column - Analysis */}
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" gutterBottom>Why 10/10 Rating?</Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            Perfect Confluence Factors:
                                        </Typography>
                                        {selectedTrade.confluence_factors.map((factor, idx) => (
                                            <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                                <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />
                                                <Typography variant="body2">{factor}</Typography>
                                            </Box>
                                        ))}
                                    </Box>

                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            Entry Conditions:
                                        </Typography>
                                        {selectedTrade.entry_conditions.map((condition, idx) => (
                                            <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                                <Info sx={{ color: 'primary.main', fontSize: 16 }} />
                                                <Typography variant="body2">{condition}</Typography>
                                            </Box>
                                        ))}
                                    </Box>
                                </Grid>

                                {/* Full Width - Risk Metrics */}
                                <Grid item xs={12}>
                                    <Typography variant="h6" gutterBottom>Risk Management</Typography>
                                    <TableContainer component={Paper} variant="outlined">
                                        <Table size="small">
                                            <TableBody>
                                                <TableRow>
                                                    <TableCell>Risk/Reward Ratio</TableCell>
                                                    <TableCell>1:{selectedTrade.risk_reward_ratio.toFixed(2)}</TableCell>
                                                    <TableCell>Position Size</TableCell>
                                                    <TableCell>{selectedTrade.risk_metrics.position_size.toFixed(1)}% of capital</TableCell>
                                                </TableRow>
                                                <TableRow>
                                                    <TableCell>Risk Percentage</TableCell>
                                                    <TableCell color="error.main">{formatPercent(selectedTrade.risk_metrics.risk_percent)}</TableCell>
                                                    <TableCell>Reward Percentage</TableCell>
                                                    <TableCell color="success.main">{formatPercent(selectedTrade.risk_metrics.reward_percent)}</TableCell>
                                                </TableRow>
                                                <TableRow>
                                                    <TableCell>Valid Until</TableCell>
                                                    <TableCell>{new Date(selectedTrade.valid_until).toLocaleDateString()}</TableCell>
                                                    <TableCell>Time Window</TableCell>
                                                    <TableCell>{selectedTrade.timeframe}</TableCell>
                                                </TableRow>
                                            </TableBody>
                                        </Table>
                                    </TableContainer>
                                </Grid>
                            </Grid>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setSelectedTrade(null)}>Close</Button>
                            <Button variant="contained" color="primary">
                                Track This Trade
                            </Button>
                        </DialogActions>
                    </>
                )}
            </Dialog>
        </Box>
    );
};

export default EliteRecommendationsDashboard; 