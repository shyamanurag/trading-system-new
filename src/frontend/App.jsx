import {
    CssBaseline
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import React, { useEffect, useState } from 'react';

// Import components
import { API_ENDPOINTS } from './api/config';
import ComprehensiveTradingDashboard from './components/ComprehensiveTradingDashboard';
import LoginForm from './components/LoginForm';

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
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
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
        MuiTab: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    fontWeight: 600,
                },
            },
        },
    },
});

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userInfo, setUserInfo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing authentication
        const validateToken = async () => {
            const token = localStorage.getItem('access_token');
            const storedUserInfo = localStorage.getItem('user_info');

            if (token && storedUserInfo) {
                try {
                    // Validate token by calling the me endpoint
                    const response = await fetch(API_ENDPOINTS.ME.url, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Accept': 'application/json'
                        }
                    });

                    if (response.ok) {
                        const userData = await response.json();
                        setUserInfo(JSON.parse(storedUserInfo));
                        setIsAuthenticated(true);
                    } else {
                        // Token is invalid, clear storage
                        console.log('Token validation failed, clearing auth data');
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('user_info');
                        setIsAuthenticated(false);
                    }
                } catch (e) {
                    console.error('Error validating token:', e);
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('user_info');
                    setIsAuthenticated(false);
                }
            }
            setLoading(false);
        };

        validateToken();
    }, []);

    const handleLogin = (loginData) => {
        setUserInfo(loginData.user_info);
        setIsAuthenticated(true);
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        setUserInfo(null);
        setIsAuthenticated(false);
    };

    if (loading) {
        return (
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100vh',
                    fontSize: '1.2rem',
                    color: '#666'
                }}>
                    Validating authentication...
                </div>
            </ThemeProvider>
        );
    }

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {isAuthenticated ? (
                <ComprehensiveTradingDashboard
                    userInfo={userInfo}
                    onLogout={handleLogout}
                />
            ) : (
                <LoginForm onLogin={handleLogin} />
            )}
        </ThemeProvider>
    );
}

export default App; 