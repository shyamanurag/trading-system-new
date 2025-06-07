#!/bin/bash
# Production Deployment Script for DigitalOcean App Platform
# Updated: 2025-06-07 - Single Dockerfile deployment with robust error handling

set -e  # Exit on any error

echo "🚀 Starting DigitalOcean Production Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    log_info "Validating deployment environment..."
    
    # Check if we're in the right directory
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile not found. Are you in the correct directory?"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found. Cannot proceed with deployment."
        exit 1
    fi
    
    if [ ! -f "config/production.env" ]; then
        log_warning "config/production.env not found. Using environment variables."
    else
        log_success "Production environment file found"
    fi
    
    if [ ! -f "app.yaml" ]; then
        log_error "app.yaml not found. DigitalOcean configuration missing."
        exit 1
    fi
    
    log_success "Environment validation passed"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if doctl is installed
    if ! command -v doctl &> /dev/null; then
        log_warning "DigitalOcean CLI (doctl) not found. Please install it for deployment."
        log_info "Install: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    else
        log_success "DigitalOcean CLI found"
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed."
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Build verification
verify_build() {
    log_info "Verifying Docker build configuration..."
    
    # Check Dockerfile syntax
    if docker build --dry-run . > /dev/null 2>&1; then
        log_success "Dockerfile syntax is valid"
    else
        log_error "Dockerfile has syntax errors"
        exit 1
    fi
    
    # Verify requirements.txt
    PACKAGE_COUNT=$(wc -l < requirements.txt)
    log_info "Found $PACKAGE_COUNT packages in requirements.txt"
    
    if [ $PACKAGE_COUNT -lt 10 ]; then
        log_warning "Only $PACKAGE_COUNT packages found. This seems low for a production system."
    else
        log_success "Requirements file looks comprehensive"
    fi
}

# Deploy to DigitalOcean
deploy_to_digitalocean() {
    log_info "Deploying to DigitalOcean App Platform..."
    
    # Check if we can authenticate with DigitalOcean
    if command -v doctl &> /dev/null; then
        if doctl auth list > /dev/null 2>&1; then
            log_success "DigitalOcean authentication verified"
            
            # Deploy using doctl
            log_info "Creating/updating app on DigitalOcean..."
            if doctl apps create --spec app.yaml; then
                log_success "App deployment initiated successfully!"
                log_info "Check deployment status at: https://cloud.digitalocean.com/apps"
            else
                log_error "Failed to deploy app. Check your app.yaml configuration."
                exit 1
            fi
        else
            log_warning "DigitalOcean authentication required. Run: doctl auth init"
        fi
    else
        log_info "Manual deployment required:"
        log_info "1. Go to https://cloud.digitalocean.com/apps"
        log_info "2. Create new app from source code"
        log_info "3. Connect your GitHub repository"
        log_info "4. Use the app.yaml file for configuration"
    fi
}

# Display deployment information
show_deployment_info() {
    log_info "Deployment Configuration Summary:"
    echo "=================================="
    echo "🐳 Docker: Single Dockerfile deployment"
    echo "📦 Dependencies: requirements.txt ($(wc -l < requirements.txt) packages)"
    echo "🔧 Configuration: app.yaml"
    echo "🌐 Platform: DigitalOcean App Platform"
    echo "🚀 Startup: start_production.py"
    echo ""
    
    if [ -f "config/production.env" ]; then
        log_info "Environment variables loaded from: config/production.env"
    else
        log_warning "Environment variables from system/DigitalOcean settings"
    fi
    
    echo ""
    log_info "Post-deployment checklist:"
    echo "✅ Monitor deployment logs"
    echo "✅ Verify database connectivity"
    echo "✅ Test API endpoints"
    echo "✅ Check WebSocket connections"
    echo "✅ Validate trading system status"
}

# Main deployment flow
main() {
    echo "🎯 DigitalOcean Single Dockerfile Deployment"
    echo "============================================"
    
    validate_environment
    check_requirements
    verify_build
    
    log_info "Ready to deploy to DigitalOcean App Platform"
    
    # Ask for confirmation
    read -p "🤔 Proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_to_digitalocean
        show_deployment_info
        
        log_success "🎉 Deployment process completed!"
        log_info "Check your DigitalOcean dashboard for deployment status."
    else
        log_info "Deployment cancelled by user."
        exit 0
    fi
}

# Run main function
main "$@" 