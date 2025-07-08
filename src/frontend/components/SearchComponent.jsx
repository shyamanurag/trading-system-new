import {
    Clear as ClearIcon,
    Close as CloseIcon,
    FilterList as FilterIcon,
    Person as PersonIcon,
    Psychology as PsychologyIcon,
    Search as SearchIcon,
    ShowChart as ShowChartIcon,
    Star as StarIcon,
    TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import {
    Avatar,
    Box,
    Button,
    Chip,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    Grid,
    IconButton,
    InputAdornment,
    InputLabel,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    MenuItem,
    Paper,
    Select,
    Tab,
    Tabs,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import React, { useEffect, useRef, useState } from 'react';
import fetchWithAuth from '../api/fetchWithAuth';
import { useDebounce } from '../hooks/useDebounce';

const SearchComponent = ({
    onResultSelect,
    fullScreen = false,
    placeholder = "Search symbols, trades, strategies...",
    showFilters = true,
    showCategories = true,
    autoFocus = false
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedQuery] = useDebounce(searchQuery, 300);
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState({
        symbols: [],
        trades: [],
        strategies: [],
        recommendations: [],
        users: []
    });
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [filters, setFilters] = useState({
        exchange: '',
        status: '',
        dateRange: '',
        strategy: '',
        user: ''
    });
    const [showFilters, setShowFiltersDialog] = useState(false);
    const [selectedTab, setSelectedTab] = useState(0);
    const [showResults, setShowResults] = useState(false);
    const [recentSearches, setRecentSearches] = useState([]);
    const [popularSearches, setPopularSearches] = useState([]);

    const searchInputRef = useRef(null);
    const resultsRef = useRef(null);

    // Category icons mapping
    const categoryIcons = {
        symbol: <ShowChartIcon />,
        trade: <TrendingUpIcon />,
        strategy: <PsychologyIcon />,
        recommendation: <StarIcon />,
        user: <PersonIcon />,
        all: <SearchIcon />
    };

    // Category colors
    const categoryColors = {
        symbol: '#1976d2',
        trade: '#388e3c',
        strategy: '#f57c00',
        recommendation: '#7b1fa2',
        user: '#d32f2f',
        all: '#424242'
    };

    useEffect(() => {
        if (autoFocus && searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, [autoFocus]);

    useEffect(() => {
        if (debouncedQuery.length >= 2) {
            performSearch();
        } else {
            clearResults();
        }
    }, [debouncedQuery, selectedCategory, filters]);

    useEffect(() => {
        if (searchQuery.length >= 1) {
            fetchSuggestions();
        } else {
            setSuggestions([]);
            setShowSuggestions(false);
        }
    }, [searchQuery]);

    useEffect(() => {
        loadRecentSearches();
        loadPopularSearches();
    }, []);

    const performSearch = async () => {
        if (!debouncedQuery.trim()) return;

        setIsSearching(true);
        setShowResults(true);

        try {
            if (selectedCategory === 'all') {
                // Global search
                const response = await fetchWithAuth(`/api/v1/search/global?query=${encodeURIComponent(debouncedQuery)}&limit=50`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        setSearchResults(data.data);
                    }
                }
            } else {
                // Category-specific search
                const endpoint = getSearchEndpoint(selectedCategory);
                const params = new URLSearchParams({
                    query: debouncedQuery,
                    limit: '50',
                    ...buildFilterParams()
                });

                const response = await fetchWithAuth(`${endpoint}?${params}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        setSearchResults(prev => ({
                            ...prev,
                            [selectedCategory]: data.data
                        }));
                    }
                }
            }

            // Save to recent searches
            saveRecentSearch(debouncedQuery);

        } catch (error) {
            console.error('Search error:', error);
        } finally {
            setIsSearching(false);
        }
    };

    const fetchSuggestions = async () => {
        if (!searchQuery.trim()) return;

        try {
            const response = await fetchWithAuth(`/api/v1/search/autocomplete?query=${encodeURIComponent(searchQuery)}&category=${selectedCategory}&limit=10`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    setSuggestions(data.suggestions);
                    setShowSuggestions(true);
                }
            }
        } catch (error) {
            console.error('Suggestions error:', error);
        }
    };

    const getSearchEndpoint = (category) => {
        const endpoints = {
            symbols: '/api/v1/search/symbols',
            trades: '/api/v1/search/trades',
            strategies: '/api/v1/search/strategies',
            recommendations: '/api/v1/search/recommendations',
            users: '/api/v1/search/users'
        };
        return endpoints[category] || '/api/v1/search/global';
    };

    const buildFilterParams = () => {
        const params = {};
        Object.entries(filters).forEach(([key, value]) => {
            if (value) {
                params[key] = value;
            }
        });
        return params;
    };

    const clearResults = () => {
        setSearchResults({
            symbols: [],
            trades: [],
            strategies: [],
            recommendations: [],
            users: []
        });
        setShowResults(false);
        setSuggestions([]);
        setShowSuggestions(false);
    };

    const handleSearchChange = (event) => {
        const value = event.target.value;
        setSearchQuery(value);

        if (!value) {
            clearResults();
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setSearchQuery(suggestion.value);
        setShowSuggestions(false);

        if (onResultSelect) {
            onResultSelect(suggestion);
        }
    };

    const handleResultClick = (result) => {
        if (onResultSelect) {
            onResultSelect(result);
        }
    };

    const handleClearSearch = () => {
        setSearchQuery('');
        clearResults();
        if (searchInputRef.current) {
            searchInputRef.current.focus();
        }
    };

    const loadRecentSearches = () => {
        const recent = JSON.parse(localStorage.getItem('recentSearches') || '[]');
        setRecentSearches(recent.slice(0, 5));
    };

    const loadPopularSearches = () => {
        // Mock popular searches - in real app, this would come from API
        setPopularSearches([
            'NIFTY',
            'BANKNIFTY',
            'RELIANCE',
            'TCS',
            'HDFC',
            'Momentum Strategy',
            'Scalping',
            'Elite Recommendations'
        ]);
    };

    const saveRecentSearch = (query) => {
        const recent = JSON.parse(localStorage.getItem('recentSearches') || '[]');
        const updated = [query, ...recent.filter(q => q !== query)].slice(0, 10);
        localStorage.setItem('recentSearches', JSON.stringify(updated));
        setRecentSearches(updated.slice(0, 5));
    };

    const formatResultTitle = (result) => {
        switch (result.category) {
            case 'symbol':
                return `${result.symbol} - ${result.name || 'Stock'}`;
            case 'trade':
                return `${result.symbol} ${result.side} ${result.quantity}`;
            case 'strategy':
                return result.name;
            case 'recommendation':
                return `${result.symbol} - ${result.type}`;
            case 'user':
                return result.username;
            default:
                return result.title || result.name || result.symbol || 'Unknown';
        }
    };

    const formatResultSubtitle = (result) => {
        switch (result.category) {
            case 'symbol':
                return `${result.exchange} | ${result.type}`;
            case 'trade':
                return `${result.strategy} | PnL: ₹${result.pnl}`;
            case 'strategy':
                return result.description || 'Trading Strategy';
            case 'recommendation':
                return `Entry: ₹${result.entry_price} | Status: ${result.status}`;
            case 'user':
                return `Balance: ₹${result.current_balance}`;
            default:
                return result.subtitle || result.description || '';
        }
    };

    const getResultsCount = () => {
        return Object.values(searchResults).reduce((total, arr) => total + arr.length, 0);
    };

    const renderSuggestions = () => {
        if (!showSuggestions || suggestions.length === 0) return null;

        return (
            <Paper
                elevation={3}
                sx={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    zIndex: 1300,
                    maxHeight: '300px',
                    overflowY: 'auto'
                }}
            >
                <List dense>
                    {suggestions.map((suggestion, index) => (
                        <ListItem
                            key={index}
                            button
                            onClick={() => handleSuggestionClick(suggestion)}
                            sx={{
                                '&:hover': {
                                    backgroundColor: 'action.hover'
                                }
                            }}
                        >
                            <ListItemIcon>
                                <Avatar
                                    sx={{
                                        width: 24,
                                        height: 24,
                                        bgcolor: categoryColors[suggestion.type] || '#424242',
                                        fontSize: '0.75rem'
                                    }}
                                >
                                    {categoryIcons[suggestion.type]}
                                </Avatar>
                            </ListItemIcon>
                            <ListItemText
                                primary={suggestion.label}
                                secondary={suggestion.type}
                            />
                        </ListItem>
                    ))}
                </List>
            </Paper>
        );
    };

    const renderSearchResults = () => {
        if (!showResults || getResultsCount() === 0) return null;

        return (
            <Paper
                elevation={3}
                sx={{
                    mt: 1,
                    p: 2,
                    maxHeight: fullScreen ? '70vh' : '400px',
                    overflowY: 'auto'
                }}
                ref={resultsRef}
            >
                <Typography variant="h6" gutterBottom>
                    Search Results ({getResultsCount()})
                </Typography>

                {showCategories && (
                    <Tabs
                        value={selectedTab}
                        onChange={(e, newValue) => setSelectedTab(newValue)}
                        variant="scrollable"
                        scrollButtons="auto"
                        sx={{ mb: 2 }}
                    >
                        <Tab label={`All (${getResultsCount()})`} />
                        <Tab label={`Symbols (${searchResults.symbols.length})`} />
                        <Tab label={`Trades (${searchResults.trades.length})`} />
                        <Tab label={`Strategies (${searchResults.strategies.length})`} />
                        <Tab label={`Recommendations (${searchResults.recommendations.length})`} />
                        {searchResults.users.length > 0 && (
                            <Tab label={`Users (${searchResults.users.length})`} />
                        )}
                    </Tabs>
                )}

                {selectedTab === 0 && renderAllResults()}
                {selectedTab === 1 && renderCategoryResults('symbols')}
                {selectedTab === 2 && renderCategoryResults('trades')}
                {selectedTab === 3 && renderCategoryResults('strategies')}
                {selectedTab === 4 && renderCategoryResults('recommendations')}
                {selectedTab === 5 && renderCategoryResults('users')}
            </Paper>
        );
    };

    const renderAllResults = () => {
        const allResults = [];

        Object.entries(searchResults).forEach(([category, results]) => {
            results.forEach(result => {
                allResults.push({ ...result, category });
            });
        });

        return (
            <List>
                {allResults.map((result, index) => (
                    <ListItem
                        key={index}
                        button
                        onClick={() => handleResultClick(result)}
                        sx={{
                            mb: 1,
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            '&:hover': {
                                backgroundColor: 'action.hover'
                            }
                        }}
                    >
                        <ListItemIcon>
                            <Avatar
                                sx={{
                                    bgcolor: categoryColors[result.category] || '#424242',
                                    width: 32,
                                    height: 32
                                }}
                            >
                                {categoryIcons[result.category]}
                            </Avatar>
                        </ListItemIcon>
                        <ListItemText
                            primary={formatResultTitle(result)}
                            secondary={formatResultSubtitle(result)}
                        />
                        <Chip
                            label={result.category}
                            size="small"
                            sx={{
                                bgcolor: categoryColors[result.category],
                                color: 'white'
                            }}
                        />
                    </ListItem>
                ))}
            </List>
        );
    };

    const renderCategoryResults = (category) => {
        const results = searchResults[category] || [];

        if (results.length === 0) {
            return (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                        No {category} found for "{debouncedQuery}"
                    </Typography>
                </Box>
            );
        }

        return (
            <List>
                {results.map((result, index) => (
                    <ListItem
                        key={index}
                        button
                        onClick={() => handleResultClick(result)}
                        sx={{
                            mb: 1,
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            '&:hover': {
                                backgroundColor: 'action.hover'
                            }
                        }}
                    >
                        <ListItemIcon>
                            <Avatar
                                sx={{
                                    bgcolor: categoryColors[category] || '#424242',
                                    width: 32,
                                    height: 32
                                }}
                            >
                                {categoryIcons[category]}
                            </Avatar>
                        </ListItemIcon>
                        <ListItemText
                            primary={formatResultTitle({ ...result, category })}
                            secondary={formatResultSubtitle({ ...result, category })}
                        />
                    </ListItem>
                ))}
            </List>
        );
    };

    const renderQuickSearches = () => {
        if (searchQuery) return null;

        return (
            <Paper elevation={1} sx={{ mt: 1, p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                    Quick Searches
                </Typography>

                {recentSearches.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Recent
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {recentSearches.map((search, index) => (
                                <Chip
                                    key={index}
                                    label={search}
                                    size="small"
                                    onClick={() => setSearchQuery(search)}
                                    sx={{ mb: 0.5 }}
                                />
                            ))}
                        </Box>
                    </Box>
                )}

                <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        Popular
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {popularSearches.map((search, index) => (
                            <Chip
                                key={index}
                                label={search}
                                size="small"
                                variant="outlined"
                                onClick={() => setSearchQuery(search)}
                                sx={{ mb: 0.5 }}
                            />
                        ))}
                    </Box>
                </Box>
            </Paper>
        );
    };

    const renderFilters = () => {
        return (
            <Dialog
                open={showFilters}
                onClose={() => setShowFiltersDialog(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    Search Filters
                    <IconButton
                        onClick={() => setShowFiltersDialog(false)}
                        sx={{ position: 'absolute', right: 8, top: 8 }}
                    >
                        <CloseIcon />
                    </IconButton>
                </DialogTitle>
                <DialogContent>
                    <Grid container spacing={3} sx={{ mt: 1 }}>
                        <Grid item xs={12} md={6}>
                            <FormControl fullWidth>
                                <InputLabel>Exchange</InputLabel>
                                <Select
                                    value={filters.exchange}
                                    onChange={(e) => setFilters(prev => ({ ...prev, exchange: e.target.value }))}
                                >
                                    <MenuItem value="">All Exchanges</MenuItem>
                                    <MenuItem value="NSE">NSE</MenuItem>
                                    <MenuItem value="BSE">BSE</MenuItem>
                                    <MenuItem value="MCX">MCX</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <FormControl fullWidth>
                                <InputLabel>Status</InputLabel>
                                <Select
                                    value={filters.status}
                                    onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                                >
                                    <MenuItem value="">All Statuses</MenuItem>
                                    <MenuItem value="ACTIVE">Active</MenuItem>
                                    <MenuItem value="COMPLETED">Completed</MenuItem>
                                    <MenuItem value="PENDING">Pending</MenuItem>
                                    <MenuItem value="CANCELLED">Cancelled</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <FormControl fullWidth>
                                <InputLabel>Date Range</InputLabel>
                                <Select
                                    value={filters.dateRange}
                                    onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                                >
                                    <MenuItem value="">All Time</MenuItem>
                                    <MenuItem value="today">Today</MenuItem>
                                    <MenuItem value="week">This Week</MenuItem>
                                    <MenuItem value="month">This Month</MenuItem>
                                    <MenuItem value="quarter">This Quarter</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Strategy"
                                value={filters.strategy}
                                onChange={(e) => setFilters(prev => ({ ...prev, strategy: e.target.value }))}
                                placeholder="Filter by strategy name"
                            />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setFilters({ exchange: '', status: '', dateRange: '', strategy: '', user: '' })}>
                        Clear All
                    </Button>
                    <Button onClick={() => setShowFiltersDialog(false)}>
                        Apply Filters
                    </Button>
                </DialogActions>
            </Dialog>
        );
    };

    return (
        <Box sx={{ position: 'relative', width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                    ref={searchInputRef}
                    fullWidth
                    placeholder={placeholder}
                    value={searchQuery}
                    onChange={handleSearchChange}
                    onFocus={() => {
                        if (!searchQuery) {
                            setShowSuggestions(false);
                        }
                    }}
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                {isSearching ? (
                                    <CircularProgress size={20} />
                                ) : (
                                    <SearchIcon />
                                )}
                            </InputAdornment>
                        ),
                        endAdornment: searchQuery && (
                            <InputAdornment position="end">
                                <IconButton onClick={handleClearSearch} size="small">
                                    <ClearIcon />
                                </IconButton>
                            </InputAdornment>
                        )
                    }}
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            borderRadius: 2
                        }
                    }}
                />

                {showFilters && (
                    <Tooltip title="Filters">
                        <IconButton onClick={() => setShowFiltersDialog(true)}>
                            <FilterIcon />
                        </IconButton>
                    </Tooltip>
                )}
            </Box>

            {showCategories && (
                <Box sx={{ mt: 1 }}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Category</InputLabel>
                        <Select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                        >
                            <MenuItem value="all">All</MenuItem>
                            <MenuItem value="symbols">Symbols</MenuItem>
                            <MenuItem value="trades">Trades</MenuItem>
                            <MenuItem value="strategies">Strategies</MenuItem>
                            <MenuItem value="recommendations">Recommendations</MenuItem>
                            <MenuItem value="users">Users</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
            )}

            {renderSuggestions()}
            {renderSearchResults()}
            {renderQuickSearches()}
            {renderFilters()}
        </Box>
    );
};

export default SearchComponent; 