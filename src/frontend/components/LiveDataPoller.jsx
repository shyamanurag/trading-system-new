import { Circle, Cloud, CloudOff } from '@mui/icons-material';
import { Box, Chip, Typography } from '@mui/material';
import React from 'react';
import { API_ENDPOINTS } from '../api/config';
import usePolling from '../hooks/usePolling';

const LiveDataPoller = ({ userId }) => {
    // Poll for live data every 3 seconds
    const { data: marketData, error: marketError } = usePolling(
        API_ENDPOINTS.MARKET_STATUS.url,
        3000,
        true
    );

    // Poll for positions every 5 seconds
    const { data: positionsData, error: positionsError } = usePolling(
        userId ? `${API_ENDPOINTS.POSITIONS.url}?user_id=${userId}` : null,
        5000,
        !!userId
    );

    const isConnected = !marketError && !positionsError;
    const hasData = marketData || positionsData;

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
                    animation: isConnected && hasData ? 'pulse 2s infinite' : 'none',
                    '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.5 },
                        '100%': { opacity: 1 }
                    }
                }}
            />

            <Typography variant="body2" sx={{ minWidth: 100 }}>
                Live Data
            </Typography>

            <Chip
                icon={isConnected ? <Cloud /> : <CloudOff />}
                label={isConnected ? 'Polling Active' : 'Disconnected'}
                color={isConnected ? 'success' : 'error'}
                size="small"
                variant="filled"
            />

            {marketData?.market_status && (
                <Typography variant="caption" color="text.secondary">
                    Market: {marketData.market_status}
                </Typography>
            )}
        </Box>
    );
};

export default LiveDataPoller; 