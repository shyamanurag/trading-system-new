# GitHub Repository Secrets Configuration

This document explains how to configure the required GitHub repository secrets for the CI/CD pipeline to work properly.

## Required Secrets

### DigitalOcean Configuration
```
DIGITALOCEAN_ACCESS_TOKEN     # DigitalOcean API token
DO_REGISTRY_NAME             # Container registry name (e.g., your-registry)
DO_K8S_CLUSTER_NAME          # Kubernetes cluster name
```

### Database Configuration
```
STAGING_DATABASE_URL         # Staging database connection string
STAGING_REDIS_URL           # Staging Redis connection string
STAGING_JWT_SECRET          # Staging JWT secret key

PRODUCTION_DATABASE_URL     # Production database connection string
PRODUCTION_REDIS_URL        # Production Redis connection string
PRODUCTION_JWT_SECRET       # Production JWT secret key
```

### Notification Configuration
```
SLACK_WEBHOOK_URL           # Slack webhook for deployment notifications
```

### API Testing Configuration
```
STAGING_URL                 # Staging environment URL
STAGING_API_TOKEN          # API token for staging tests
```

### ML Model Configuration
```
MODEL_REGISTRY_URL         # ML model registry URL
MODEL_REGISTRY_TOKEN       # Model registry access token
MODEL_SERVING_ENDPOINT     # Model serving API endpoint
MODEL_SERVING_TOKEN        # Model serving access token
```

## How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name from the list above

## Example Values (Development)

```bash
# DigitalOcean (replace with your actual values)
DIGITALOCEAN_ACCESS_TOKEN=dop_v1_your_actual_token_here
DO_REGISTRY_NAME=trading-system-registry
DO_K8S_CLUSTER_NAME=trading-system-k8s

# Database URLs
STAGING_DATABASE_URL=postgresql://user:pass@staging-db:5432/trading_system
PRODUCTION_DATABASE_URL=postgresql://user:pass@prod-db:5432/trading_system

# Redis URLs
STAGING_REDIS_URL=redis://staging-redis:6379/0
PRODUCTION_REDIS_URL=redis://prod-redis:6379/0

# JWT Secrets (generate with: openssl rand -hex 32)
STAGING_JWT_SECRET=your-staging-jwt-secret-32-chars-minimum
PRODUCTION_JWT_SECRET=your-production-jwt-secret-32-chars-minimum

# Slack webhook for notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# API testing
STAGING_URL=https://staging-api.yourdomain.com
STAGING_API_TOKEN=your-staging-api-token

# ML Model serving (optional - set to placeholder if not using)
MODEL_REGISTRY_URL=https://your-model-registry.com
MODEL_REGISTRY_TOKEN=your-model-registry-token
MODEL_SERVING_ENDPOINT=https://your-model-api.com
MODEL_SERVING_TOKEN=your-model-serving-token
```

## Security Notes

- Never commit secrets to the repository
- Use strong, randomly generated secrets for production
- Rotate secrets periodically
- Use different secrets for staging and production
- Consider using environment-specific encryption keys

## Testing Without Secrets

To test the workflow without setting up all services:

1. Set placeholder values for optional secrets
2. Comment out deployment steps that require external services
3. Focus on the build and test stages first

## Troubleshooting

If you see "Context access might be invalid" warnings:
1. Verify the secret names match exactly
2. Ensure secrets are added to the repository (not environment)
3. Check that the workflow has permission to access secrets 