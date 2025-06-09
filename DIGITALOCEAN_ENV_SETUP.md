# DigitalOcean Environment Variables Setup Guide

## Why Environment Variables Keep Disappearing

The environment variables disappear because:
1. The app spec file (`DIGITALOCEAN_FRESH_APP_SPEC.yaml`) doesn't include them
2. When DigitalOcean redeploys, it uses the app spec which resets everything

## Solution: Update App Spec with Environment Variables

### Option 1: Use the DigitalOcean Dashboard (Temporary)
1. Go to your app in DigitalOcean App Platform
2. Click on the API component
3. Go to Settings → Environment Variables
4. Add each variable manually

**Note**: These will be lost on next deployment if not in app spec!

### Option 2: Update App Spec (Permanent Solution)

1. Use the provided `DIGITALOCEAN_APP_SPEC_WITH_ENV.yaml`
2. Replace the placeholder values:
   - `YOUR_REDIS_PASSWORD_HERE` → Your actual Redis password
   - `YOUR_POSTGRES_HOST_HERE` → Your PostgreSQL host (e.g., `app-81-do-user-xxx.db.ondigitalocean.com`)
   - `YOUR_DATABASE_PASSWORD_HERE` → Your PostgreSQL password
   - `YOUR_JWT_SECRET_HERE` → A secure random string

3. Update your app using the CLI:
   ```bash
   doctl apps update <app-id> --spec DIGITALOCEAN_APP_SPEC_WITH_ENV.yaml
   ```

### Required Environment Variables

#### Redis Configuration
```
REDIS_HOST=redis-cache-do-user-23093341-0.k.db.ondigitalocean.com
REDIS_PORT=25061
REDIS_PASSWORD=<your-redis-password>
REDIS_SSL=true
```

#### Database Configuration
```
DATABASE_HOST=<your-postgres-host>.db.ondigitalocean.com
DATABASE_PORT=25060
DATABASE_NAME=db
DATABASE_USER=db
DATABASE_PASSWORD=<your-postgres-password>
```

#### Application Configuration
```
ENVIRONMENT=production
JWT_SECRET=<secure-random-string>
AUTONOMOUS_TRADING_ENABLED=true
PAPER_TRADING_ENABLED=true
```

### Getting Your Database Credentials

1. **Redis Password**:
   - Go to Databases in DigitalOcean
   - Click on your Redis database
   - Find the connection details
   - Copy the password

2. **PostgreSQL Details**:
   - Go to Databases in DigitalOcean
   - Click on your PostgreSQL database
   - Find the connection details
   - Copy the host and password

### Verifying Environment Variables

After setting up, check if they're working:

1. Check API logs for connection errors
2. Visit `/health` endpoint to see if Redis/Database are connected
3. The dashboard should start showing real data instead of errors

### Important Notes

- Always use `type: SECRET` for sensitive values in the app spec
- The app spec in the repository should use placeholders, not actual secrets
- Keep a local copy of your actual values in a secure location
- Consider using DigitalOcean's secrets management for production 