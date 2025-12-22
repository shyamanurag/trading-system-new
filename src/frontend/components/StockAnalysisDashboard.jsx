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

            {/* Debug: Show calculation inputs */}
            {levels.calculation_inputs && (
                <Box sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                        Pivot Data: {levels.calculation_inputs.data_source === 'daily_candle' ? '✅ Previous Day' : '⚠️ Intraday Estimate'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                            H: {formatPrice(levels.calculation_inputs.prev_high)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            L: {formatPrice(levels.calculation_inputs.prev_low)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            C: {formatPrice(levels.calculation_inputs.prev_close)}
                        </Typography>
                    </Box>
                </Box>
            )}

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

// Bollinger Bands Display Component
const BollingerBandsDisplay = ({ bollinger }) => {
    if (!bollinger || bollinger.error) {
        return (
            <Alert severity="info" sx={{ mt: 1 }}>
                Bollinger data not available
            </Alert>
        );
    }

    const getPositionColor = () => {
        switch (bollinger.position) {
            case 'ABOVE_UPPER': return '#f44336';
            case 'BELOW_LOWER': return '#4caf50';
            case 'UPPER_HALF': return '#ff9800';
            case 'LOWER_HALF': return '#8bc34a';
            default: return '#2196f3';
        }
    };

    return (
        <Box sx={{ p: 2 }}>
            <Grid container spacing={1}>
                <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">Upper</Typography>
                    <Typography variant="body2" color="error">
                        ₹{bollinger.upper_band?.toFixed(2)}
                    </Typography>
                </Grid>
                <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">Middle</Typography>
                    <Typography variant="body2">
                        ₹{bollinger.middle_band?.toFixed(2)}
                    </Typography>
                </Grid>
                <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">Lower</Typography>
                    <Typography variant="body2" color="success">
                        ₹{bollinger.lower_band?.toFixed(2)}
                    </Typography>
                </Grid>
            </Grid>
            <Divider sx={{ my: 1 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="caption" color="text.secondary">Bandwidth</Typography>
                    <Typography variant="body2">{bollinger.bandwidth?.toFixed(2)}%</Typography>
                </Box>
                <Box>
                    <Typography variant="caption" color="text.secondary">Position</Typography>
                    <Typography variant="body2" sx={{ color: getPositionColor() }}>
                        {bollinger.band_position?.toFixed(0)}%
                    </Typography>
                </Box>
            </Box>
            {bollinger.is_squeeze && (
                <Chip 
                    label={`SQUEEZE (${bollinger.squeeze_intensity?.toFixed(0)}%)`}
                    size="small"
                    color="warning"
                    sx={{ mt: 1 }}
                />
            )}
        </Box>
    );
};

// GARCH Volatility Display Component
const GARCHVolatilityDisplay = ({ garch, hv }) => {
    if (!garch || garch.error) {
        return (
            <Alert severity="info" sx={{ mt: 1 }}>
                Volatility data not available
            </Alert>
        );
    }

    const getRegimeColor = () => {
        switch (garch.regime) {
            case 'EXTREME': return '#c62828';
            case 'HIGH': return '#f44336';
            case 'NORMAL': return '#2196f3';
            case 'LOW': return '#4caf50';
            default: return '#9e9e9e';
        }
    };

    const getTrendIcon = () => {
        if (garch.trend === 'INCREASING') return <TrendingUp color="error" />;
        if (garch.trend === 'DECREASING') return <TrendingDown color="success" />;
        return <TrendingFlat />;
    };

    return (
        <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Box>
                    <Typography variant="caption" color="text.secondary">GARCH Vol</Typography>
                    <Typography variant="h6">{garch.garch_volatility?.toFixed(1)}%</Typography>
                </Box>
                <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="caption" color="text.secondary">Historical Vol</Typography>
                    <Typography variant="h6">{garch.historical_volatility?.toFixed(1)}%</Typography>
                </Box>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Chip 
                    label={garch.regime}
                    size="small"
                    sx={{ bgcolor: getRegimeColor(), color: 'white' }}
                />
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {getTrendIcon()}
                    <Typography variant="caption">{garch.trend}</Typography>
                </Box>
            </Box>
            {hv && !hv.error && (
                <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Typography variant="caption">HV5: {hv.hv_5?.toFixed(1)}%</Typography>
                    <Typography variant="caption">HV10: {hv.hv_10?.toFixed(1)}%</Typography>
                    <Typography variant="caption">HV20: {hv.hv_20?.toFixed(1)}%</Typography>
                </Box>
            )}
        </Box>
    );
};

// Options Analytics Display Component (for indices)
const OptionsAnalyticsDisplay = ({ options }) => {
    if (!options || !options.available) {
        return (
            <Alert severity="info" sx={{ mt: 1 }}>
                Options data not available
            </Alert>
        );
    }

    const getPCRColor = () => {
        if (options.pcr > 1.2) return '#4caf50';
        if (options.pcr < 0.8) return '#f44336';
        return '#ff9800';
    };

    const formatOI = (oi) => {
        if (!oi) return '-';
        if (oi >= 10000000) return (oi / 10000000).toFixed(2) + ' Cr';
        if (oi >= 100000) return (oi / 100000).toFixed(2) + ' L';
        return oi.toLocaleString();
    };

    return (
        <Box sx={{ p: 2 }}>
            <Grid container spacing={2}>
                <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Put-Call Ratio</Typography>
                    <Typography variant="h5" sx={{ color: getPCRColor() }}>
                        {options.pcr?.toFixed(2)}
                    </Typography>
                    <Chip 
                        label={options.pcr_interpretation?.replace('_', ' ')}
                        size="small"
                        sx={{ bgcolor: getPCRColor(), color: 'white' }}
                    />
                </Grid>
                <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Max Pain</Typography>
                    <Typography variant="h5">₹{options.max_pain?.toLocaleString()}</Typography>
                    <Typography variant="caption" color={options.distance_to_max_pain_pct > 0 ? 'success.main' : 'error.main'}>
                        {options.distance_to_max_pain_pct > 0 ? '+' : ''}{options.distance_to_max_pain_pct?.toFixed(2)}% away
                    </Typography>
                </Grid>
            </Grid>
            <Divider sx={{ my: 1 }} />
            <Grid container spacing={2}>
                <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Call OI</Typography>
                    <Typography variant="body2" color="error">{formatOI(options.total_call_oi)}</Typography>
                </Grid>
                <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Put OI</Typography>
                    <Typography variant="body2" color="success">{formatOI(options.total_put_oi)}</Typography>
                </Grid>
            </Grid>
            <Divider sx={{ my: 1 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Box>
                    <Typography variant="caption" color="text.secondary">IV Mean</Typography>
                    <Typography variant="body2">{options.iv_mean?.toFixed(1)}%</Typography>
                </Box>
                <Box>
                    <Typography variant="caption" color="text.secondary">ATM Strike</Typography>
                    <Typography variant="body2">₹{options.atm_strike?.toLocaleString()}</Typography>
                </Box>
            </Box>
            {options.expiry && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Expiry: {options.expiry}
                </Typography>
            )}
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
            
            if (!response) {
                setError('No response from server');
                setAnalysis(null);
                return;
            }
            
            const data = await response.json();

            if (data && data.success) {
                setAnalysis(data.data);
            } else {
                setError(data?.detail || data?.message || 'Failed to fetch analysis');
                setAnalysis(null);
            }
        } catch (err) {
            console.error('Stock analysis error:', err);
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

                    {/* Bollinger Bands */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Bollinger Bands
                                </Typography>
                                <BollingerBandsDisplay bollinger={analysis.indicators?.bollinger} />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Volatility Analysis */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Volatility (GARCH)
                                </Typography>
                                <GARCHVolatilityDisplay 
                                    garch={analysis.indicators?.garch}
                                    hv={analysis.indicators?.historical_volatility}
                                />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Options Analytics (for indices) */}
                    {analysis.options_analytics?.available && (
                        <Grid item xs={12} md={4}>
                            <Card sx={{ height: '100%' }}>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Options Analytics
                                    </Typography>
                                    <OptionsAnalyticsDisplay options={analysis.options_analytics} />
                                </CardContent>
                            </Card>
                        </Grid>
                    )}

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
