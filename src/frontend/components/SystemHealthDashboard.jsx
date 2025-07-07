import {
    CheckCircle as CheckIcon,
    Error as ErrorIcon,
    Info as InfoIcon,
    Refresh as RefreshIcon,
    Warning as WarningIcon
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Card,
    CardContent,
    Chip,
    Grid,
    IconButton,
    LinearProgress,
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
import React, { useEffect, useState } from 'react';

const SystemHealthDashboard = () => {
    const [healthData, setHealthData] = useState({
        endpoints: [],
        dataConsistency: [],
        systemMetrics: {},
        lastUpdate: null
    });
    const [loading, setLoading] = useState(false);

    // Critical endpoints to monitor
    const criticalEndpoints = [
        { name: 'Autonomous Trading', url: '/api/v1/autonomous/status', critical: true },
        { name: 'Dashboard Summary', url: '/api/v1/dashboard/summary', critical: true },
        { name: 'Trading Control', url: '/api/v1/control/trading/status', critical: false },
        { name: 'System Status', url: '/api/v1/system/status', critical: false },
        { name: 'Performance API', url: '/api/v1/performance/trades', critical: false },
        { name: 'Market Data', url: '/api/market/indices', critical: false }
    ];

    const checkSystemHealth = async () => {
        setLoading(true);

        try {
            console.log('🏥 Running comprehensive system health check...');

            const endpointResults = [];
            const dataConsistencyResults = [];
            let autonomousData = null;
            let dashboardData = null;

            // Test all endpoints
            for (const endpoint of criticalEndpoints) {
                try {
                    const startTime = Date.now();
                    const response = await fetch(endpoint.url);
                    const endTime = Date.now();
                    const responseTime = endTime - startTime;

                    let status = 'healthy';
                    let message = 'OK';

                    if (!response.ok) {
                        status = 'error';
                        message = `HTTP ${response.status}`;
                    } else if (responseTime > 2000) {
                        status = 'warning';
                        message = `Slow response (${responseTime}ms)`;
                    }

                    // Parse data for consistency checks
                    if (response.ok) {
                        const data = await response.json();
                        if (endpoint.name === 'Autonomous Trading') {
                            autonomousData = data;
                        } else if (endpoint.name === 'Dashboard Summary') {
                            dashboardData = data;
                        }
                    }

                    endpointResults.push({
                        name: endpoint.name,
                        url: endpoint.url,
                        status,
                        message,
                        responseTime,
                        critical: endpoint.critical,
                        timestamp: new Date().toISOString()
                    });

                } catch (error) {
                    endpointResults.push({
                        name: endpoint.name,
                        url: endpoint.url,
                        status: 'error',
                        message: error.message,
                        responseTime: null,
                        critical: endpoint.critical,
                        timestamp: new Date().toISOString()
                    });
                }
            }

            // Data consistency checks
            if (autonomousData && dashboardData) {
                const autonomousTrading = autonomousData.data || {};
                const dashboardTrading = dashboardData.autonomous_trading || {};

                // Compare key metrics
                const checks = [
                    {
                        metric: 'Total Trades',
                        autonomous: autonomousTrading.total_trades || 0,
                        dashboard: dashboardTrading.total_trades || 0,
                        tolerance: 0 // Should be exactly the same
                    },
                    {
                        metric: 'Daily P&L',
                        autonomous: autonomousTrading.daily_pnl || 0,
                        dashboard: dashboardTrading.daily_pnl || 0,
                        tolerance: 0.01 // Allow small rounding differences
                    },
                    {
                        metric: 'Trading Active',
                        autonomous: autonomousTrading.is_active || false,
                        dashboard: dashboardTrading.is_active || false,
                        tolerance: 0 // Should be exactly the same
                    }
                ];

                checks.forEach(check => {
                    const difference = Math.abs(check.autonomous - check.dashboard);
                    let status = 'consistent';
                    let message = 'Data matches between sources';

                    if (difference > check.tolerance) {
                        status = 'inconsistent';
                        message = `Mismatch: Autonomous=${check.autonomous}, Dashboard=${check.dashboard}`;
                    }

                    dataConsistencyResults.push({
                        metric: check.metric,
                        status,
                        message,
                        autonomousValue: check.autonomous,
                        dashboardValue: check.dashboard,
                        difference
                    });
                });
            }

            // Calculate system metrics
            const healthyEndpoints = endpointResults.filter(e => e.status === 'healthy').length;
            const totalEndpoints = endpointResults.length;
            const systemHealth = (healthyEndpoints / totalEndpoints) * 100;

            const criticalIssues = endpointResults.filter(e => e.critical && e.status === 'error').length;
            const dataInconsistencies = dataConsistencyResults.filter(d => d.status === 'inconsistent').length;

            setHealthData({
                endpoints: endpointResults,
                dataConsistency: dataConsistencyResults,
                systemMetrics: {
                    overallHealth: systemHealth,
                    healthyEndpoints,
                    totalEndpoints,
                    criticalIssues,
                    dataInconsistencies,
                    averageResponseTime: endpointResults
                        .filter(e => e.responseTime)
                        .reduce((sum, e) => sum + e.responseTime, 0) /
                        endpointResults.filter(e => e.responseTime).length || 0
                },
                lastUpdate: new Date()
            });

            console.log('✅ System health check completed');

        } catch (error) {
            console.error('❌ System health check failed:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkSystemHealth();

        // Auto-refresh every 2 minutes
        const interval = setInterval(checkSystemHealth, 120000);
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy':
            case 'consistent':
                return 'success';
            case 'warning':
                return 'warning';
            case 'error':
            case 'inconsistent':
                return 'error';
            default:
                return 'default';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'healthy':
            case 'consistent':
                return <CheckIcon />;
            case 'warning':
                return <WarningIcon />;
            case 'error':
            case 'inconsistent':
                return <ErrorIcon />;
            default:
                return <InfoIcon />;
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" component="h1">
                    System Health Monitor
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                        Last updated: {healthData.lastUpdate ? healthData.lastUpdate.toLocaleTimeString() : 'Never'}
                    </Typography>
                    <Tooltip title="Refresh Health Check">
                        <IconButton onClick={checkSystemHealth} disabled={loading}>
                            <RefreshIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* System Overview Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Overall Health
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Typography variant="h4" sx={{ mr: 1 }}>
                                    {healthData.systemMetrics.overallHealth?.toFixed(1) || 0}%
                                </Typography>
                                {healthData.systemMetrics.overallHealth >= 80 ?
                                    <CheckIcon color="success" /> :
                                    <ErrorIcon color="error" />
                                }
                            </Box>
                            <LinearProgress
                                variant="determinate"
                                value={healthData.systemMetrics.overallHealth || 0}
                                color={healthData.systemMetrics.overallHealth >= 80 ? 'success' : 'error'}
                            />
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Endpoint Status
                            </Typography>
                            <Typography variant="h4">
                                {healthData.systemMetrics.healthyEndpoints || 0}/{healthData.systemMetrics.totalEndpoints || 0}
                            </Typography>
                            <Typography variant="body2">
                                Healthy endpoints
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Critical Issues
                            </Typography>
                            <Typography variant="h4" color={healthData.systemMetrics.criticalIssues > 0 ? 'error' : 'success'}>
                                {healthData.systemMetrics.criticalIssues || 0}
                            </Typography>
                            <Typography variant="body2">
                                Need immediate attention
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Avg Response Time
                            </Typography>
                            <Typography variant="h4">
                                {healthData.systemMetrics.averageResponseTime?.toFixed(0) || 0}ms
                            </Typography>
                            <Typography variant="body2">
                                API performance
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Critical Alerts */}
            {healthData.systemMetrics.criticalIssues > 0 && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        ⚠️ Critical System Issues Detected
                    </Typography>
                    <Typography>
                        {healthData.systemMetrics.criticalIssues} critical endpoint(s) are failing.
                        This may impact trading operations. Please investigate immediately.
                    </Typography>
                </Alert>
            )}

            {healthData.systemMetrics.dataInconsistencies > 0 && (
                <Alert severity="warning" sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        📊 Data Inconsistency Warning
                    </Typography>
                    <Typography>
                        {healthData.systemMetrics.dataInconsistencies} data inconsistency issue(s) detected.
                        Trading data may not be accurately reflected across all interfaces.
                    </Typography>
                </Alert>
            )}

            {/* Endpoint Status Table */}
            <Paper sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ p: 2 }}>
                    Endpoint Health Status
                </Typography>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Service</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Response Time</TableCell>
                                <TableCell>Message</TableCell>
                                <TableCell>Critical</TableCell>
                                <TableCell>Last Check</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {healthData.endpoints.map((endpoint, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <Typography variant="body2" fontWeight="bold">
                                            {endpoint.name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {endpoint.url}
                                        </Typography>
                                    </TableCell>
                                    <TableCell>
                                        <Chip
                                            icon={getStatusIcon(endpoint.status)}
                                            label={endpoint.status.toUpperCase()}
                                            color={getStatusColor(endpoint.status)}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {endpoint.responseTime ? `${endpoint.responseTime}ms` : 'N/A'}
                                    </TableCell>
                                    <TableCell>{endpoint.message}</TableCell>
                                    <TableCell>
                                        <Chip
                                            label={endpoint.critical ? 'YES' : 'NO'}
                                            color={endpoint.critical ? 'error' : 'default'}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {new Date(endpoint.timestamp).toLocaleTimeString()}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>

            {/* Data Consistency Checks */}
            <Paper>
                <Typography variant="h6" sx={{ p: 2 }}>
                    Data Consistency Checks
                </Typography>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Metric</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Autonomous API</TableCell>
                                <TableCell>Dashboard API</TableCell>
                                <TableCell>Notes</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {healthData.dataConsistency.map((check, index) => (
                                <TableRow key={index}>
                                    <TableCell>{check.metric}</TableCell>
                                    <TableCell>
                                        <Chip
                                            icon={getStatusIcon(check.status)}
                                            label={check.status.toUpperCase()}
                                            color={getStatusColor(check.status)}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>{String(check.autonomousValue)}</TableCell>
                                    <TableCell>{String(check.dashboardValue)}</TableCell>
                                    <TableCell>{check.message}</TableCell>
                                </TableRow>
                            ))}
                            {healthData.dataConsistency.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={5} align="center">
                                        <Typography color="text.secondary">
                                            No data consistency checks available.
                                            Ensure both autonomous and dashboard endpoints are responding.
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </Box>
    );
};

export default SystemHealthDashboard; 