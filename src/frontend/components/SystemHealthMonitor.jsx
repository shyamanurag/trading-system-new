import {
    CheckCircle,
    Error as ErrorIcon,
    Info,
    Warning
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Card,
    CardContent,
    Chip,
    Grid,
    LinearProgress,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { API_ENDPOINTS } from '../api/config';
import fetchWithAuth from '../api/fetchWithAuth';

const SystemHealthMonitor = () => {
    const [health, setHealth] = useState({
        overall: 'unknown',
        components: {},
        lastCheck: null
    });
    const [loading, setLoading] = useState(true);

    const fetchHealthStatus = async () => {
        try {
            const response = await fetchWithAuth(API_ENDPOINTS.HEALTH_READY_JSON.url);
            const data = await response.json();

            // Parse the response to determine health status
            const isHealthy = data.status === 'ready' || data.status === 'healthy';
            const components = {
                api: isHealthy ? 'healthy' : 'unhealthy',
                database: data.database_connected !== false ? 'healthy' : 'unhealthy',
                redis: data.redis_connected !== false ? 'healthy' : 'unhealthy',
                trading: data.trading_enabled ? 'active' : 'inactive'
            };

            setHealth({
                overall: isHealthy ? 'healthy' : 'unhealthy',
                components,
                lastCheck: new Date().toISOString(),
                details: data
            });
        } catch (error) {
            console.error('Error fetching health status:', error);
            setHealth({
                overall: 'error',
                components: {
                    api: 'error',
                    database: 'unknown',
                    redis: 'unknown',
                    trading: 'unknown'
                },
                lastCheck: new Date().toISOString(),
                error: error.message
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHealthStatus();
        const interval = setInterval(fetchHealthStatus, 30000); // Check every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy':
            case 'active':
                return 'success';
            case 'unhealthy':
            case 'inactive':
                return 'error';
            case 'warning':
                return 'warning';
            default:
                return 'default';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'healthy':
            case 'active':
                return <CheckCircle color="success" />;
            case 'unhealthy':
            case 'inactive':
                return <ErrorIcon color="error" />;
            case 'warning':
                return <Warning color="warning" />;
            default:
                return <Info color="disabled" />;
        }
    };

    if (loading) {
        return (
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <LinearProgress sx={{ flex: 1 }} />
                        <Typography variant="body2">Checking system health...</Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">System Health</Typography>
                    <Chip
                        icon={getStatusIcon(health.overall)}
                        label={health.overall.toUpperCase()}
                        color={getStatusColor(health.overall)}
                        size="small"
                    />
                </Box>

                {health.error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {health.error}
                    </Alert>
                )}

                <Grid container spacing={2}>
                    {Object.entries(health.components).map(([component, status]) => (
                        <Grid item xs={6} sm={3} key={component}>
                            <Box sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                p: 1,
                                borderRadius: 1,
                                bgcolor: 'background.default'
                            }}>
                                {getStatusIcon(status)}
                                <Typography variant="caption" sx={{ mt: 1, textTransform: 'capitalize' }}>
                                    {component}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    {typeof status === 'string' ? status : String(status || 'Unknown')}
                                </Typography>
                            </Box>
                        </Grid>
                    ))}
                </Grid>

                {health.lastCheck && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
                        Last checked: {new Date(health.lastCheck).toLocaleTimeString()}
                    </Typography>
                )}
            </CardContent>
        </Card>
    );
};

export default SystemHealthMonitor;