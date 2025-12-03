# 🏦 Institutional-Grade Algorithmic Trading System
## Complete Feature Documentation & Technical Audit

---

## 📊 EXECUTIVE SUMMARY

This is a **production-grade autonomous intraday trading system** built for the Indian equity and F&O markets. It integrates with **Zerodha Kite** for execution and **TrueData** for real-time market data, with **Redis** for caching and state management.

### Key Statistics
| Metric | Value |
|--------|-------|
| Total Python Files | 150+ |
| Lines of Code | ~80,000+ |
| Active Strategies | 4 |
| Mathematical Models | 15+ |
| API Endpoints | 50+ |
| Real-time Data Sources | 2 (Zerodha + TrueData) |

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ REST APIs   │  │ WebSocket   │  │ Dashboard (Frontend)    │  │
│  │ (FastAPI)   │  │ (Real-time) │  │ (React - separate repo) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  TradingOrchestrator                        ││
│  │  • Strategy Coordination  • Signal Processing               ││
│  │  • Position Management    • Risk Enforcement                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      STRATEGY LAYER                              │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │ Momentum      │ │ Options       │ │ Microstructure│          │
│  │ Surfer        │ │ Engine        │ │ Scalper       │          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
│  ┌───────────────┐ ┌───────────────────────────────────┐        │
│  │ Regime        │ │ BaseStrategy (Shared Foundation)  │        │
│  │ Controller    │ │                                   │        │
│  └───────────────┘ └───────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Trade       │  │ Order       │  │ Position                │  │
│  │ Engine      │  │ Manager     │  │ Tracker                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    DATA & BROKER LAYER                           │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │ Zerodha Integration │  │ TrueData Client                 │   │
│  │ • Orders            │  │ • Real-time Quotes              │   │
│  │ • Positions         │  │ • Historical Data               │   │
│  │ • Historical Data   │  │ • Option Chains                 │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTENCE & CACHE LAYER                      │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │ PostgreSQL          │  │ Redis                           │   │
│  │ • Trades            │  │ • Market Data Cache             │   │
│  │ • Positions         │  │ • Signal Deduplication          │   │
│  │ • Performance       │  │ • Session State                 │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 TRADING STRATEGIES

### 1. Momentum Surfer (`momentum_surfer.py`)
**Purpose:** Intraday momentum-based trading on equity and options

| Feature | Implementation |
|---------|---------------|
| Momentum Detection | Multi-timeframe analysis (1D, 5D, 20D) |
| Trend Identification | Hodrick-Prescott Filter + Linear Regression |
| Entry Signals | RSI Divergence, MACD Crossover, Bollinger Breakout |
| Exit Management | Dynamic ATR-based stops, Trailing stops |
| Position Sizing | Risk-adjusted (2% max loss per trade) |

**Mathematical Models Used:**
- RSI with divergence detection
- MACD with crossover and histogram analysis
- Bollinger Bands with squeeze detection
- HP Trend Filter for noise separation
- Cross-Sectional Momentum (relative strength percentile)
- Mean Reversion Probability (Z-score based)

### 2. News Impact Scalper (`news_impact_scalper.py`)
**Purpose:** Options trading on F&O stocks

| Feature | Implementation |
|---------|---------------|
| Instrument Selection | ATM/OTM strike calculation |
| Greeks Analysis | Delta, Gamma, Theta, Vega monitoring |
| Expiry Management | Skip nearest expiry, prefer monthly |
| Signal Generation | Dual-timeframe underlying analysis |

**Options-Specific Models:**
- Black-Scholes pricing (Call/Put)
- Greeks calculation
- Implied Volatility estimation
- Put-Call Parity verification

### 3. Optimized Volume Scalper (`optimized_volume_scalper.py`)
**Purpose:** Market microstructure-based trading

| Feature | Implementation |
|---------|---------------|
| Order Flow Analysis | Buying/Selling pressure detection |
| Liquidity Detection | Bid-Ask spread analysis |
| Mean Reversion | Z-score based opportunities |
| Statistical Arbitrage | Cointegration testing |

**Microstructure Models:**
- GARCH Volatility modeling
- Cointegration Test (Engle-Granger)
- Market Impact Model
- Kelly Criterion position sizing
- VaR Calculation (95% confidence)

### 4. Regime Adaptive Controller (`regime_adaptive_controller.py`)
**Purpose:** Meta-strategy that adjusts other strategies based on market regime

| Feature | Implementation |
|---------|---------------|
| Regime Detection | Hidden Markov Model (4-8 states) |
| State Estimation | Kalman Filter |
| Volatility Regime | GARCH-based classification |
| Allocation | Dynamic strategy weighting |

**ML/Statistical Models:**
- **Hidden Markov Model** (Full implementation):
  - Forward Algorithm
  - Backward Algorithm
  - Viterbi Algorithm
  - Baum-Welch (EM) Algorithm
- **Kalman Filter** for state estimation
- **Gaussian Mixture Model** for clustering
- **Markov Switching** probabilities

---

## 🧮 MATHEMATICAL MODELS (Honest Assessment)

### ✅ FULLY IMPLEMENTED & ACTIVE

| Model | Location | Status |
|-------|----------|--------|
| RSI (14-period) | `base_strategy.py` | ✅ Working |
| MACD (12,26,9) | `base_strategy.py` | ✅ Working |
| Bollinger Bands (20,2) | `base_strategy.py` | ✅ Working |
| ATR (14-period) | `base_strategy.py` | ✅ Working |
| Hodrick-Prescott Filter | `momentum_surfer.py` | ✅ Working |
| Momentum Score | `momentum_surfer.py` | ✅ Working |
| Trend Strength (R²) | `momentum_surfer.py` | ✅ Working |
| Mean Reversion Probability | `momentum_surfer.py` | ✅ Working |
| Cross-Sectional Momentum | `momentum_surfer.py` | ✅ Working |
| Momentum Regime Detection | `momentum_surfer.py` | ✅ Working |
| GARCH Volatility | `regime_adaptive_controller.py` | ✅ Working |
| Kalman Filter | `regime_adaptive_controller.py` | ✅ Working |
| Hidden Markov Model | `regime_adaptive_controller.py` | ✅ Working |
| GMM Regime Detection | `regime_adaptive_controller.py` | ✅ Working |
| Black-Scholes | `news_impact_scalper.py` | ✅ Working |
| Greeks (Δ,Γ,Θ,V,ρ) | `news_impact_scalper.py` | ✅ Working |

### ⚠️ HONEST LIMITATIONS

| Limitation | Impact | Reality |
|------------|--------|---------|
| Backtesting | Medium | Framework exists but not production-tested |
| ML Signal Validation | Low | RandomForest exists but needs training data |
| News Sentiment | None | Not implemented (name is legacy) |
| Cross-Sectional Momentum | Low | Works only when 5+ symbols tracked |
| HMM Training | Medium | Trains every 50 observations, may need tuning |

---

## 🔄 DATA FLOW

### Real-Time Market Data Flow
```
TrueData WebSocket → Redis Cache → Orchestrator → Strategies
         ↓                              ↓
   live_market_data dict          Market Bias Calculation
         ↓                              ↓
   154+ symbols tracked           Direction: BULLISH/BEARISH/NEUTRAL
```

### Signal Generation Flow
```
Strategy.generate_signals()
         ↓
   Signal Deduplicator (Redis-based)
         ↓
   Position Opening Decision
         ↓
   Risk Manager Validation
         ↓
   Order Manager → Zerodha API
         ↓
   Position Tracker (sync with broker)
```

### Cache Architecture
| Cache | Purpose | TTL |
|-------|---------|-----|
| Margins | Capital availability | 5 min |
| Positions | Current holdings | 1 min |
| LTP | Last traded price | 5 sec |
| Instruments | NFO/NSE symbols | 1 hour |
| Executed Signals | Deduplication | 24 hours |
| Market Data (Redis) | Cross-process sharing | Real-time |

---

## ⚠️ RISK MANAGEMENT

### Position-Level Controls
| Control | Value | Implementation |
|---------|-------|----------------|
| Max Loss per Trade | 2% of capital | `position_opening_decision.py` |
| Intraday Leverage | 4x | Margin calculation |
| Max Options Exposure | 50% of capital | Hard limit |
| Max Total Exposure | 80% of capital | Hard limit |
| Stop Loss | Dynamic (ATR-based) | Per-signal |

### Portfolio-Level Controls
| Control | Value | Implementation |
|---------|-------|----------------|
| Daily Loss Limit | 2% of portfolio | `position_opening_decision.py` |
| Max Concurrent Positions | Configurable | `orchestrator.py` |
| Trading Hours | 9:15 AM - 3:00 PM | Time restrictions |
| Square-off Time | 3:15 PM | Auto exit |

### Greeks Risk (Options)
| Greek | Monitoring | Action |
|-------|------------|--------|
| Delta | Portfolio delta exposure | Hedge triggers |
| Theta | Time decay tracking | Exit before expiry |
| Vega | Volatility exposure | Position sizing |

---

## 🔌 API ENDPOINTS

### Core Trading APIs
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/autonomous/start` | POST | Start trading system |
| `/autonomous/stop` | POST | Stop trading system |
| `/autonomous/status` | GET | System status |
| `/positions/` | GET | Current positions |
| `/trades/today` | GET | Today's trades |
| `/performance/daily-pnl` | GET | P&L metrics |

### Authentication APIs
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/zerodha/auth/submit-token` | POST | Submit access token |
| `/zerodha/auth/status` | GET | Auth status |
| `/zerodha/auth/validate` | GET | Token validation |

### Market Data APIs
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/market/bias` | GET | Current market bias |
| `/market/indices` | GET | NIFTY/BANKNIFTY data |
| `/truedata/status` | GET | Data feed status |

---

## 🚦 HONEST AUDIT FINDINGS

### ✅ STRENGTHS

1. **Robust Architecture**
   - Clean separation of concerns
   - Proper async/await patterns
   - Comprehensive error handling with fallbacks

2. **Professional Risk Management**
   - Multi-layer risk controls
   - Real-time position monitoring
   - Automatic square-off

3. **Advanced Mathematical Models**
   - All claimed models are actually implemented
   - No dead code remaining (after recent fixes)
   - Production-ready calculations

4. **Broker Integration**
   - Full Zerodha API coverage
   - Order placement with retries
   - Real-time position sync

5. **Caching Strategy**
   - Redis for cross-process state
   - In-memory caching for performance
   - Proper TTL management

### ⚠️ AREAS FOR IMPROVEMENT

1. **Backtesting**
   - Framework exists but needs production validation
   - Historical data fetching works but not fully tested
   - Recommendation: Run extensive backtests before live trading

2. **ML Model Training**
   - RandomForest classifier exists but needs training
   - No pre-trained models shipped
   - Recommendation: Collect data and train models

3. **Signal Quality**
   - Confidence scores are calculated but may need tuning
   - Threshold of 7.5 is empirical, not backtested
   - Recommendation: Tune based on live performance

4. **Options Pricing**
   - Black-Scholes is simplified (no dividends)
   - IV estimation is approximate
   - Recommendation: Use market IV when available

5. **Market Regime Detection**
   - HMM needs sufficient data (50+ observations)
   - Cold start issue on deployment
   - Recommendation: Pre-load historical data

### 🔴 KNOWN ISSUES

| Issue | Severity | Mitigation |
|-------|----------|------------|
| TrueData "User Already Connected" | Medium | Graceful reconnection logic |
| Phantom Positions | Low | Periodic sync with broker |
| MIS Order Cutoff (3:20 PM) | Info | Handled gracefully |
| Redis Connection Loss | Medium | Fallback to local mode |

---

## 📁 KEY FILE LOCATIONS

| Component | File |
|-----------|------|
| Main Orchestrator | `src/core/orchestrator.py` |
| Market Bias | `src/core/market_directional_bias.py` |
| Risk Manager | `src/core/risk_manager.py` |
| Trade Engine | `src/core/trade_engine.py` |
| Base Strategy | `strategies/base_strategy.py` |
| Momentum Strategy | `strategies/momentum_surfer.py` |
| Options Strategy | `strategies/news_impact_scalper.py` |
| Microstructure | `strategies/optimized_volume_scalper.py` |
| Regime Controller | `strategies/regime_adaptive_controller.py` |
| Zerodha Integration | `brokers/zerodha.py` |
| TrueData Client | `data/truedata_client.py` |
| Signal Deduplicator | `src/core/signal_deduplicator.py` |
| Position Tracker | `src/core/position_tracker.py` |

---

## 🚀 DEPLOYMENT

### Environment Variables Required
```bash
# Zerodha
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_ACCESS_TOKEN=daily_token

# TrueData
TRUEDATA_USERNAME=your_username
TRUEDATA_PASSWORD=your_password

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Trading Mode
PAPER_TRADING=false  # Set to true for paper trading
```

### Platform
- **Hosting:** DigitalOcean App Platform / Heroku
- **Database:** PostgreSQL (managed)
- **Cache:** Redis (managed)
- **Runtime:** Python 3.11+

---

## 📈 PERFORMANCE METRICS TRACKED

| Metric | Calculation |
|--------|-------------|
| Sharpe Ratio | `(returns - rf) / std(returns)` |
| Win Rate | `wins / total_trades` |
| Max Drawdown | Peak-to-trough decline |
| VaR (95%) | 5th percentile of returns |
| Kelly Criterion | Optimal position size |
| Statistical Significance | T-test p-value |

---

## 🔐 SECURITY

| Feature | Implementation |
|---------|----------------|
| API Authentication | Token-based (Zerodha OAuth) |
| Rate Limiting | Per-endpoint and global |
| Order Validation | Multi-layer checks |
| Database | Encrypted connection |
| Secrets | Environment variables only |

---

## 📞 SUPPORT & MAINTENANCE

### Daily Operations
1. Submit fresh Zerodha token (before 9:15 AM)
2. Verify system status via `/autonomous/status`
3. Start trading via `/autonomous/start`
4. Monitor via dashboard

### Monitoring Points
- Redis connection status
- TrueData feed status
- Position sync accuracy
- Order execution success rate

---

*Document Version: 1.0*
*Last Updated: December 3, 2025*
*Generated by: System Audit*

