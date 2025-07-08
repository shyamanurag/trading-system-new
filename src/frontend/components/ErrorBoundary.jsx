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
            const isObjectRenderingError = this.state.error?.message?.includes('Objects are not valid as a React child');

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

                        {isObjectRenderingError && (
                            <Alert severity="warning" sx={{ mb: 2, textAlign: 'left' }}>
                                <Typography variant="subtitle2" gutterBottom>
                                    🔧 React Error #31 Detected
                                </Typography>
                                <Typography variant="body2">
                                    This error occurs when trying to display an object directly in React.
                                    Likely cause: TrueData status information being rendered incorrectly.
                                    <br />
                                    <strong>Quick Fix:</strong> Try the "Retry Component" button below.
                                </Typography>
                            </Alert>
                        )}

                        {this.state.error && (
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', display: 'block', mb: 2 }}>
                                Error: {this.state.error.message}
                            </Typography>
                        )}

                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                            <Button
                                variant="outlined"
                                startIcon={<Refresh />}
                                onClick={() => {
                                    this.setState({ hasError: false, error: null, errorInfo: null });
                                }}
                                sx={{ mt: 1 }}
                            >
                                Retry Component
                            </Button>
                            <Button
                                variant="contained"
                                startIcon={<Refresh />}
                                onClick={() => window.location.reload()}
                                sx={{ mt: 1 }}
                            >
                                Reload Application
                            </Button>
                        </Box>
                    </Alert>
                </Box>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary; 