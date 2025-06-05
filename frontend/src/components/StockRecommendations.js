import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { TrendingUp, TrendingDown, Warning } from '@mui/icons-material';

const StockRecommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations();
    // Refresh recommendations every 5 minutes
    const interval = setInterval(fetchRecommendations, 300000);
    return () => clearInterval(interval);
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/recommendations');
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }
      const data = await response.json();
      setRecommendations(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (type) => {
    switch (type.toLowerCase()) {
      case 'buy':
        return 'success';
      case 'sell':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getRecommendationIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'buy':
        return <TrendingUp />;
      case 'sell':
        return <TrendingDown />;
      default:
        return <Warning />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Stock Recommendations
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Based on our core engine analysis
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {recommendations.map((rec, index) => (
          <Grid item xs={12} md={6} lg={4} key={index}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 3,
                },
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" component="div">
                    {rec.symbol}
                  </Typography>
                  <Chip
                    icon={getRecommendationIcon(rec.recommendation)}
                    label={rec.recommendation}
                    color={getRecommendationColor(rec.recommendation)}
                    size="small"
                  />
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Entry Price
                    </Typography>
                    <Typography variant="body1">
                      ₹{rec.entryPrice.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Stop Loss
                    </Typography>
                    <Typography variant="body1" color="error">
                      ₹{rec.stopLoss.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Target
                    </Typography>
                    <Typography variant="body1" color="success.main">
                      ₹{rec.target.toFixed(2)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Risk/Reward
                    </Typography>
                    <Typography variant="body1">
                      {rec.riskRewardRatio.toFixed(2)}
                    </Typography>
                  </Grid>
                </Grid>

                <Box mt={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Analysis
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {rec.analysis}
                  </Typography>
                </Box>

                <Box mt={2}>
                  <Typography variant="caption" color="text.secondary">
                    Last Updated: {new Date(rec.timestamp).toLocaleString()}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default StockRecommendations; 