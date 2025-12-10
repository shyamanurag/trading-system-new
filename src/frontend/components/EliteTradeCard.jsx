import React, { useState } from 'react';
import './EliteTradeCard.css';

const EliteTradeCard = ({ trade }) => {
    const [expanded, setExpanded] = useState(false);

    // 🔧 FIX: Safe number formatting to prevent crashes on undefined
    const safeNumber = (value, defaultVal = 0) => {
        const num = parseFloat(value);
        return isNaN(num) ? defaultVal : num;
    };
    const formatPrice = (value) => `₹${safeNumber(value, 0).toFixed(2)}`;
    const formatScore = (value) => `${safeNumber(value, 0).toFixed(1)}/10`;
    const formatRatio = (value) => `1:${safeNumber(value, 1).toFixed(1)}`;

    return (
        <div className={`elite-trade-card ${trade.direction.toLowerCase()}`}>
            <div className="card-header">
                <div className="symbol-info">
                    <h2>{trade.symbol}</h2>
                    <span className="direction-badge">{trade.direction}</span>
                </div>
                <div className="timestamp">
                    <div className="generated-time">
                        Generated: {new Date(trade.timestamp).toLocaleString()}
                    </div>
                    <div className={`validity ${new Date() > new Date(trade.valid_until) ? 'expired' : ''}`}>
                        Valid until: {new Date(trade.valid_until).toLocaleString()}
                    </div>
                </div>
            </div>

            <div className="trade-levels">
                <div className="level-group">
                    <label>Entry</label>
                    <span className="price entry">{formatPrice(trade.entry_price)}</span>
                </div>
                <div className="level-group">
                    <label>Stop Loss</label>
                    <span className="price stop-loss">{formatPrice(trade.stop_loss)}</span>
                </div>
                <div className="level-group">
                    <label>Targets</label>
                    <div className="targets">
                        <span className="price target">T1: {formatPrice(trade.primary_target)}</span>
                        <span className="price target">T2: {formatPrice(trade.secondary_target)}</span>
                        <span className="price target">T3: {formatPrice(trade.tertiary_target)}</span>
                    </div>
                </div>
                <div className="level-group">
                    <label>Risk/Reward</label>
                    <span className="risk-reward">
                        {formatRatio(trade.risk_metrics?.risk_reward_ratio)}
                    </span>
                </div>
            </div>

            <div className="confluence-summary">
                <h3>Perfect Confluence Factors ({trade.confluence_factors.length})</h3>
                <div className="factor-pills">
                    {trade.confluence_factors.slice(0, 5).map((factor, idx) => (
                        <span key={idx} className="factor-pill">{factor}</span>
                    ))}
                    {trade.confluence_factors.length > 5 && (
                        <span className="more-factors">
                            +{trade.confluence_factors.length - 5} more
                        </span>
                    )}
                </div>
            </div>

            <div className="entry-conditions">
                <h4>Entry Conditions</h4>
                <ul>
                    {trade.entry_conditions.map((condition, idx) => (
                        <li key={idx}>{condition}</li>
                    ))}
                </ul>
            </div>

            <div className="trade-management">
                <div className="position-sizing">
                    <h4>Position Sizing</h4>
                    <div className="sizing-info">
                        <span>Recommended: {trade.position_sizing.recommended_percent}%</span>
                        <span>Range: {trade.position_sizing.minimum_percent}% - {trade.position_sizing.maximum_percent}%</span>
                    </div>
                </div>

                <div className="scaling-plan">
                    <h4>Scaling Strategy</h4>
                    <div className="scaling-details">
                        <div>Entry: {trade.scaling_plan.entry_allocation.join('/')}%</div>
                        <div>Exit: {trade.scaling_plan.exit_allocation.join('/')}% at T1/T2/T3</div>
                    </div>
                </div>
            </div>

            <button 
                className="expand-button"
                onClick={() => setExpanded(!expanded)}
            >
                {expanded ? 'Show Less' : 'Show Full Analysis'}
            </button>

            {expanded && (
                <div className="expanded-details">
                    <div className="score-breakdown">
                        <h4>Perfect Score Breakdown</h4>
                        <div className="score-grid">
                            <div className="score-item">
                                <label>Technical</label>
                                <span className="score">{formatScore(trade.technical_score)}</span>
                            </div>
                            <div className="score-item">
                                <label>Volume</label>
                                <span className="score">{formatScore(trade.volume_score)}</span>
                            </div>
                            <div className="score-item">
                                <label>Pattern</label>
                                <span className="score">{formatScore(trade.pattern_score)}</span>
                            </div>
                            <div className="score-item">
                                <label>Regime</label>
                                <span className="score">{formatScore(trade.regime_score)}</span>
                            </div>
                            <div className="score-item">
                                <label>Momentum</label>
                                <span className="score">{formatScore(trade.momentum_score)}</span>
                            </div>
                            <div className="score-item">
                                <label>Smart Money</label>
                                <span className="score">{formatScore(trade.smart_money_score)}</span>
                            </div>
                        </div>
                    </div>

                    <div className="key-levels">
                        <h4>Key Price Levels</h4>
                        <table>
                            <tbody>
                                <tr>
                                    <td>Support</td>
                                    <td>{formatPrice(trade.key_levels?.support)}</td>
                                </tr>
                                <tr>
                                    <td>Resistance</td>
                                    <td>{formatPrice(trade.key_levels?.resistance)}</td>
                                </tr>
                                <tr>
                                    <td>Pivot</td>
                                    <td>{formatPrice(trade.key_levels?.pivot)}</td>
                                </tr>
                                <tr>
                                    <td>VWAP</td>
                                    <td>{formatPrice(trade.key_levels?.vwap)}</td>
                                </tr>
                                <tr>
                                    <td>POC</td>
                                    <td>{formatPrice(trade.key_levels?.poc)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div className="invalidation-conditions">
                        <h4>Setup Invalidation</h4>
                        <ul className="warning-list">
                            {trade.invalidation_conditions.map((condition, idx) => (
                                <li key={idx}>{condition}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="trade-summary">
                        <pre>{trade.generate_summary()}</pre>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EliteTradeCard; 