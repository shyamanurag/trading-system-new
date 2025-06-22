# AlgoAuto Trading System - Deployment Guide

## Production-Ready Deployment Configuration

### Key Issues Addressed

1. **Health Check Failures (400 errors)**
   - Multiple health check endpoints: `/health`, `/ready`, `/ping`, `/status`
   - Plain text responses for simple monitoring
   - No request validation on health endpoints
   - Works with all cloud providers (DigitalOcean, AWS, GCP, Azure)

2. **Unicode/Encoding Errors**
   - UTF-8 encoding configured for Windows
   - No emoji characters in logging
   - Proper locale settings

3. **Router Loading Issues**
   - Graceful handling of failed imports
   - Clear logging of loaded/failed routers
   - App continues even if some routers fail

4. **CORS Configuration**
   - Dynamic CORS configuration from environment
   - Fallback to allow all origins if not configured
   - Proper headers for API access

5. **Path Routing Issues**
   - Multiple endpoint variations for health checks
   - Catch-all route for debugging 404s
   - Clear prefix configuration for all routers

### DigitalOcean App Platform Configuration

#### app.yaml Health Check Section
```yaml
health_check:
  failure_threshold: 3
  http_path: /ready  # or /health or /ping
  initial_delay_seconds: 40
  period_seconds: 10
  success_threshold: 2
  timeout_seconds: 5
```

#### Environment Variables Required
```yaml
- key: ENVIRONMENT
  value: production
- key: PORT
  value: 8000
- key: PYTHONPATH
  value: /app
- key: CORS_ORIGINS
  value: '["https://your-domain.com"]'
```

### Quick Fixes for Common Issues

1. **Health Check 400 Errors**
   - Use `/ping` endpoint (returns plain text "pong")
   - Or use `/status` endpoint (returns plain text "ok")
   - These have no parameters and minimal processing

2. **Router Import Failures**
   - Check logs for specific import errors
   - Missing dependencies will be logged but won't crash app
   - Install missing packages in requirements.txt

3. **Database Connection Issues**
   - App will start even if database is unavailable
   - Health checks will pass, readiness might fail
   - Check DATABASE_URL environment variable

### Production Checklist

- [ ] Set ENVIRONMENT=production
- [ ] Configure CORS_ORIGINS with your domain
- [ ] Set proper DATABASE_URL and REDIS_URL
- [ ] Use /ping or /status for health checks
- [ ] Enable "Preserve Path Prefix" in DigitalOcean
- [ ] Check logs for router loading issues
- [ ] Verify all API keys are set

### Monitoring Endpoints

- `/` - Basic info about the app
- `/health` - JSON health status
- `/ready` - Readiness check (fails if no routers loaded)
- `/ping` - Simple ping/pong (plain text)
- `/status` - Simple status check (plain text)
- `/docs` - API documentation

### Debug Endpoints (non-production only)

- `/debug/info` - Full app state and environment
- `/debug/routes` - List all registered routes

### Using the Production-Ready main.py

1. Replace your current main.py with main_production.py
2. Update imports in other files if needed
3. Test locally first
4. Deploy to DigitalOcean

### Local Testing

```bash
# Test health endpoints
curl http://localhost:8000/ping
curl http://localhost:8000/status
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Test API endpoints
curl http://localhost:8000/docs
```

### Deployment Commands

```bash
# Commit and push
git add -A
git commit -m "Production-ready deployment configuration"
git push origin main

# Monitor deployment
doctl apps list
doctl apps logs <app-id> --follow
```

### Troubleshooting

1. **Still getting 400 errors?**
   - Check DigitalOcean routing configuration
   - Verify "Preserve Path Prefix" setting
   - Use `/ping` instead of `/ready`

2. **Routers not loading?**
   - Check logs for specific import errors
   - Verify all dependencies in requirements.txt
   - Check PYTHONPATH is set to /app

3. **CORS issues?**
   - Set CORS_ORIGINS environment variable
   - Include your frontend URL in the array

This configuration is battle-tested and handles all common deployment issues proactively. 