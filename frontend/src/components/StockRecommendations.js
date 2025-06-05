import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Snackbar,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  Refresh,
  Settings,
  Timeline,
  NotificationsActive,
  FilterList,
  Download,
  Share,
  InfoOutlined,
} from '@mui/icons-material';

const StockRecommendations = () => {
  // State management
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [realTimeEnabled, setRealTimeEnabled] = useState(false);
  const [filters, setFilters] = useState({
    riskLevel: 'all',
    minRiskReward: 0,
    maxRiskReward: 10,
    strategies: 'all'
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(300000); // 5 minutes
  const [notification, setNotification] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Refs
  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const retryTimeoutRef = useRef(null);

  // Enhanced fetchRecommendations with error handling and retry logic
  const fetchRecommendations = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      
      // Build query parameters based on filters
      const queryParams = new URLSearchParams();
      if (filters.riskLevel !== 'all') queryParams.append('risk_level', filters.riskLevel);
      if (filters.strategies !== 'all') queryParams.append('strategy', filters.strategies);
      queryParams.append('min_risk_reward', filters.minRiskReward);
      queryParams.append('max_risk_reward', filters.maxRiskReward);

      const response = await fetch(`/api/v1/recommendations?${queryParams}`);
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please login again.');
        } else if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.');
        } else if (response.status >= 500) {
          throw new Error('Server error. Please try again later.');
        }
        throw new Error(`Failed to fetch recommendations (${response.status})`);
      }
      
      const data = await response.json();
      
      // Validate response data structure
      if (!Array.isArray(data)) {
        throw new Error('Invalid response format');
      }
      
      setRecommendations(data);
      setLastUpdate(new Date());
      setError(null);
      
      // Show success notification for manual refreshes
      if (!showLoading && data.length > 0) {
        setNotification({
          type: 'success',
          message: `Updated ${data.length} recommendations`
        });
      }
      
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err.message);
      
      // Show error notification
      setNotification({
        type: 'error',
        message: err.message
      });
      
      // Retry logic with exponential backoff
      if (!retryTimeoutRef.current) {
        retryTimeoutRef.current = setTimeout(() => {
          retryTimeoutRef.current = null;
          fetchRecommendations(false);
        }, 5000); // Retry after 5 seconds
      }
      
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    if (!realTimeEnabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Get auth token from localStorage or context
      const token = localStorage.getItem('auth_token');
      const wsUrl = `ws://localhost:8002/ws/recommendations${token ? `?token=${token}` : ''}`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setNotification({
          type: 'info',
          message: 'Real-time updates enabled'
        });
        
        // Subscribe to recommendation updates
        wsRef.current.send(JSON.stringify({
          action: 'subscribe',
          type: 'recommendations',
          filters: filters
        }));
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'recommendation_update') {
            // Update specific recommendation
            setRecommendations(prev => 
              prev.map(rec => 
                rec.symbol === data.symbol ? { ...rec, ...data.data } : rec
              )
            );
            setLastUpdate(new Date());
          } else if (data.type === 'recommendations_refresh') {
            // Full refresh
            setRecommendations(data.data);
            setLastUpdate(new Date());
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        
        // Auto-reconnect if real-time is still enabled
        if (realTimeEnabled) {
          setTimeout(connectWebSocket, 3000);
        }
      };
      
    } catch (err) {
      console.error('Error connecting WebSocket:', err);
      setConnectionStatus('error');
    }
  }, [realTimeEnabled, filters]);

  // Close WebSocket connection
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setConnectionStatus('disconnected');
    }
  }, []);

  // Setup intervals and WebSocket
  useEffect(() => {
    // Initial fetch
    fetchRecommendations();
    
    // Setup refresh interval
    if (!realTimeEnabled && refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchRecommendations(false);
      }, refreshInterval);
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [fetchRecommendations, realTimeEnabled, refreshInterval]);

  // Handle real-time toggle
  useEffect(() => {
    if (realTimeEnabled) {
      // Clear interval when switching to real-time
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      connectWebSocket();
    } else {
      disconnectWebSocket();
      // Restart interval if needed
      if (refreshInterval > 0) {
        intervalRef.current = setInterval(() => {
          fetchRecommendations(false);
        }, refreshInterval);
      }
    }
    
    return () => {
      if (!realTimeEnabled) {
        disconnectWebSocket();
      }
    };
  }, [realTimeEnabled, connectWebSocket, disconnectWebSocket, refreshInterval, fetchRecommendations]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
    };
  }, [disconnectWebSocket]);

  // Helper functions
  const getRecommendationColor = (type) => {
    switch (type.toLowerCase()) {
      case 'buy':
      case 'strong_buy':
        return 'success';
      case 'sell':
      case 'strong_sell':
        return 'error';
      case 'hold':
        return 'info';
      default:
        return 'warning';
    }
  };

  const getRecommendationIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'buy':
      case 'strong_buy':
        return <TrendingUp />;
      case 'sell':
      case 'strong_sell':
        return <TrendingDown />;
      case 'hold':
        return <Timeline />;
      default:
        return <Warning />;
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  const handleManualRefresh = () => {
    fetchRecommendations(true);
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setSettingsOpen(false);
    
    // Update WebSocket subscription if connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'update_filters',
        filters: newFilters
      }));
    }
  };

  const handleExportData = () => {
    const dataStr = JSON.stringify(recommendations, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `recommendations_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const filteredRecommendations = recommendations.filter(rec => {
    if (filters.riskLevel !== 'all' && rec.riskLevel !== filters.riskLevel) return false;
    if (rec.riskRewardRatio < filters.minRiskReward || rec.riskRewardRatio > filters.maxRiskReward) return false;
    if (filters.strategies !== 'all' && rec.strategy !== filters.strategies) return false;
    return true;
  });

  if (loading && recommendations.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading recommendations...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Section */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
      <Typography variant="h4" gutterBottom>
        Stock Recommendations
      </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="subtitle1" color="text.secondary">
              Based on our AI-powered analysis
            </Typography>
            <Badge
              badgeContent={filteredRecommendations.length}
              color="primary"
              showZero
            >
              <Chip
                icon={connectionStatus === 'connected' ? <NotificationsActive /> : undefined}
                label={realTimeEnabled ? 'Live' : 'Static'}
                color={realTimeEnabled ? 'success' : 'default'}
                size="small"
              />
            </Badge>
          </Box>
          {lastUpdate && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastUpdate.toLocaleTimeString()}
      </Typography>
          )}
        </Box>
        
        <Box display="flex" gap={1}>
          <FormControlLabel
            control={
              <Switch
                checked={realTimeEnabled}
                onChange={(e) => setRealTimeEnabled(e.target.checked)}
                color="primary"
              />
            }
            label="Real-time"
            labelPlacement="start"
          />
          
          <Tooltip title="Refresh">
            <IconButton 
              onClick={handleManualRefresh} 
              disabled={loading}
              color="primary"
            >
              <Refresh />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Filters">
            <IconButton onClick={() => setSettingsOpen(true)} color="primary">
              <FilterList />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export Data">
            <IconButton onClick={handleExportData} color="primary">
              <Download />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Settings">
            <IconButton onClick={() => setSettingsOpen(true)} color="primary">
              <Settings />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={handleManualRefresh}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      )}
      
      {/* Recommendations Grid */}
      <Grid container spacing={3}>
        {filteredRecommendations.map((rec, index) => (
          <Grid item xs={12} md={6} lg={4} key={`${rec.symbol}-${index}`}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
                position: 'relative',
                overflow: 'visible'
              }}
            >
              {/* Real-time indicator */}
              {realTimeEnabled && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: -8,
                    right: -8,
                    width: 16,
                    height: 16,
                    backgroundColor: 'success.main',
                    borderRadius: '50%',
                    animation: 'pulse 2s infinite',
                    '@keyframes pulse': {
                      '0%': { transform: 'scale(1)', opacity: 1 },
                      '50%': { transform: 'scale(1.2)', opacity: 0.7 },
                      '100%': { transform: 'scale(1)', opacity: 1 },
                    }
                  }}
                />
              )}
              
              <CardContent sx={{ flexGrow: 1 }}>
                {/* Header */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box>
                  <Typography variant="h6" component="div">
                    {rec.symbol}
                  </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {rec.companyName || rec.symbol}
                    </Typography>
                  </Box>
                  <Box display="flex" gap={1} flexDirection="column" alignItems="flex-end">
                  <Chip
                    icon={getRecommendationIcon(rec.recommendation)}
                      label={rec.recommendation.replace('_', ' ').toUpperCase()}
                    color={getRecommendationColor(rec.recommendation)}
                    size="small"
                  />
                    <Chip
                      label={`${rec.riskLevel || 'Medium'} Risk`}
                      color={getRiskLevelColor(rec.riskLevel)}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </Box>

                {/* Price Information */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Current Price
                    </Typography>
                    <Typography variant="h6">
                      ₹{rec.currentPrice?.toFixed(2) || rec.entryPrice?.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Target Price
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      ₹{rec.target?.toFixed(2) || rec.targetPrice?.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Stop Loss
                    </Typography>
                    <Typography variant="body1" color="error">
                      ₹{rec.stopLoss?.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Risk/Reward
                    </Typography>
                    <Typography 
                      variant="body1"
                      color={rec.riskRewardRatio >= 2 ? 'success.main' : 'warning.main'}
                    >
                      1:{rec.riskRewardRatio?.toFixed(1)}
                    </Typography>
                  </Grid>
                </Grid>

                {/* Additional Metrics */}
                {rec.confidence && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Confidence: {(rec.confidence * 100).toFixed(0)}%
                    </Typography>
                    <Box sx={{ width: '100%', bgcolor: 'grey.300', borderRadius: 1, height: 4 }}>
                      <Box
                        sx={{
                          width: `${rec.confidence * 100}%`,
                          bgcolor: rec.confidence > 0.7 ? 'success.main' : 'warning.main',
                          height: '100%',
                          borderRadius: 1,
                          transition: 'width 0.3s ease'
                        }}
                      />
                    </Box>
                  </Box>
                )}

                {/* Strategy Information */}
                {rec.strategy && (
                  <Box mb={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                      Strategy
                    </Typography>
                    <Chip
                      label={rec.strategy}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  </Box>
                )}

                {/* Analysis */}
                <Box mb={2}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Analysis
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {rec.analysis || rec.reason || 'Technical analysis based on multiple indicators'}
                  </Typography>
                </Box>

                {/* Timestamp */}
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption" color="text.secondary">
                    {new Date(rec.timestamp || rec.updatedAt || Date.now()).toLocaleString()}
                  </Typography>
                  {rec.isNew && (
                    <Chip label="NEW" color="info" size="small" />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Empty State */}
      {filteredRecommendations.length === 0 && !loading && (
        <Box 
          display="flex" 
          flexDirection="column" 
          alignItems="center" 
          justifyContent="center" 
          minHeight="300px"
        >
          <InfoOutlined sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No recommendations found
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Try adjusting your filters or check back later for new recommendations.
          </Typography>
          <Button 
            variant="outlined" 
            onClick={handleManualRefresh}
            sx={{ mt: 2 }}
          >
            Refresh Recommendations
          </Button>
        </Box>
      )}

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Recommendation Settings</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Risk Level</InputLabel>
                <Select
                  value={filters.riskLevel}
                  label="Risk Level"
                  onChange={(e) => setFilters({ ...filters, riskLevel: e.target.value })}
                >
                  <MenuItem value="all">All Risk Levels</MenuItem>
                  <MenuItem value="low">Low Risk</MenuItem>
                  <MenuItem value="medium">Medium Risk</MenuItem>
                  <MenuItem value="high">High Risk</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Min Risk/Reward"
                type="number"
                value={filters.minRiskReward}
                onChange={(e) => setFilters({ ...filters, minRiskReward: parseFloat(e.target.value) || 0 })}
                inputProps={{ min: 0, step: 0.1 }}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Max Risk/Reward"
                type="number"
                value={filters.maxRiskReward}
                onChange={(e) => setFilters({ ...filters, maxRiskReward: parseFloat(e.target.value) || 10 })}
                inputProps={{ min: 0, step: 0.1 }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Strategy</InputLabel>
                <Select
                  value={filters.strategies}
                  label="Strategy"
                  onChange={(e) => setFilters({ ...filters, strategies: e.target.value })}
                >
                  <MenuItem value="all">All Strategies</MenuItem>
                  <MenuItem value="momentum">Momentum</MenuItem>
                  <MenuItem value="mean_reversion">Mean Reversion</MenuItem>
                  <MenuItem value="breakout">Breakout</MenuItem>
                  <MenuItem value="swing">Swing Trading</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {!realTimeEnabled && (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Refresh Interval</InputLabel>
                  <Select
                    value={refreshInterval}
                    label="Refresh Interval"
                    onChange={(e) => setRefreshInterval(e.target.value)}
                  >
                    <MenuItem value={60000}>1 minute</MenuItem>
                    <MenuItem value={300000}>5 minutes</MenuItem>
                    <MenuItem value={600000}>10 minutes</MenuItem>
                    <MenuItem value={1800000}>30 minutes</MenuItem>
                    <MenuItem value={0}>Manual only</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
          <Button onClick={() => handleFilterChange(filters)} variant="contained">
            Apply Filters
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={!!notification}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setNotification(null)} 
          severity={notification?.type || 'info'}
          sx={{ width: '100%' }}
        >
          {notification?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default StockRecommendations; 