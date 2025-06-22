# Frontend Fixes for Digital Ocean Deployment

## Issues Found:

1. **Dashboard API Path Duplication**
   - Frontend calls: `/api/v1/dashboard/summary`
   - Backend expects: `/api/v1/dashboard/dashboard/summary`
   - **Fix**: Update frontend to use the correct path

2. **Health Endpoint Returns Plain Text**
   - `/health/ready` returns plain text "ready"
   - Frontend expects JSON response
   - **Fix**: Use `/health/ready/json` endpoint instead

3. **WebSocket Path Issue**
   - Frontend tries to connect to `/ws/${userId}` (e.g., `/ws/admin`)
   - Backend only has `/ws` endpoint
   - **Fix**: Already fixed in WebSocketStatus.jsx

4. **Daily PnL Endpoint Issue**
   - Frontend calls: `/api/v1/performance/daily-pnl`
   - Backend has: `/api/v1/monitoring/daily-pnl`
   - **Fix**: Update frontend path

## Required Frontend Changes:

### 1. Fix SystemHealthMonitor.jsx
```javascript
// Change from:
const response = await fetch(`${API_BASE_URL}/health/ready`);

// To:
const response = await fetch(`${API_BASE_URL}/health/ready/json`);
```

### 2. Fix api/config.js
```javascript
export const API_ENDPOINTS = {
    // ... existing code ...
    
    // Fix dashboard path duplication:
    DASHBOARD_SUMMARY: createEndpoint('/api/v1/dashboard/dashboard/summary'),
    
    // Fix daily PnL path:
    DAILY_PNL: createEndpoint('/api/v1/monitoring/daily-pnl'),
    
    // Fix recommendations path (check if it exists):
    RECOMMENDATIONS: createEndpoint('/api/v1/recommendations/analysis'),
    
    // ... rest of code ...
};
```

### 3. Alternative Solution - Fix Backend Routes

Instead of changing all frontend paths, we could fix the backend routes to match what the frontend expects. This would be cleaner.

## Backend Route Fixes Needed:

1. In `src/api/dashboard_api.py`:
   - Change `@router.get("/dashboard/summary")` to `@router.get("/summary")`
   
2. In `main.py` where performance router is mounted:
   - Ensure daily-pnl is accessible at `/api/v1/performance/daily-pnl`

## Recommended Approach:

Fix the frontend paths to match the existing backend routes since the backend is already deployed and working. This avoids breaking changes for other clients that might be using the API. 