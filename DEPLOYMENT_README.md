# Deployment Guide - Trading System

## Overview
This guide documents the unified deployment process for the trading system across all environments.

## Prerequisites
- Python 3.8 or higher
- Git
- Docker (for staging/production deployments)
- DigitalOcean CLI (`doctl`) for production deployments

## Unified Deployment Script

All deployments are now handled through a single script: `deploy.py`

### Basic Usage

```bash
# Deploy to local environment
python deploy.py local

# Deploy to staging environment
python deploy.py staging

# Deploy to production environment
python deploy.py production
```

### Command Line Options

- `--verbose, -v`: Enable verbose output for debugging
- `--skip-tests`: Skip running tests before deployment (not recommended)
- `--no-backup`: Skip creating backup before deployment

### Examples

```bash
# Deploy to local with verbose output
python deploy.py local --verbose

# Deploy to production with all safety checks
python deploy.py production

# Quick local deployment (skip tests and backup)
python deploy.py local --skip-tests --no-backup
```

## Environment-Specific Details

### Local Deployment
- Creates/uses virtual environment in `venv_local/`
- Installs dependencies from `requirements.txt`
- Starts the application using `python main.py`
- No Docker required

### Staging Deployment
- Builds Docker image tagged as `trading-system:staging`
- Runs container with staging environment variables
- Exposes port 8001
- Requires `config/staging.env` file

### Production Deployment
- Ensures deployment from `main` branch only
- Checks for uncommitted changes
- Creates Git tag for the release
- Deploys to DigitalOcean App Platform
- Requires `.do/app.yaml` configuration

## Configuration Files

### Required Files
- `requirements.txt`: Python dependencies
- `main.py`: Application entry point
- `Dockerfile`: For staging/production deployments

### Environment Variables
- Local: `.env` or environment variables
- Staging: `config/staging.env`
- Production: `config/production.env`

## Deployment Process

1. **Prerequisites Check**
   - Verifies Python version
   - Checks for required files
   - Validates environment-specific requirements

2. **Backup Creation**
   - Creates timestamped backup in `deployment_backups/`
   - Backs up configuration files
   - Preserves current deployment state

3. **Test Execution** (except for local)
   - Runs full test suite
   - Aborts deployment on test failure
   - Ensures code quality

4. **Application Build**
   - Installs/updates dependencies
   - Builds frontend (if exists)
   - Prepares application for deployment

5. **Environment Deployment**
   - Executes environment-specific deployment steps
   - Monitors deployment progress
   - Reports success/failure

## Troubleshooting

### Common Issues

1. **"Python 3.8+ is required"**
   - Update your Python installation
   - Use `python3` instead of `python` on some systems

2. **"Required file missing"**
   - Ensure you're in the project root directory
   - Check that all required files exist

3. **"Must be on main branch for production"**
   - Switch to main branch: `git checkout main`
   - Merge your changes to main first

4. **"Uncommitted changes detected"**
   - Commit your changes: `git add . && git commit -m "message"`
   - Or stash them: `git stash`

### Logs and Debugging

- Use `--verbose` flag for detailed output
- Check `deployment_backups/` for previous configurations
- Review application logs in respective environments

## Rollback Procedure

1. **Local**: Simply restart with previous configuration
2. **Staging**: Redeploy previous Docker image
3. **Production**: Use DigitalOcean's rollback feature or redeploy previous Git tag

## Security Notes

- Never commit sensitive credentials to Git
- Use environment variables for secrets
- Rotate credentials regularly
- Monitor deployment logs for security issues

## Migration from Old Scripts

If you were using old deployment scripts:
- `deploy.sh` → `python deploy.py production`
- `deploy.bat` → `python deploy.py production`
- `deploy_production.py` → `python deploy.py production`
- `start_local.bat` → `python deploy.py local`

All old scripts have been archived in `deployment_scripts_archive/` for reference.

## Support

For deployment issues:
1. Check this guide first
2. Review error messages with `--verbose`
3. Check application logs
4. Contact the development team

## Next Steps

After successful deployment:
1. Verify application health at `/health` endpoint
2. Check WebSocket connections at `/ws`
3. Monitor logs for any errors
4. Test critical functionality 