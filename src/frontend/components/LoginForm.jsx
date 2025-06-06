import { TradingView, Visibility, VisibilityOff } from '@mui/icons-material';
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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
            const formData = new FormData();
            formData.append('username', credentials.username);
            formData.append('password', credentials.password);

            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Store token
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user_info', JSON.stringify(data.user_info));

                // Call parent callback
                onLogin(data);
            } else {
                setError(data.detail || 'Login failed');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleDemoLogin = (role) => {
        const demoCredentials = {
            trader: { username: 'trader', password: 'trader123' },
            admin: { username: 'admin', password: 'admin123' },
            analyst: { username: 'analyst', password: 'analyst123' }
        };

        setCredentials(demoCredentials[role]);
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
                            <TradingView sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
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

                        <Box sx={{ mt: 3 }}>
                            <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 1 }}>
                                Demo Accounts:
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                <Button
                                    size="small"
                                    onClick={() => handleDemoLogin('trader')}
                                    disabled={loading}
                                >
                                    Trader
                                </Button>
                                <Button
                                    size="small"
                                    onClick={() => handleDemoLogin('admin')}
                                    disabled={loading}
                                >
                                    Admin
                                </Button>
                                <Button
                                    size="small"
                                    onClick={() => handleDemoLogin('analyst')}
                                    disabled={loading}
                                >
                                    Analyst
                                </Button>
                            </Box>
                        </Box>
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
};

export default LoginForm; 