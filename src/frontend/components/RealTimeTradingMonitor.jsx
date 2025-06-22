import { format } from 'date-fns';
import {
    Activity,
    AlertCircle,
    AlertTriangle,
    BarChart2,
    CheckCircle,
    Pause,
    Radio,
    Shield,
    TrendingDown,
    TrendingUp,
    Users,
    XCircle,
    Zap
} from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import { Line } from 'react-chartjs-2';
import api from '../api/api';
import useWebSocket from '../hooks/useWebSocket';

const RealTimeTradingMonitor = () => {
    // State Management
    const [systemStatus, setSystemStatus] = useState({
        is_active: false,
        market_open: false,
        connections: {},
        active_positions: [],
        active_strategies: [],
        risk_status: {},
        market_outlook: 'NEUTRAL'
    });

    const [liveData, setLiveData] = useState({
        spot_price: 0,
        vix: 0,
        volume: 0,
        bid_ask_spread: 0
    });

    const [recentTrades, setRecentTrades] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [performanceMetrics, setPerformanceMetrics] = useState({
        daily_pnl: 0,
        total_trades: 0,
        win_rate: 0,
        active_positions: 0
    });

    // Chart data
    const [pnlHistory, setPnlHistory] = useState([]);
    const chartRef = useRef(null);

    // WebSocket connection
    const { isConnected, sendMessage, lastMessage } = useWebSocket(
        process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws'
    );

    // Fetch initial data
    useEffect(() => {
        fetchSystemStatus();
        fetchPerformanceMetrics();
        const interval = setInterval(() => {
            fetchSystemStatus();
            fetchPerformanceMetrics();
        }, 5000); // Update every 5 seconds

        return () => clearInterval(interval);
    }, []);

    // Handle WebSocket messages
    useEffect(() => {
        if (lastMessage) {
            handleWebSocketMessage(lastMessage);
        }
    }, [lastMessage]);

    const fetchSystemStatus = async () => {
        try {
            const response = await api.get('/api/system/status');
            setSystemStatus(response.data);
        } catch (error) {
            console.error('Error fetching system status:', error);
        }
    };

    const fetchPerformanceMetrics = async () => {
        try {
            const response = await api.get('/api/performance/today');
            setPerformanceMetrics(response.data);
        } catch (error) {
            console.error('Error fetching performance metrics:', error);
        }
    };

    const handleWebSocketMessage = (message) => {
        const data = JSON.parse(message);

        switch (data.type) {
            case 'market_data':
                setLiveData(prev => ({ ...prev, ...data.payload }));
                break;

            case 'trade_executed':
                setRecentTrades(prev => [data.payload, ...prev].slice(0, 20));
                break;

            case 'alert':
                setAlerts(prev => [data.payload, ...prev].slice(0, 10));
                break;

            case 'pnl_update':
                setPnlHistory(prev => [...prev, {
                    time: new Date(),
                    value: data.payload.cumulative_pnl
                }].slice(-50));
                setPerformanceMetrics(prev => ({
                    ...prev,
                    daily_pnl: data.payload.cumulative_pnl
                }));
                break;

            case 'position_update':
                setSystemStatus(prev => ({
                    ...prev,
                    active_positions: data.payload.positions
                }));
                break;
        }
    };

    const toggleTrading = async () => {
        try {
            const endpoint = systemStatus.is_active ? '/api/trading/disable' : '/api/trading/enable';
            await api.post(endpoint);
            await fetchSystemStatus();
        } catch (error) {
            console.error('Error toggling trading:', error);
        }
    };

    // Chart configuration
    const pnlChartData = {
        labels: pnlHistory.map(p => format(p.time, 'HH:mm:ss')),
        datasets: [{
            label: 'P&L',
            data: pnlHistory.map(p => p.value),
            borderColor: pnlHistory.length > 0 && pnlHistory[pnlHistory.length - 1].value >= 0
                ? 'rgb(34, 197, 94)'
                : 'rgb(239, 68, 68)',
            backgroundColor: pnlHistory.length > 0 && pnlHistory[pnlHistory.length - 1].value >= 0
                ? 'rgba(34, 197, 94, 0.1)'
                : 'rgba(239, 68, 68, 0.1)',
            tension: 0.1,
            fill: true
        }]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { display: false },
            y: {
                grid: { color: 'rgba(0, 0, 0, 0.05)' }
            }
        }
    };

    // Components
    const StatusIndicator = ({ status, label }) => {
        const getStatusColor = () => {
            switch (status) {
                case 'connected':
                case 'active':
                case true:
                    return 'bg-green-500';
                case 'disconnected':
                case 'inactive':
                case false:
                    return 'bg-red-500';
                case 'connecting':
                case 'pending':
                    return 'bg-yellow-500';
                default:
                    return 'bg-gray-500';
            }
        };

        return (
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`} />
                <span className="text-sm text-gray-600">{label}</span>
            </div>
        );
    };

    const MetricCard = ({ title, value, icon, trend, color = 'blue' }) => {
        const trendIcon = trend > 0 ? <TrendingUp className="w-4 h-4" /> :
            trend < 0 ? <TrendingDown className="w-4 h-4" /> : null;

        const valueColor = trend > 0 ? 'text-green-600' :
            trend < 0 ? 'text-red-600' : 'text-gray-900';

        return (
            <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">{title}</span>
                    <div className={`p-2 rounded bg-${color}-100`}>
                        {React.cloneElement(icon, { className: `w-4 h-4 text-${color}-600` })}
                    </div>
                </div>
                <div className="flex items-end justify-between">
                    <span className={`text-2xl font-bold ${valueColor}`}>{value}</span>
                    {trendIcon && (
                        <div className={trend > 0 ? 'text-green-500' : 'text-red-500'}>
                            {trendIcon}
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const TradeRow = ({ trade }) => {
        const isProfitable = trade.pnl > 0;

        return (
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded ${isProfitable ? 'bg-green-100' : 'bg-red-100'}`}>
                        {isProfitable ?
                            <TrendingUp className="w-4 h-4 text-green-600" /> :
                            <TrendingDown className="w-4 h-4 text-red-600" />
                        }
                    </div>
                    <div>
                        <div className="font-medium text-sm">{trade.symbol}</div>
                        <div className="text-xs text-gray-500">{trade.strategy}</div>
                    </div>
                </div>
                <div className="text-right">
                    <div className={`font-medium text-sm ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                        {isProfitable ? '+' : ''}₹{Math.abs(trade.pnl).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500">
                        {format(new Date(trade.timestamp), 'HH:mm:ss')}
                    </div>
                </div>
            </div>
        );
    };

    const AlertItem = ({ alert }) => {
        const getAlertIcon = () => {
            switch (alert.severity) {
                case 'critical':
                    return <XCircle className="w-5 h-5 text-red-500" />;
                case 'warning':
                    return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
                case 'info':
                    return <AlertCircle className="w-5 h-5 text-blue-500" />;
                default:
                    return <CheckCircle className="w-5 h-5 text-green-500" />;
            }
        };

        return (
            <div className={`flex items-start gap-3 p-3 rounded-lg border ${alert.severity === 'critical' ? 'bg-red-50 border-red-200' :
                    alert.severity === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                        'bg-blue-50 border-blue-200'
                }`}>
                {getAlertIcon()}
                <div className="flex-1">
                    <div className="font-medium text-sm">{alert.title}</div>
                    <div className="text-xs text-gray-600 mt-1">{alert.message}</div>
                    <div className="text-xs text-gray-500 mt-1">
                        {format(new Date(alert.timestamp), 'HH:mm:ss')}
                    </div>
                </div>
            </div>
        );
    };

    const PositionCard = ({ position }) => {
        const pnlPercent = ((position.current_price - position.entry_price) / position.entry_price * 100).toFixed(2);
        const isProfitable = position.unrealized_pnl > 0;

        return (
            <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex justify-between items-start mb-3">
                    <div>
                        <h4 className="font-semibold">{position.symbol}</h4>
                        <p className="text-sm text-gray-500">{position.strategy}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${position.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                        {position.side}
                    </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                        <span className="text-gray-500">Entry</span>
                        <p className="font-medium">₹{position.entry_price}</p>
                    </div>
                    <div>
                        <span className="text-gray-500">Current</span>
                        <p className="font-medium">₹{position.current_price}</p>
                    </div>
                    <div>
                        <span className="text-gray-500">Quantity</span>
                        <p className="font-medium">{position.quantity}</p>
                    </div>
                    <div>
                        <span className="text-gray-500">P&L</span>
                        <p className={`font-medium ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                            {isProfitable ? '+' : ''}₹{position.unrealized_pnl.toLocaleString()}
                            <span className="text-xs ml-1">({pnlPercent}%)</span>
                        </p>
                    </div>
                </div>

                {/* Progress bar for stop loss / target */}
                <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>SL: ₹{position.stop_loss}</span>
                        <span>Target: ₹{position.target}</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all ${isProfitable ? 'bg-green-500' : 'bg-red-500'}`}
                            style={{
                                width: `${Math.min(100, Math.max(0,
                                    ((position.current_price - position.stop_loss) /
                                        (position.target - position.stop_loss) * 100)
                                ))}%`
                            }}
                        />
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center gap-4">
                            <h1 className="text-xl font-bold text-gray-900">Real-Time Trading Monitor</h1>
                            <div className="flex items-center gap-3">
                                <StatusIndicator
                                    status={systemStatus.market_open}
                                    label={systemStatus.market_open ? 'Market Open' : 'Market Closed'}
                                />
                                <StatusIndicator
                                    status={isConnected}
                                    label={isConnected ? 'Live Data' : 'Disconnected'}
                                />
                            </div>
                        </div>

                        <button
                            onClick={toggleTrading}
                            className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${systemStatus.is_active
                                    ? 'bg-red-600 text-white hover:bg-red-700'
                                    : 'bg-green-600 text-white hover:bg-green-700'
                                }`}
                        >
                            {systemStatus.is_active ? (
                                <>
                                    <Pause className="w-4 h-4" />
                                    Stop Trading
                                </>
                            ) : (
                                <>
                                    <Zap className="w-4 h-4" />
                                    Start Trading
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <MetricCard
                        title="Daily P&L"
                        value={`₹${performanceMetrics.daily_pnl.toLocaleString()}`}
                        icon={<TrendingUp />}
                        trend={performanceMetrics.daily_pnl}
                    />
                    <MetricCard
                        title="Total Trades"
                        value={performanceMetrics.total_trades}
                        icon={<Activity />}
                        color="purple"
                    />
                    <MetricCard
                        title="Win Rate"
                        value={`${performanceMetrics.win_rate.toFixed(1)}%`}
                        icon={<BarChart2 />}
                        trend={performanceMetrics.win_rate - 50}
                        color="green"
                    />
                    <MetricCard
                        title="Active Positions"
                        value={performanceMetrics.active_positions}
                        icon={<Users />}
                        color="orange"
                    />
                </div>

                {/* Market Data Bar */}
                <div className="bg-white rounded-lg shadow p-4 mb-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <span className="text-sm text-gray-500">Spot Price</span>
                            <p className="text-lg font-semibold">₹{liveData.spot_price.toLocaleString()}</p>
                        </div>
                        <div>
                            <span className="text-sm text-gray-500">VIX</span>
                            <p className="text-lg font-semibold">{liveData.vix.toFixed(2)}</p>
                        </div>
                        <div>
                            <span className="text-sm text-gray-500">Volume</span>
                            <p className="text-lg font-semibold">{(liveData.volume / 1000000).toFixed(1)}M</p>
                        </div>
                        <div>
                            <span className="text-sm text-gray-500">Bid-Ask Spread</span>
                            <p className="text-lg font-semibold">{liveData.bid_ask_spread.toFixed(2)}</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* P&L Chart */}
                    <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-4">Live P&L</h3>
                        <div className="h-64">
                            <Line data={pnlChartData} options={chartOptions} />
                        </div>
                    </div>

                    {/* Alerts */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">System Alerts</h3>
                            <Radio className="w-5 h-5 text-blue-500 animate-pulse" />
                        </div>
                        <div className="space-y-3 max-h-64 overflow-y-auto">
                            {alerts.length > 0 ? (
                                alerts.map((alert, idx) => (
                                    <AlertItem key={idx} alert={alert} />
                                ))
                            ) : (
                                <p className="text-gray-500 text-center py-8">No alerts</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Active Positions */}
                <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-4">Active Positions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {systemStatus.active_positions.length > 0 ? (
                            systemStatus.active_positions.map((position, idx) => (
                                <PositionCard key={idx} position={position} />
                            ))
                        ) : (
                            <div className="col-span-full bg-white rounded-lg shadow p-8 text-center text-gray-500">
                                No active positions
                            </div>
                        )}
                    </div>
                </div>

                {/* Recent Trades */}
                <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-4">Recent Trades</h3>
                        <div className="space-y-3 max-h-96 overflow-y-auto">
                            {recentTrades.length > 0 ? (
                                recentTrades.map((trade, idx) => (
                                    <TradeRow key={idx} trade={trade} />
                                ))
                            ) : (
                                <p className="text-gray-500 text-center py-8">No recent trades</p>
                            )}
                        </div>
                    </div>

                    {/* Strategy Status */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-4">Active Strategies</h3>
                        <div className="space-y-3">
                            {systemStatus.active_strategies.map((strategy, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                    <div className="flex items-center gap-3">
                                        <Shield className="w-5 h-5 text-blue-500" />
                                        <div>
                                            <div className="font-medium">{strategy.name}</div>
                                            <div className="text-sm text-gray-500">
                                                {strategy.trades_today} trades • {strategy.win_rate}% win rate
                                            </div>
                                        </div>
                                    </div>
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${strategy.status === 'active'
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-gray-100 text-gray-800'
                                        }`}>
                                        {strategy.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RealTimeTradingMonitor; 