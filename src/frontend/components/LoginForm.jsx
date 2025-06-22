import { TrendingUp, Visibility, VisibilityOff } from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Container,
    IconButton,
    InputAdornment,
    TextField,
    Typography
} from '@mui/material';
import React, { useState } from 'react';
import { API_ENDPOINTS } from '../api/config';

const LoginForm = ({ onLogin }) => {
    const [credentials, setCredentials] = useState({
        username: '',
        password: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(API_ENDPOINTS.LOGIN.url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Origin': window.location.origin
                },
                credentials: 'include',
                body: JSON.stringify({
                    username: credentials.username,
                    password: credentials.password
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Authentication failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            if (data.access_token) {
                // Store authentication token
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user_info', JSON.stringify(data.user_info));

                // Create user info object with proper structure
                const userInfo = {
                    username: data.user_info.username,
                    name: data.user_info.full_name,
                    role: data.user_info.is_admin ? 'admin' : 'trader',
                    email: data.user_info.email,
                    permissions: data.user_info.is_admin ? ['trade', 'view_analytics'] : ['trade']
                };

                onLogin({ user_info: userInfo });
            } else {
                throw new Error('Invalid response from server: Missing access token');
            }
        } catch (err) {
            console.error('Authentication error:', err);
            setError(err.message || 'Authentication failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <Box sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            }}>
                <Card sx={{ width: '100%', maxWidth: 400 }}>
                    <CardContent sx={{ p: 4 }}>
                        <Box sx={{ textAlign: 'center', mb: 3 }}>
                            <TrendingUp sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                            <Typography variant="h4" component="h1" gutterBottom>
                                Elite Trading System
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Professional Trading Platform
                            </Typography>
                        </Box>

                        {error && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                                {error}
                            </Alert>
                        )}

                        <form onSubmit={handleSubmit}>
                            <TextField
                                fullWidth
                                label="Username"
                                value={credentials.username}
                                onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                                margin="normal"
                                required
                                disabled={loading}
                            />

                            <TextField
                                fullWidth
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                value={credentials.password}
                                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                                margin="normal"
                                required
                                disabled={loading}
                                InputProps={{
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={() => setShowPassword(!showPassword)}
                                                edge="end"
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    )
                                }}
                            />

                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                size="large"
                                disabled={loading}
                                sx={{ mt: 3, mb: 2, py: 1.5 }}
                            >
                                {loading ? 'Signing In...' : 'Sign In'}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
};

export default LoginForm; 