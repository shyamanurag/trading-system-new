import { Refresh } from '@mui/icons-material';
import { Alert, Box, Button, Typography } from '@mui/material';
import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({
            error: error,
            errorInfo: errorInfo
        });

        // Log error details
        console.error('React Error Boundary caught an error:', error, errorInfo);

        // Special handling for React error #31 (object rendering)
        if (error.message && error.message.includes('Objects are not valid as a React child')) {
            console.error('REACT ERROR #31: Attempted to render object as React child');
            console.error('This often happens when trying to render objects like: {connected, username, symbols_active}');
            console.error('Fix: Convert object to string or render individual properties');
        }
    }

    render() {
        if (this.state.hasError) {
            return (
                <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Alert severity="error" sx={{ mb: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Frontend Error Detected
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            A rendering error occurred. This is usually caused by:
                        </Typography>
                        <Box component="ul" sx={{ textAlign: 'left', mb: 2 }}>
                            <li>Invalid data format from API</li>
                            <li>Object rendered as React child (Error #31)</li>
                            <li>Network connectivity issues</li>
                        </Box>

                        {this.state.error && (
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', display: 'block', mb: 2 }}>
                                Error: {this.state.error.message}
                            </Typography>
                        )}

                        <Button
                            variant="contained"
                            startIcon={<Refresh />}
                            onClick={() => window.location.reload()}
                            sx={{ mt: 1 }}
                        >
                            Reload Application
                        </Button>
                    </Alert>
                </Box>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary; 