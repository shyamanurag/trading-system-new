import { endOfDay, format, startOfDay, subDays } from 'date-fns';
import {
    Activity,
    BarChart2,
    Calendar,
    DollarSign,
    Download,
    RefreshCw,
    Shield,
    Target,
    Users
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { Bar, Line, Pie } from 'react-chartjs-2';
import api from '../api/api';

const TradingReportsHub = () => {
    // State Management
    const [activeTab, setActiveTab] = useState('daily');
    const [dateRange, setDateRange] = useState({
        start: startOfDay(new Date()),
        end: endOfDay(new Date())
    });
    const [selectedUser, setSelectedUser] = useState('all');
    const [selectedStrategy, setSelectedStrategy] = useState('all');
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [users, setUsers] = useState([]);
    const [strategies, setStrategies] = useState([]);

    // Fetch initial data
    useEffect(() => {
        fetchUsers();
        fetchStrategies();
        fetchReportData();
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await api.get('/api/users');
            setUsers(response.data);
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const fetchStrategies = async () => {
        try {
            const response = await api.get('/api/strategies');
            setStrategies(response.data);
        } catch (error) {
            console.error('Error fetching strategies:', error);
        }
    };

    const fetchReportData = async () => {
        setLoading(true);
        try {
            const params = {
                start_date: format(dateRange.start, 'yyyy-MM-dd'),
                end_date: format(dateRange.end, 'yyyy-MM-dd'),
                user_id: selectedUser !== 'all' ? selectedUser : undefined,
                strategy: selectedStrategy !== 'all' ? selectedStrategy : undefined
            };

            const response = await api.get(`/api/reports/${activeTab}`, { params });
            setReportData(response.data);
        } catch (error) {
            console.error('Error fetching report data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Export functionality
    const exportReport = async (format) => {
        try {
            const params = {
                start_date: format(dateRange.start, 'yyyy-MM-dd'),
                end_date: format(dateRange.end, 'yyyy-MM-dd'),
                user_id: selectedUser !== 'all' ? selectedUser : undefined,
                strategy: selectedStrategy !== 'all' ? selectedStrategy : undefined,
                format: format
            };

            const response = await api.get(`/api/reports/export/${activeTab}`, {
                params,
                responseType: 'blob'
            });

            // Download file
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${activeTab}_report_${format(new Date(), 'yyyyMMdd')}.${format}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Error exporting report:', error);
        }
    };

    // Quick date range setters
    const setQuickDateRange = (days) => {
        setDateRange({
            start: startOfDay(subDays(new Date(), days)),
            end: endOfDay(new Date())
        });
    };

    // Report Components
    const DailyReport = ({ data }) => {
        if (!data) return null;

        const pnlChartData = {
            labels: data.hourly_pnl?.map(h => h.hour) || [],
            datasets: [{
                label: 'Cumulative P&L',
                data: data.hourly_pnl?.map(h => h.cumulative_pnl) || [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1
            }]
        };

        const tradesDistribution = {
            labels: Object.keys(data.strategy_breakdown || {}),
            datasets: [{
                data: Object.values(data.strategy_breakdown || {}).map(s => s.count),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)'
                ]
            }]
        };

        return (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Summary Cards */}
                <div className="col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <SummaryCard
                        title="Total P&L"
                        value={`₹${data.total_pnl?.toLocaleString() || 0}`}
                        icon={<DollarSign />}
                        trend={data.total_pnl > 0 ? 'up' : 'down'}
                    />
                    <SummaryCard
                        title="Total Trades"
                        value={data.total_trades || 0}
                        icon={<Activity />}
                    />
                    <SummaryCard
                        title="Win Rate"
                        value={`${data.win_rate?.toFixed(1) || 0}%`}
                        icon={<Target />}
                        trend={data.win_rate > 50 ? 'up' : 'down'}
                    />
                    <SummaryCard
                        title="Risk Score"
                        value={data.risk_score || 'Low'}
                        icon={<Shield />}
                        trend={data.risk_score === 'Low' ? 'up' : 'down'}
                    />
                </div>

                {/* P&L Chart */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Hourly P&L Progression</h3>
                    <Line data={pnlChartData} options={{ responsive: true }} />
                </div>

                {/* Strategy Distribution */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Trades by Strategy</h3>
                    <Pie data={tradesDistribution} options={{ responsive: true }} />
                </div>

                {/* Top Performers */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Top Performing Trades</h3>
                    <div className="space-y-2">
                        {data.top_trades?.map((trade, idx) => (
                            <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                <span className="text-sm">{trade.symbol}</span>
                                <span className="text-sm font-medium text-green-600">
                                    +₹{trade.pnl.toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Metrics */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Risk Metrics</h3>
                    <div className="space-y-3">
                        <MetricRow label="Max Drawdown" value={`${data.max_drawdown?.toFixed(2) || 0}%`} />
                        <MetricRow label="Sharpe Ratio" value={data.sharpe_ratio?.toFixed(2) || 'N/A'} />
                        <MetricRow label="Value at Risk" value={`₹${data.var_95?.toLocaleString() || 0}`} />
                        <MetricRow label="Greeks Exposure" value={data.greeks_exposure || 'Neutral'} />
                    </div>
                </div>
            </div>
        );
    };

    const StrategyReport = ({ data }) => {
        if (!data) return null;

        const performanceData = {
            labels: data.strategies?.map(s => s.name) || [],
            datasets: [
                {
                    label: 'Total P&L',
                    data: data.strategies?.map(s => s.total_pnl) || [],
                    backgroundColor: 'rgba(75, 192, 192, 0.8)'
                },
                {
                    label: 'Win Rate %',
                    data: data.strategies?.map(s => s.win_rate) || [],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)'
                }
            ]
        };

        return (
            <div className="space-y-6">
                {/* Strategy Performance Comparison */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Strategy Performance Comparison</h3>
                    <Bar data={performanceData} options={{ responsive: true }} />
                </div>

                {/* Detailed Strategy Table */}
                <div className="bg-white p-6 rounded-lg shadow overflow-x-auto">
                    <h3 className="text-lg font-semibold mb-4">Strategy Details</h3>
                    <table className="min-w-full">
                        <thead>
                            <tr className="border-b">
                                <th className="text-left py-2">Strategy</th>
                                <th className="text-right py-2">Trades</th>
                                <th className="text-right py-2">Win Rate</th>
                                <th className="text-right py-2">Avg Win</th>
                                <th className="text-right py-2">Avg Loss</th>
                                <th className="text-right py-2">Total P&L</th>
                                <th className="text-right py-2">Sharpe</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.strategies?.map((strategy, idx) => (
                                <tr key={idx} className="border-b hover:bg-gray-50">
                                    <td className="py-2">{strategy.name}</td>
                                    <td className="text-right">{strategy.total_trades}</td>
                                    <td className="text-right">{strategy.win_rate.toFixed(1)}%</td>
                                    <td className="text-right text-green-600">
                                        ₹{strategy.avg_win.toLocaleString()}
                                    </td>
                                    <td className="text-right text-red-600">
                                        ₹{strategy.avg_loss.toLocaleString()}
                                    </td>
                                    <td className="text-right font-medium">
                                        ₹{strategy.total_pnl.toLocaleString()}
                                    </td>
                                    <td className="text-right">{strategy.sharpe_ratio.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    const UserReport = ({ data }) => {
        if (!data) return null;

        const userPnlData = {
            labels: data.users?.map(u => u.name) || [],
            datasets: [{
                label: 'User P&L',
                data: data.users?.map(u => u.total_pnl) || [],
                backgroundColor: data.users?.map(u =>
                    u.total_pnl > 0 ? 'rgba(75, 192, 192, 0.8)' : 'rgba(255, 99, 132, 0.8)'
                )
            }]
        };

        return (
            <div className="space-y-6">
                {/* User P&L Comparison */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">User P&L Comparison</h3>
                    <Bar data={userPnlData} options={{ responsive: true }} />
                </div>

                {/* User Performance Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {data.users?.map((user, idx) => (
                        <UserCard key={idx} user={user} />
                    ))}
                </div>
            </div>
        );
    };

    const RiskReport = ({ data }) => {
        if (!data) return null;

        return (
            <div className="space-y-6">
                {/* Risk Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <RiskCard
                        title="Portfolio VaR (95%)"
                        value={`₹${data.portfolio_var?.toLocaleString() || 0}`}
                        status={data.var_breach ? 'danger' : 'safe'}
                    />
                    <RiskCard
                        title="Greeks Exposure"
                        value={data.greeks_summary || 'Balanced'}
                        status={data.greeks_risk || 'normal'}
                    />
                    <RiskCard
                        title="Compliance Status"
                        value={data.compliance_violations || 0}
                        status={data.compliance_violations > 0 ? 'warning' : 'safe'}
                    />
                </div>

                {/* Risk Heatmap */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Risk Heatmap</h3>
                    <div className="grid grid-cols-5 gap-2">
                        {data.risk_heatmap?.map((cell, idx) => (
                            <div
                                key={idx}
                                className={`p-4 rounded text-center text-white ${cell.level === 'high' ? 'bg-red-500' :
                                        cell.level === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                                    }`}
                            >
                                <div className="text-xs">{cell.category}</div>
                                <div className="font-bold">{cell.score}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Compliance Violations */}
                {data.violations && data.violations.length > 0 && (
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-lg font-semibold mb-4 text-red-600">
                            Compliance Violations
                        </h3>
                        <div className="space-y-2">
                            {data.violations.map((violation, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-red-50 rounded">
                                    <div>
                                        <div className="font-medium">{violation.type}</div>
                                        <div className="text-sm text-gray-600">{violation.description}</div>
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        {format(new Date(violation.timestamp), 'HH:mm:ss')}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // Helper Components
    const SummaryCard = ({ title, value, icon, trend }) => (
        <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-gray-600">{title}</p>
                    <p className="text-2xl font-bold mt-1">{value}</p>
                </div>
                <div className={`p-3 rounded-full ${trend === 'up' ? 'bg-green-100' : trend === 'down' ? 'bg-red-100' : 'bg-gray-100'
                    }`}>
                    {React.cloneElement(icon, {
                        className: `w-6 h-6 ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
                            }`
                    })}
                </div>
            </div>
        </div>
    );

    const MetricRow = ({ label, value }) => (
        <div className="flex justify-between items-center">
            <span className="text-gray-600">{label}</span>
            <span className="font-medium">{value}</span>
        </div>
    );

    const UserCard = ({ user }) => (
        <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold">{user.name}</h4>
                <span className={`px-2 py-1 rounded text-xs ${user.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                    {user.status}
                </span>
            </div>
            <div className="space-y-2 text-sm">
                <MetricRow label="Total P&L" value={`₹${user.total_pnl.toLocaleString()}`} />
                <MetricRow label="Win Rate" value={`${user.win_rate.toFixed(1)}%`} />
                <MetricRow label="Trades" value={user.total_trades} />
                <MetricRow label="Capital" value={`₹${user.current_capital.toLocaleString()}`} />
            </div>
        </div>
    );

    const RiskCard = ({ title, value, status }) => (
        <div className={`bg-white p-6 rounded-lg shadow border-l-4 ${status === 'danger' ? 'border-red-500' :
                status === 'warning' ? 'border-yellow-500' : 'border-green-500'
            }`}>
            <h4 className="text-gray-600 text-sm mb-2">{title}</h4>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Reports Hub</h1>
                    <p className="text-gray-600">Comprehensive trading analytics and reporting</p>
                </div>

                {/* Controls */}
                <div className="bg-white p-4 rounded-lg shadow mb-6">
                    <div className="flex flex-wrap items-center gap-4">
                        {/* Date Range */}
                        <div className="flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-gray-500" />
                            <input
                                type="date"
                                value={format(dateRange.start, 'yyyy-MM-dd')}
                                onChange={(e) => setDateRange(prev => ({
                                    ...prev,
                                    start: new Date(e.target.value)
                                }))}
                                className="px-3 py-2 border rounded"
                            />
                            <span>to</span>
                            <input
                                type="date"
                                value={format(dateRange.end, 'yyyy-MM-dd')}
                                onChange={(e) => setDateRange(prev => ({
                                    ...prev,
                                    end: new Date(e.target.value)
                                }))}
                                className="px-3 py-2 border rounded"
                            />
                        </div>

                        {/* Quick Ranges */}
                        <div className="flex gap-2">
                            <button
                                onClick={() => setQuickDateRange(0)}
                                className="px-3 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
                            >
                                Today
                            </button>
                            <button
                                onClick={() => setQuickDateRange(7)}
                                className="px-3 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
                            >
                                7 Days
                            </button>
                            <button
                                onClick={() => setQuickDateRange(30)}
                                className="px-3 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
                            >
                                30 Days
                            </button>
                        </div>

                        {/* Filters */}
                        <select
                            value={selectedUser}
                            onChange={(e) => setSelectedUser(e.target.value)}
                            className="px-3 py-2 border rounded"
                        >
                            <option value="all">All Users</option>
                            {users.map(user => (
                                <option key={user.id} value={user.id}>{user.name}</option>
                            ))}
                        </select>

                        <select
                            value={selectedStrategy}
                            onChange={(e) => setSelectedStrategy(e.target.value)}
                            className="px-3 py-2 border rounded"
                        >
                            <option value="all">All Strategies</option>
                            {strategies.map(strategy => (
                                <option key={strategy.id} value={strategy.id}>{strategy.name}</option>
                            ))}
                        </select>

                        {/* Actions */}
                        <button
                            onClick={fetchReportData}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Refresh
                        </button>

                        <div className="flex gap-2 ml-auto">
                            <button
                                onClick={() => exportReport('pdf')}
                                className="px-4 py-2 border rounded hover:bg-gray-50 flex items-center gap-2"
                            >
                                <Download className="w-4 h-4" />
                                PDF
                            </button>
                            <button
                                onClick={() => exportReport('excel')}
                                className="px-4 py-2 border rounded hover:bg-gray-50 flex items-center gap-2"
                            >
                                <Download className="w-4 h-4" />
                                Excel
                            </button>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="bg-white rounded-lg shadow mb-6">
                    <div className="border-b">
                        <nav className="flex -mb-px">
                            {[
                                { id: 'daily', label: 'Daily Report', icon: <Calendar /> },
                                { id: 'strategy', label: 'Strategy Analysis', icon: <BarChart2 /> },
                                { id: 'user', label: 'User Performance', icon: <Users /> },
                                { id: 'risk', label: 'Risk Report', icon: <Shield /> }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-6 py-3 border-b-2 font-medium text-sm ${activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700'
                                        }`}
                                >
                                    {React.cloneElement(tab.icon, { className: 'w-4 h-4' })}
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* Content */}
                <div className="min-h-[600px]">
                    {loading ? (
                        <div className="flex items-center justify-center h-64">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        </div>
                    ) : (
                        <>
                            {activeTab === 'daily' && <DailyReport data={reportData} />}
                            {activeTab === 'strategy' && <StrategyReport data={reportData} />}
                            {activeTab === 'user' && <UserReport data={reportData} />}
                            {activeTab === 'risk' && <RiskReport data={reportData} />}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TradingReportsHub; 