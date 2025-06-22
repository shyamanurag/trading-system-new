import {
    Circle,
    Info
} from '@mui/icons-material';
import { Box, Chip, Tooltip, Typography } from '@mui/material';
import React from 'react';

const WebSocketStatus = ({ userId }) => {
    // On Digital Ocean, we use polling instead of WebSocket
    // due to Cloudflare proxy limitations

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
                    color: 'info.main',
                    animation: 'pulse 2s infinite',
                    '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.5 },
                        '100%': { opacity: 1 }
                    }
                }}
            />

            <Typography variant="body2" sx={{ minWidth: 100 }}>
                Live Updates
            </Typography>

            <Tooltip title="Using polling for real-time updates on Digital Ocean">
                <Chip
                    icon={<Info />}
                    label="Polling Mode"
                    color="info"
                    size="small"
                    variant="filled"
                    sx={{
                        '& .MuiChip-icon': {
                            fontSize: 16,
                            marginLeft: 1
                        }
                    }}
                />
            </Tooltip>
        </Box>
    );
};

export default WebSocketStatus; 