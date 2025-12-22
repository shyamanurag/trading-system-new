import {
    Analytics as AnalyticsIcon,
    ArrowDownward,
    ArrowUpward,
    Refresh as RefreshIcon,
    Search as SearchIcon,
    ShowChart as ChartIcon,
    TrendingDown,
    TrendingFlat,
    TrendingUp
} from '@mui/icons-material';
import {
    Alert,
    Autocomplete,
    Box,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Divider,
    Grid,
    IconButton,
    LinearProgress,
    Paper,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import fetchWithAuth from '../api/fetchWithAuth';

// Gauge component for indicators like RSI, MFI, VRSI
const IndicatorGauge = ({ value, label, zones, interpretation }) => {
    const getColor = () => {
        if (!value && value !== 0) return '#9e9e9e';
        if (value <= 30) return '#4caf50'; // Green - Oversold (bullish)
        if (value >= 70) return '#f44336'; // Red - Overbought (bearish)
        if (value <= 40) return '#8bc34a'; // Light green
        if (value >= 60) return '#ff9800'; // Orange
        return '#2196f3'; // Blue - Neutral
    };

    const getZoneLabel = () => {
        if (!interpretation) return '';
        return interpretation.replace('_', ' ');
    };

    return (
        <Box sx={{ textAlign: 'center', p: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
                {label}
            </Typography>
            <Box sx={{ position: 'relative', display: 'inline-flex', my: 1 }}>
                <CircularProgress
                    variant="determinate"
                    value={value || 0}
                    size={80}
                    thickness={6}
                    sx={{ color: getColor() }}
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
                    <Typography variant="h6" component="div" color="text.primary">
                        {value !== null && value !== undefined ? Math.round(value) : '-'}
                    </Typography>
                </Box>
            </Box>
            <Chip
                label={getZoneLabel() || 'N/A'}
                size="small"
                sx={{
                    bgcolor: getColor(),
                    color: 'white',
                    fontSize: '0.7rem'
                }}
            />
        </Box>
    );
};

// MACD Display Component
const MACDDisplay = ({ macd }) => {
    if (!macd || macd.error) {
        return (
            <Alert severity="info" sx={{ mt: 1 }}>
                MACD data not available
            </Alert>
        );
    }

    const getStateColor = () => {
        switch (macd.state) {
            case 'STRONG_BULLISH': return '#2e7d32';
            case 'BULLISH': return '#4caf50';
            case 'STRONG_BEARISH': return '#c62828';
            case 'BEARISH': return '#f44336';
            default: return '#9e9e9e';
        }
    };

    const getStateIcon = () => {
        if (macd.state?.includes('BULLISH')) return <TrendingUp />;
        if (macd.state?.includes('BEARISH')) return <TrendingDown />;
        return <TrendingFlat />;
    };

    return (
        <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <Chip
                    icon={getStateIcon()}
                    label={macd.state?.replace('_', ' ') || 'NEUTRAL'}
                    sx={{
                        bgcolor: getStateColor(),
                        color: 'white',
                        fontWeight: 'bold'
                    }}
                />
            </Box>
            
            <Grid container spacing={1}>
                <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">MACD Line</Typography>
                    <Typography variant="body2" fontWeight="bold">
                        {macd.macd_line?.toFixed(2) || '-'}
                    </Typography>
                </Grid>
                <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">Signal Line</Typography>
                    <Typography variant="body2" fontWeight="bold">
                        {macd.signal_line?.toFixed(2) || '-'}
                    </Typography>
                </Grid>
                <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">Histogram</Typography>
                    <Typography 
                        variant="body2" 
                        fontWeight="bold"
                        color={macd.histogram > 0 ? 'success.main' : 'error.main'}
                    >
                        {macd.histogram?.toFixed(2) || '-'}
                    </Typography>
                </Grid>
            </Grid>

            {macd.crossover && (
                <Chip
                    label={macd.crossover.replace('_', ' ')}
                    color={macd.crossover.includes('BULLISH') ? 'success' : 'error'}
                    size="small"
                    sx={{ mt: 1 }}
                />
            )}
        </Box>
    );
};

// Support/Resistance Levels Display
const SupportResistanceLevels = ({ levels, currentPrice }) => {
    if (!levels || levels.error) {
        return (
            <Alert severity="info" sx={{ mt: 1 }}>
                S/R levels not available
            </Alert>
        );
    }

    const formatPrice = (price) => {
        if (!price) return '-';
        return new Intl.NumberFormat('en-IN', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        }).format(price);
    };

    const getLevelColor = (level, current) => {
        if (!level || !current) return 'default';
        const diff = ((level - current) / current) * 100;
        if (Math.abs(diff) < 0.5) return 'warning'; // Very close
        if (diff > 0) return 'error'; // Resistance
        return 'success'; // Support
    };

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom textAlign="center">
                Price Position: <Chip label={levels.position?.replace('_', ' ') || 'N/A'} size="small" />
            </Typography>
            
            <Divider sx={{ my: 1 }} />
            
            <Grid container spacing={1}>
                {/* Resistance Levels */}
                <Grid item xs={6}>
                    <Typography variant="caption" color="error.main" fontWeight="bold">
                        RESISTANCE
                    </Typography>
                    {levels.resistance && (
                        <>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                                <Typography variant="caption">R1:</Typography>
                                <Typography variant="body2" color="error.main">
                                    {formatPrice(levels.resistance.r1)}
                                </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="caption">R2:</Typography>
                                <Typography variant="body2" color="error.main">
                                    {formatPrice(levels.resistance.r2)}
                                </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="caption">R3:</Typography>
                                <Typography variant="body2" color="error.main">
                                    {formatPrice(levels.resistance.r3)}
                                </Typography>
                            </Box>
                        </>
                    )}
                </Grid>

                {/* Support Levels */}
                <Grid item xs={6}>
                    <Typography variant="caption" color="success.main" fontWeight="bold">
                        SUPPORT
                    </Typography>
                    {levels.support && (
                        <>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                                <Typography variant="caption">S1:</Typography>
                                <Typography variant="body2" color="success.main">
                                    {formatPrice(levels.support.s1)}
                                </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="caption">S2:</Typography>
                                <Typography variant="body2" color="success.main">
                                    {formatPrice(levels.support.s2)}
                                </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="caption">S3:</Typography>
                                <Typography variant="body2" color="success.main">
                                    {formatPrice(levels.support.s3)}
                                </Typography>
                            </Box>
                        </>
                    )}
                </Grid>
            </Grid>

            <Divider sx={{ my: 1 }} />

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">Pivot:</Typography>
                <Typography variant="body2" fontWeight="bold">
                    {formatPrice(levels.pivot)}
                </Typography>
            </Box>

            {levels.nearest_support && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="success.main">Nearest Support:</Typography>
                    <Typography variant="body2" color="success.main" fontWeight="bold">
                        {formatPrice(levels.nearest_support)}
                    </Typography>
                </Box>
            )}

            {levels.nearest_resistance && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="error.main">Nearest Resistance:</Typography>
                    <Typography variant="body2" color="error.main" fontWeight="bold">
                        {formatPrice(levels.nearest_resistance)}
                    </Typography>
                </Box>
            )}
        </Box>
    );
};

// Volume Analysis Display
const VolumeAnalysis = ({ volume }) => {
    if (!volume || volume.error) {
        return (
            <Alert severity="info" sx={{ mt: 1 }}>
                Volume analysis not available
            </Alert>
        );
    }

    const formatVolume = (vol) => {
        if (!vol) return '-';
        if (vol >= 10000000) return (vol / 10000000).toFixed(2) + ' Cr';
        if (vol >= 100000) return (vol / 100000).toFixed(2) + ' L';
        if (vol >= 1000) return (vol / 1000).toFixed(2) + ' K';
        return vol.toString();
    };

    return (
        <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="caption">Current Volume:</Typography>
                <Typography variant="body2" fontWeight="bold">
                    {formatVolume(volume.current_volume)}
                </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="caption">Average Volume:</Typography>
                <Typography variant="body2">
                    {formatVolume(volume.average_volume)}
                </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="caption">Volume Ratio:</Typography>
                <Chip
                    label={`${volume.volume_ratio?.toFixed(2)}x`}
                    size="small"
                    color={volume.volume_ratio > 1.5 ? 'success' : volume.volume_ratio < 0.7 ? 'warning' : 'default'}
                />
            </Box>

            <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                Buy/Sell Pressure
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ flex: 1, mr: 1 }}>
                    <LinearProgress
                        variant="determinate"
                        value={volume.buy_pressure || 50}
                        sx={{
                            height: 12,
                            borderRadius: 6,
                            bgcolor: '#ffebee',
                            '& .MuiLinearProgress-bar': {
                                bgcolor: '#4caf50',
                                borderRadius: 6
                            }
                        }}
                    />
                </Box>
                <Typography variant="caption" sx={{ minWidth: 40 }}>
                    {volume.buy_pressure?.toFixed(0)}% Buy
                </Typography>
            </Box>

            <Chip
                label={volume.interpretation?.replace('_', ' ') || 'BALANCED'}
                size="small"
                color={
                    volume.interpretation === 'HIGH_BUYING' ? 'success' :
                    volume.interpretation === 'HIGH_SELLING' ? 'error' : 'default'
                }
            />
        </Box>
    );
};

// Algorithm Recommendation Display
const AlgorithmRecommendation = ({ recommendation }) => {
    if (!recommendation) {
        return (
            <Alert severity="info">
                Recommendation not available
            </Alert>
        );
    }

    const getRecommendationColor = () => {
        switch (recommendation.recommendation) {
            case 'BUY': return '#2e7d32';
            case 'WEAK_BUY': return '#4caf50';
            case 'SELL': return '#c62828';
            case 'WEAK_SELL': return '#f44336';
            case 'NEUTRAL': return '#ff9800';
            default: return '#9e9e9e';
        }
    };

    const getRecommendationIcon = () => {
        if (recommendation.recommendation?.includes('BUY')) return <ArrowUpward />;
        if (recommendation.recommendation?.includes('SELL')) return <ArrowDownward />;
        return <TrendingFlat />;
    };

    return (
        <Card 
            sx={{ 
                bgcolor: getRecommendationColor(), 
                color: 'white',
                textAlign: 'center',
                p: 2
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                {getRecommendationIcon()}
                <Typography variant="h5" fontWeight="bold" sx={{ ml: 1 }}>
                    {recommendation.recommendation?.replace('_', ' ') || 'N/A'}
                </Typography>
            </Box>
            
            <Typography variant="h6">
                Confidence: {recommendation.confidence?.toFixed(1)}%
            </Typography>

            <Divider sx={{ my: 2, bgcolor: 'rgba(255,255,255,0.3)' }} />

            <Grid container spacing={2}>
                <Grid item xs={6}>
                    <Typography variant="caption" sx={{ opacity: 0.8 }}>Bullish Score</Typography>
                    <Typography variant="h6">{recommendation.bullish_score?.toFixed(1)}%</Typography>
                </Grid>
                <Grid item xs={6}>
                    <Typography variant="caption" sx={{ opacity: 0.8 }}>Bearish Score</Typography>
                    <Typography variant="h6">{recommendation.bearish_score?.toFixed(1)}%</Typography>
                </Grid>
            </Grid>

            {recommendation.key_reasons && recommendation.key_reasons.length > 0 && (
                <Box sx={{ mt: 2, textAlign: 'left' }}>
                    <Typography variant="caption" sx={{ opacity: 0.8 }}>Key Reasons:</Typography>
                    {recommendation.key_reasons.map((reason, idx) => (
                        <Typography key={idx} variant="body2" sx={{ fontSize: '0.75rem' }}>
                            • {reason}
                        </Typography>
                    ))}
                </Box>
            )}
        </Card>
    );
};

// Main Component
const StockAnalysisDashboard = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSymbol, setSelectedSymbol] = useState(null);
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [availableSymbols, setAvailableSymbols] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);

    // Fetch available symbols on mount
    useEffect(() => {
        const fetchSymbols = async () => {
            try {
                const response = await fetchWithAuth('/api/v1/stock-analysis/symbols/available');
                const data = await response.json();
                if (data.success) {
                    setAvailableSymbols(data.symbols || []);
                }
            } catch (err) {
                console.error('Error fetching symbols:', err);
            }
        };
        fetchSymbols();
    }, []);

    // Search suggestions
    useEffect(() => {
        const fetchSuggestions = async () => {
            if (!searchQuery || searchQuery.length < 1) {
                setSuggestions([]);
                return;
            }

            setLoadingSuggestions(true);
            try {
                const response = await fetchWithAuth(
                    `/api/v1/search/autocomplete?query=${encodeURIComponent(searchQuery)}&category=symbols&limit=10`
                );
                const data = await response.json();
                if (data.success && data.suggestions) {
                    setSuggestions(data.suggestions.map(s => s.value || s.label));
                } else {
                    // Fallback to filtering available symbols
                    const filtered = availableSymbols.filter(s => 
                        s.toUpperCase().includes(searchQuery.toUpperCase())
                    ).slice(0, 10);
                    setSuggestions(filtered);
                }
            } catch (err) {
                // Fallback to local filtering
                const filtered = availableSymbols.filter(s => 
                    s.toUpperCase().includes(searchQuery.toUpperCase())
                ).slice(0, 10);
                setSuggestions(filtered);
            } finally {
                setLoadingSuggestions(false);
            }
        };

        const timer = setTimeout(fetchSuggestions, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, availableSymbols]);

    // Fetch analysis for selected symbol
    const fetchAnalysis = async (symbol) => {
        if (!symbol) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetchWithAuth(
                `/api/v1/stock-analysis/${encodeURIComponent(symbol)}`
            );
            const data = await response.json();

            if (data.success) {
                setAnalysis(data.data);
            } else {
                setError(data.detail || 'Failed to fetch analysis');
                setAnalysis(null);
            }
        } catch (err) {
            setError(err.message || 'Failed to connect to analysis service');
            setAnalysis(null);
        } finally {
            setLoading(false);
        }
    };

    const handleSymbolSelect = (symbol) => {
        if (symbol) {
            setSelectedSymbol(symbol);
            fetchAnalysis(symbol);
        }
    };

    const handleRefresh = () => {
        if (selectedSymbol) {
            fetchAnalysis(selectedSymbol);
        }
    };

    const formatNumber = (num) => {
        return new Intl.NumberFormat('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    };

    return (
        <Box sx={{ p: 2 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <AnalyticsIcon sx={{ fontSize: 32, mr: 1, color: 'primary.main' }} />
                <Typography variant="h5" fontWeight="bold">
                    Stock Technical Analysis
                </Typography>
            </Box>

            {/* Search Bar */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Autocomplete
                        freeSolo
                        options={suggestions}
                        loading={loadingSuggestions}
                        inputValue={searchQuery}
                        onInputChange={(event, newValue) => setSearchQuery(newValue || '')}
                        onChange={(event, newValue) => handleSymbolSelect(newValue)}
                        sx={{ flex: 1 }}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                placeholder="Search stock symbol (e.g., RELIANCE, NIFTY, TATASTEEL)..."
                                variant="outlined"
                                size="medium"
                                InputProps={{
                                    ...params.InputProps,
                                    startAdornment: (
                                        <>
                                            <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />
                                            {params.InputProps.startAdornment}
                                        </>
                                    ),
                                    endAdornment: (
                                        <>
                                            {loadingSuggestions && <CircularProgress size={20} />}
                                            {params.InputProps.endAdornment}
                                        </>
                                    )
                                }}
                            />
                        )}
                    />
                    
                    {selectedSymbol && (
                        <Tooltip title="Refresh Analysis">
                            <IconButton 
                                onClick={handleRefresh} 
                                disabled={loading}
                                color="primary"
                            >
                                <RefreshIcon />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>

                {availableSymbols.length > 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        {availableSymbols.length} symbols available for analysis
                    </Typography>
                )}
            </Paper>

            {/* Loading State */}
            {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                </Box>
            )}

            {/* Error State */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {/* Analysis Results */}
            {analysis && !loading && (
                <Grid container spacing={3}>
                    {/* Price Card */}
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        <ChartIcon sx={{ mr: 1, color: 'primary.main' }} />
                                        <Typography variant="h5" fontWeight="bold">
                                            {analysis.price_data?.symbol}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ textAlign: 'right' }}>
                                        <Typography variant="h4" fontWeight="bold">
                                            ₹{formatNumber(analysis.price_data?.ltp || 0)}
                                        </Typography>
                                        <Chip
                                            icon={analysis.price_data?.change >= 0 ? <ArrowUpward /> : <ArrowDownward />}
                                            label={`${analysis.price_data?.change >= 0 ? '+' : ''}${formatNumber(analysis.price_data?.change || 0)} (${analysis.price_data?.change_percent?.toFixed(2) || 0}%)`}
                                            color={analysis.price_data?.change >= 0 ? 'success' : 'error'}
                                            size="small"
                                        />
                                    </Box>
                                </Box>

                                <Divider sx={{ my: 2 }} />

                                <Grid container spacing={2}>
                                    <Grid item xs={3}>
                                        <Typography variant="caption" color="text.secondary">Open</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            ₹{formatNumber(analysis.price_data?.open || 0)}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <Typography variant="caption" color="text.secondary">High</Typography>
                                        <Typography variant="body2" fontWeight="bold" color="success.main">
                                            ₹{formatNumber(analysis.price_data?.high || 0)}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <Typography variant="caption" color="text.secondary">Low</Typography>
                                        <Typography variant="body2" fontWeight="bold" color="error.main">
                                            ₹{formatNumber(analysis.price_data?.low || 0)}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <Typography variant="caption" color="text.secondary">Volume</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {new Intl.NumberFormat('en-IN').format(analysis.price_data?.volume || 0)}
                                        </Typography>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Algorithm Recommendation */}
                    <Grid item xs={12} md={4}>
                        <Typography variant="h6" gutterBottom>
                            Algorithm Verdict
                        </Typography>
                        <AlgorithmRecommendation recommendation={analysis.recommendation} />
                    </Grid>

                    {/* Momentum Indicators */}
                    <Grid item xs={12} md={8}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Momentum Indicators
                                </Typography>
                                <Grid container>
                                    <Grid item xs={4}>
                                        <IndicatorGauge
                                            value={analysis.indicators?.rsi?.value}
                                            label="RSI (14)"
                                            interpretation={analysis.indicators?.rsi?.interpretation}
                                        />
                                    </Grid>
                                    <Grid item xs={4}>
                                        <IndicatorGauge
                                            value={analysis.indicators?.vrsi?.value}
                                            label="VRSI (Vol-Weighted)"
                                            interpretation={analysis.indicators?.vrsi?.interpretation}
                                        />
                                    </Grid>
                                    <Grid item xs={4}>
                                        <IndicatorGauge
                                            value={analysis.indicators?.mfi?.value}
                                            label="MFI (Money Flow)"
                                            interpretation={analysis.indicators?.mfi?.interpretation}
                                        />
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* MACD */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    MACD Analysis
                                </Typography>
                                <MACDDisplay macd={analysis.indicators?.macd} />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Support/Resistance */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Support & Resistance
                                </Typography>
                                <SupportResistanceLevels
                                    levels={analysis.support_resistance}
                                    currentPrice={analysis.price_data?.ltp}
                                />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Volume Analysis */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Volume Analysis
                                </Typography>
                                <VolumeAnalysis volume={analysis.volume_analysis} />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Data Source Info */}
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary" textAlign="center" display="block">
                            Data Source: {analysis.data_source} | 
                            Candles Analyzed: {analysis.candles_analyzed || 'N/A'} | 
                            Last Updated: {new Date(analysis.analyzed_at).toLocaleTimeString()}
                        </Typography>
                    </Grid>
                </Grid>
            )}

            {/* Empty State */}
            {!analysis && !loading && !error && (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                    <ChartIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                        Search for a stock to view technical analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Get RSI, MACD, Support/Resistance levels, volume analysis, and algorithm recommendations
                    </Typography>
                </Paper>
            )}
        </Box>
    );
};

export default StockAnalysisDashboard;
