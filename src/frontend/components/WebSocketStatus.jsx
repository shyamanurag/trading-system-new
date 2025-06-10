import {
    Circle,
    Refresh,
    Wifi,
    WifiOff
} from '@mui/icons-material';
import { Box, Chip, IconButton, Tooltip, Typography } from '@mui/material';
import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const WebSocketStatus = ({ userId = 'default_user' }) => {
    const {
        isConnected,
        connectionStats,
        lastMessage,
        reconnect
    } = useWebSocket(userId);

    const getStatusColor = () => {
        if (isConnected) return 'success';
        if (connectionStats.reconnectAttempts > 0) return 'warning';
        return 'error';
    };

    const getStatusText = () => {
        if (isConnected) return 'Connected';
        if (connectionStats.reconnectAttempts > 0) {
            return `Reconnecting... (${connectionStats.reconnectAttempts}/5)`;
        }
        return 'Disconnected';
    };

    return (
        <Box sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 1,
            borderRadius: 1,
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider'
        }}>
            <Circle
                sx={{
                    fontSize: 12,
                    color: isConnected ? 'success.main' : 'error.main',
                    animation: isConnected ? 'pulse 2s infinite' : 'none',
                    '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.5 },
                        '100%': { opacity: 1 }
                    }
                }}
            />

            <Typography variant="body2" sx={{ minWidth: 100 }}>
                WebSocket
            </Typography>

            <Chip
                label={getStatusText()}
                color={getStatusColor()}
                size="small"
                icon={isConnected ? <Wifi /> : <WifiOff />}
            />

            {connectionStats.lastError && (
                <Tooltip title={connectionStats.lastError}>
                    <Typography variant="caption" color="error">
                        Error
                    </Typography>
                </Tooltip>
            )}

            {!isConnected && (
                <Tooltip title="Reconnect">
                    <IconButton
                        size="small"
                        onClick={reconnect}
                        color="primary"
                    >
                        <Refresh />
                    </IconButton>
                </Tooltip>
            )}

            {lastMessage && (
                <Box sx={{ ml: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                        Last update: {new Date(lastMessage.timestamp).toLocaleTimeString()}
                    </Typography>
                </Box>
            )}
        </Box>
    );
};

export default WebSocketStatus; 