import {
    Assessment,
    Dashboard,
    Description,
    ExitToApp, Menu as MenuIcon,
    Monitor,
    Notifications,
    People, Settings,
    Speed
} from '@mui/icons-material';
import {
    AppBar,
    Avatar,
    Badge,
    Box,
    Chip,
    Divider,
    Drawer,
    IconButton,
    List, ListItem, ListItemIcon, ListItemText,
    Menu, MenuItem,
    Toolbar, Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';

// Import all dashboard components
import AutonomousTradingDashboard from './AutonomousTradingDashboard';
import ComprehensiveTradingDashboard from './ComprehensiveTradingDashboard';
import RealTimeTradingMonitor from './RealTimeTradingMonitor';
import SystemHealthMonitor from './SystemHealthMonitor';
import TradingReportsHub from './TradingReportsHub';
import UserManagementDashboard from './UserManagementDashboard';

const EnhancedTradingDashboard = ({ userInfo, onLogout }) => {
    const [selectedView, setSelectedView] = useState('realtime');
    const [drawerOpen, setDrawerOpen] = useState(true);
    const [anchorEl, setAnchorEl] = useState(null);
    const [notifications, setNotifications] = useState([]);

    const menuItems = [
        { id: 'realtime', label: 'Real-Time Monitor', icon: <Monitor />, badge: 'LIVE' },
        { id: 'dashboard', label: 'Trading Dashboard', icon: <Dashboard /> },
        { id: 'reports', label: 'Reports Hub', icon: <Description /> },
        { id: 'autonomous', label: 'Autonomous Trading', icon: <Speed /> },
        { id: 'users', label: 'User Management', icon: <People /> },
        { id: 'health', label: 'System Health', icon: <Assessment /> },
    ];

    useEffect(() => {
        // Fetch notifications
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            const response = await fetch('/api/notifications', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setNotifications(data.notifications || []);
            }
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    };

    const handleProfileMenuOpen = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleProfileMenuClose = () => {
        setAnchorEl(null);
    };

    const renderContent = () => {
        switch (selectedView) {
            case 'realtime':
                return <RealTimeTradingMonitor />;
            case 'dashboard':
                return <ComprehensiveTradingDashboard userInfo={userInfo} onLogout={onLogout} />;
            case 'reports':
                return <TradingReportsHub />;
            case 'autonomous':
                return <AutonomousTradingDashboard />;
            case 'users':
                return <UserManagementDashboard />;
            case 'health':
                return <SystemHealthMonitor />;
            default:
                return <RealTimeTradingMonitor />;
        }
    };

    return (
        <Box sx={{ display: 'flex', height: '100vh' }}>
            {/* App Bar */}
            <AppBar
                position="fixed"
                sx={{
                    zIndex: (theme) => theme.zIndex.drawer + 1,
                    backgroundColor: '#1a1a1a'
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        edge="start"
                        onClick={() => setDrawerOpen(!drawerOpen)}
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>

                    <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
                        AlgoAuto Trading System
                    </Typography>

                    {/* Market Status */}
                    <Chip
                        label="Market Open"
                        color="success"
                        size="small"
                        sx={{ mr: 2 }}
                    />

                    {/* Notifications */}
                    <IconButton color="inherit" sx={{ mr: 2 }}>
                        <Badge badgeContent={notifications.length} color="error">
                            <Notifications />
                        </Badge>
                    </IconButton>

                    {/* User Profile */}
                    <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0 }}>
                        <Avatar sx={{ bgcolor: 'secondary.main' }}>
                            {userInfo?.username?.[0]?.toUpperCase() || 'U'}
                        </Avatar>
                    </IconButton>

                    <Menu
                        anchorEl={anchorEl}
                        open={Boolean(anchorEl)}
                        onClose={handleProfileMenuClose}
                    >
                        <MenuItem disabled>
                            <Typography variant="body2">{userInfo?.username}</Typography>
                        </MenuItem>
                        <MenuItem disabled>
                            <Typography variant="caption" color="text.secondary">
                                {userInfo?.role || 'Trader'}
                            </Typography>
                        </MenuItem>
                        <Divider />
                        <MenuItem onClick={() => { handleProfileMenuClose(); setSelectedView('settings'); }}>
                            <ListItemIcon><Settings fontSize="small" /></ListItemIcon>
                            Settings
                        </MenuItem>
                        <MenuItem onClick={() => { handleProfileMenuClose(); onLogout(); }}>
                            <ListItemIcon><ExitToApp fontSize="small" /></ListItemIcon>
                            Logout
                        </MenuItem>
                    </Menu>
                </Toolbar>
            </AppBar>

            {/* Side Drawer */}
            <Drawer
                variant="persistent"
                anchor="left"
                open={drawerOpen}
                sx={{
                    width: drawerOpen ? 240 : 0,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: 240,
                        boxSizing: 'border-box',
                        backgroundColor: '#f5f5f5',
                        borderRight: '1px solid #e0e0e0'
                    },
                }}
            >
                <Toolbar />
                <Box sx={{ overflow: 'auto' }}>
                    <List>
                        {menuItems.map((item) => (
                            <ListItem
                                button
                                key={item.id}
                                selected={selectedView === item.id}
                                onClick={() => setSelectedView(item.id)}
                                sx={{
                                    '&.Mui-selected': {
                                        backgroundColor: 'rgba(25, 118, 210, 0.08)',
                                        borderLeft: '3px solid #1976d2',
                                    },
                                    '&:hover': {
                                        backgroundColor: 'rgba(25, 118, 210, 0.04)',
                                    }
                                }}
                            >
                                <ListItemIcon sx={{ color: selectedView === item.id ? '#1976d2' : 'inherit' }}>
                                    {item.icon}
                                </ListItemIcon>
                                <ListItemText
                                    primary={item.label}
                                    primaryTypographyProps={{
                                        fontWeight: selectedView === item.id ? 600 : 400
                                    }}
                                />
                                {item.badge && (
                                    <Chip
                                        label={item.badge}
                                        size="small"
                                        color={item.badge === 'LIVE' ? 'error' : 'default'}
                                        sx={{
                                            height: 20,
                                            fontSize: '0.7rem',
                                            animation: item.badge === 'LIVE' ? 'pulse 2s infinite' : 'none'
                                        }}
                                    />
                                )}
                            </ListItem>
                        ))}
                    </List>

                    <Divider sx={{ my: 2 }} />

                    {/* Quick Stats */}
                    <Box sx={{ px: 2, pb: 2 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom>
                            QUICK STATS
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="body2">Daily P&L</Typography>
                            <Typography variant="h6" color="success.main">+₹25,450</Typography>
                        </Box>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="body2">Active Positions</Typography>
                            <Typography variant="h6">7</Typography>
                        </Box>
                    </Box>
                </Box>
            </Drawer>

            {/* Main Content */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    bgcolor: '#fafafa',
                    p: 0,
                    marginLeft: drawerOpen ? 0 : `-240px`,
                    transition: 'margin 0.3s',
                    mt: 8
                }}
            >
                {renderContent()}
            </Box>

            {/* CSS for pulse animation */}
            <style jsx global>{`
        @keyframes pulse {
          0% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
          100% {
            opacity: 1;
          }
        }
      `}</style>
        </Box>
    );
};

export default EnhancedTradingDashboard; 