import {
    AccountBalance,
    Assessment,
    Dashboard,
    Menu as MenuIcon,
    Notifications,
    Star,
    Timeline,
    TrendingUp
} from '@mui/icons-material';
import {
    AppBar,
    Avatar,
    Badge,
    Box,
    Chip,
    CssBaseline,
    Divider,
    Drawer,
    IconButton,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Toolbar,
    Typography
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import React, { useState } from 'react';

// Import the comprehensive dashboard components
import EliteRecommendationsDashboard from './components/EliteRecommendationsDashboard';
import TradingDashboard from './components/TradingDashboard';
import UserPerformanceDashboard from './components/UserPerformanceDashboard';

const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#2196f3',
        },
        secondary: {
            main: '#f50057',
        },
        success: {
            main: '#4caf50',
        },
        error: {
            main: '#f44336',
        },
        warning: {
            main: '#ff9800',
        },
    },
    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        h4: {
            fontWeight: 600,
        },
        h5: {
            fontWeight: 600,
        },
        h6: {
            fontWeight: 600,
        },
    },
    components: {
        MuiCard: {
            styleOverrides: {
                root: {
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    borderRadius: 12,
                },
            },
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    textTransform: 'none',
                    fontWeight: 600,
                },
            },
        },
    },
});

const drawerWidth = 280;

const navigationItems = [
    {
        title: 'System Overview',
        icon: <Dashboard />,
        component: 'dashboard',
        description: 'Overall system status and health'
    },
    {
        title: 'Elite Recommendations',
        icon: <Star />,
        component: 'elite-recommendations',
        description: '10/10 trade setups only',
        badge: '10/10'
    },
    {
        title: 'User Performance',
        icon: <Assessment />,
        component: 'user-performance',
        description: 'Daily P&L, user analytics & management'
    },
    {
        title: 'Live Trading',
        icon: <TrendingUp />,
        component: 'live-trading',
        description: 'Real-time trade execution'
    },
    {
        title: 'Portfolio Analytics',
        icon: <Timeline />,
        component: 'portfolio-analytics',
        description: 'Advanced portfolio insights'
    },
    {
        title: 'Risk Management',
        icon: <AccountBalance />,
        component: 'risk-management',
        description: 'Risk monitoring and controls'
    }
];

function App() {
    const [mobileOpen, setMobileOpen] = useState(false);
    const [selectedComponent, setSelectedComponent] = useState('elite-recommendations');

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const renderComponent = () => {
        switch (selectedComponent) {
            case 'dashboard':
                return <TradingDashboard />;
            case 'elite-recommendations':
                return <EliteRecommendationsDashboard />;
            case 'user-performance':
                return <UserPerformanceDashboard />;
            case 'live-trading':
                return (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h4" gutterBottom>Live Trading</Typography>
                        <Typography variant="body1">
                            Live trading interface coming soon. This will include real-time order execution,
                            position management, and live P&L tracking.
                        </Typography>
                    </Box>
                );
            case 'portfolio-analytics':
                return (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h4" gutterBottom>Portfolio Analytics</Typography>
                        <Typography variant="body1">
                            Advanced portfolio analytics with risk-adjusted returns, correlation analysis,
                            and performance attribution coming soon.
                        </Typography>
                    </Box>
                );
            case 'risk-management':
                return (
                    <Box sx={{ p: 3 }}>
                        <Typography variant="h4" gutterBottom>Risk Management</Typography>
                        <Typography variant="body1">
                            Comprehensive risk management dashboard with position sizing, drawdown monitoring,
                            and risk alerts coming soon.
                        </Typography>
                    </Box>
                );
            default:
                return <EliteRecommendationsDashboard />;
        }
    };

    const drawer = (
        <div>
            {/* Header */}
            <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <Star />
                    </Avatar>
                    <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            Elite Trading System
                        </Typography>
                        <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            AI-Powered Analytics
                        </Typography>
                    </Box>
                </Box>
            </Box>

            <Divider />

            {/* System Status */}
            <Box sx={{ p: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                    System Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Box sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: 'success.main',
                        animation: 'pulse 2s infinite'
                    }} />
                    <Typography variant="body2">API Online</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Box sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: 'success.main',
                        animation: 'pulse 2s infinite'
                    }} />
                    <Typography variant="body2">Market Data Live</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: 'warning.main'
                    }} />
                    <Typography variant="body2">4 Active Trades</Typography>
                </Box>
            </Box>

            <Divider />

            {/* Navigation */}
            <List sx={{ pt: 1 }}>
                {navigationItems.map((item) => (
                    <ListItem key={item.component} disablePadding>
                        <ListItemButton
                            selected={selectedComponent === item.component}
                            onClick={() => setSelectedComponent(item.component)}
                            sx={{
                                margin: '4px 8px',
                                borderRadius: 2,
                                '&.Mui-selected': {
                                    bgcolor: 'primary.main',
                                    color: 'white',
                                    '&:hover': {
                                        bgcolor: 'primary.dark',
                                    },
                                    '& .MuiListItemIcon-root': {
                                        color: 'white',
                                    },
                                },
                            }}
                        >
                            <ListItemIcon>
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText
                                primary={item.title}
                                secondary={item.description}
                                sx={{
                                    '& .MuiListItemText-secondary': {
                                        fontSize: '0.75rem',
                                        opacity: selectedComponent === item.component ? 0.8 : 0.6,
                                    },
                                }}
                            />
                            {item.badge && (
                                <Chip
                                    label={item.badge}
                                    size="small"
                                    color={selectedComponent === item.component ? 'secondary' : 'primary'}
                                    sx={{ fontSize: '0.7rem' }}
                                />
                            )}
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>

            <Divider sx={{ mt: 2 }} />

            {/* Performance Summary */}
            <Box sx={{ p: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                    Today's Performance
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Total P&L:</Typography>
                    <Typography variant="body2" color="success.main" fontWeight={600}>
                        +₹25,750
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Win Rate:</Typography>
                    <Typography variant="body2" color="primary.main" fontWeight={600}>
                        91.2%
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Elite Trades:</Typography>
                    <Typography variant="body2" color="warning.main" fontWeight={600}>
                        6 Active
                    </Typography>
                </Box>
            </Box>
        </div>
    );

    return (
        <ThemeProvider theme={theme}>
            <Box sx={{ display: 'flex' }}>
                <CssBaseline />

                {/* App Bar */}
                <AppBar
                    position="fixed"
                    sx={{
                        width: { sm: `calc(100% - ${drawerWidth}px)` },
                        ml: { sm: `${drawerWidth}px` },
                        bgcolor: 'white',
                        color: 'text.primary',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    }}
                >
                    <Toolbar>
                        <IconButton
                            color="inherit"
                            aria-label="open drawer"
                            edge="start"
                            onClick={handleDrawerToggle}
                            sx={{ mr: 2, display: { sm: 'none' } }}
                        >
                            <MenuIcon />
                        </IconButton>

                        <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 600 }}>
                                {navigationItems.find(item => item.component === selectedComponent)?.title || 'Dashboard'}
                            </Typography>

                            {selectedComponent === 'elite-recommendations' && (
                                <Chip
                                    label="10/10 Scale"
                                    color="success"
                                    size="small"
                                    icon={<Star />}
                                />
                            )}
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Badge badgeContent={3} color="error">
                                <IconButton color="inherit">
                                    <Notifications />
                                </IconButton>
                            </Badge>

                            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                                <Typography variant="body2">AD</Typography>
                            </Avatar>
                        </Box>
                    </Toolbar>
                </AppBar>

                {/* Navigation Drawer */}
                <Box
                    component="nav"
                    sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
                >
                    <Drawer
                        variant="temporary"
                        open={mobileOpen}
                        onClose={handleDrawerToggle}
                        ModalProps={{ keepMounted: true }}
                        sx={{
                            display: { xs: 'block', sm: 'none' },
                            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                        }}
                    >
                        {drawer}
                    </Drawer>
                    <Drawer
                        variant="permanent"
                        sx={{
                            display: { xs: 'none', sm: 'block' },
                            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                        }}
                        open
                    >
                        {drawer}
                    </Drawer>
                </Box>

                {/* Main Content */}
                <Box
                    component="main"
                    sx={{
                        flexGrow: 1,
                        width: { sm: `calc(100% - ${drawerWidth}px)` },
                        minHeight: '100vh',
                        bgcolor: '#f5f5f5'
                    }}
                >
                    <Toolbar />
                    {renderComponent()}
                </Box>
            </Box>

            {/* Global Styles for animations */}
            <style jsx global>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
        </ThemeProvider>
    );
}

export default App; 