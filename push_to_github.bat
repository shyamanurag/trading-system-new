@echo off
echo ==========================================
echo PUSHING CRITICAL FIXES TO GITHUB
echo ==========================================
echo.
echo FIXES IN THIS PUSH:
echo 1. Fixed f-string backslash syntax error in zerodha.py line 2575
echo 2. Added missing positions router import in main.py
echo.
echo 3. MAJOR: Comprehensive market bias logic rewrite
echo    - NEW: _identify_market_scenario() detects 8 market patterns
echo    - GAP_UP_CONTINUATION, GAP_UP_FADE
echo    - GAP_DOWN_CONTINUATION, GAP_DOWN_RECOVERY  
echo    - FLAT_TRENDING_UP, FLAT_TRENDING_DOWN
echo    - CHOPPY, MIXED_SIGNALS
echo    - Fixed: BULLISH bias when market is DOWN bug
echo    - Scenario stored in _last_scenario for strategies
echo.
echo 4. Fixed market internals A/D ratio thresholds
echo    - A/D 0.70 now correctly classified as BEARISH
echo    - Granular scoring: 0.5/0.67/0.80/0.90 and 1.1/1.25/1.5/2.0
echo    - Added VWAP, VIX change, sector rotation factors
echo.
echo 5. Strategy alignment update (base_strategy.py)
echo    - _calculate_adaptive_confidence_threshold now uses scenarios
echo    - Scenario-specific threshold adjustments per signal direction
echo    - Better handling of regime + bias confidence combinations
echo ==========================================

cd /d C:\trading-system-new

echo.
echo === Current Git Status ===
git status

echo.
echo === Adding all changes ===
git add -A

echo.
echo === Committing ===
git commit -m "MAJOR: Comprehensive market bias scenarios + aligned strategy thresholds"

echo.
echo === Pushing to GitHub ===
git push origin main

echo.
echo === Verifying Push ===
git log origin/main --oneline -5

echo.
echo ==========================================
echo DONE - Check output above for errors
echo If push succeeded, DigitalOcean will auto-deploy
echo ==========================================
pause
