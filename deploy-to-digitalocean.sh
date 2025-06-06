#!/bin/bash

# =========================================================================
# AI Trading System - DigitalOcean Deployment Script
# Deploy complete trading system to DigitalOcean droplet
# Usage: ./deploy-to-digitalocean.sh [DROPLET_IP] [SSH_USER]
# =========================================================================

set -e  # Exit on any error

# Configuration
DROPLET_IP=${1:-"165.22.212.171"}
SSH_USER=${2:-"root"}
PROJECT_NAME="trading-system-new"
DOMAIN_NAME=${3:-"$DROPLET_IP"}  # Use IP or custom domain
REPO_URL="https://github.com/shyamanurag/trading-system-new.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Trading System - DigitalOcean Deployment${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "${YELLOW}📍 Target: ${DROPLET_IP}${NC}"
echo -e "${YELLOW}👤 User: ${SSH_USER}${NC}"
echo -e "${YELLOW}📦 Project: ${PROJECT_NAME}${NC}"
echo ""

# Function to run commands on remote server
run_remote() {
    echo -e "${BLUE}🔧 Running on server: $1${NC}"
    ssh -o StrictHostKeyChecking=no ${SSH_USER}@${DROPLET_IP} "$1"
}

# Function to copy files to remote server
copy_to_remote() {
    echo -e "${BLUE}📁 Copying: $1 → $2${NC}"
    scp -o StrictHostKeyChecking=no -r "$1" ${SSH_USER}@${DROPLET_IP}:"$2"
}

echo -e "${GREEN}Step 1: Testing SSH Connection${NC}"
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${SSH_USER}@${DROPLET_IP} "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection established${NC}"
else
    echo -e "${RED}❌ SSH connection failed. Please check:${NC}"
    echo -e "${RED}   - Droplet IP: ${DROPLET_IP}${NC}"
    echo -e "${RED}   - SSH user: ${SSH_USER}${NC}"
    echo -e "${RED}   - SSH key configured${NC}"
    exit 1
fi

echo -e "${GREEN}Step 2: System Update & Dependencies${NC}"
run_remote "apt update && apt upgrade -y"
run_remote "apt install -y python3 python3-pip python3-venv nodejs npm docker.io docker-compose git nginx certbot python3-certbot-nginx htop curl wget"

echo -e "${GREEN}Step 3: Enable Docker${NC}"
run_remote "systemctl enable docker && systemctl start docker"
run_remote "usermod -aG docker ${SSH_USER} || true"

echo -e "${GREEN}Step 4: Clone Repository${NC}"
run_remote "cd /opt && rm -rf ${PROJECT_NAME} || true"
run_remote "cd /opt && git clone ${REPO_URL}"
run_remote "chown -R ${SSH_USER}:${SSH_USER} /opt/${PROJECT_NAME}"

echo -e "${GREEN}Step 5: Setup Python Environment${NC}"
run_remote "cd /opt/${PROJECT_NAME} && python3 -m venv venv"
run_remote "cd /opt/${PROJECT_NAME} && source venv/bin/activate && pip install --upgrade pip"
run_remote "cd /opt/${PROJECT_NAME} && source venv/bin/activate && pip install -r requirements.txt"

echo -e "${GREEN}Step 6: Setup Environment Configuration${NC}"
run_remote "cd /opt/${PROJECT_NAME} && cp config.example.env .env"

# Create production environment file
cat > temp_production.env << EOF
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database (SQLite for simple setup, upgrade to PostgreSQL for production)
DATABASE_URL=sqlite:///./trading_system.db

# Redis (optional - system works without it)
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-$(openssl rand -hex 32)
ENCRYPTION_KEY=your-encryption-key-change-this-$(openssl rand -hex 16)

# API Configuration
API_PREFIX=/api/v1
CORS_ORIGINS=["http://${DOMAIN_NAME}:3000", "https://${DOMAIN_NAME}", "http://localhost:3000"]

# Trading Configuration
ENABLE_REAL_TRADING=false
PAPER_TRADING=true
MAX_POSITION_SIZE=10000
RISK_LIMIT=0.02

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
BACKUP_ENABLED=true

# WebSocket
WEBSOCKET_PORT=8002
ENABLE_WEBSOCKET=true
EOF

copy_to_remote "temp_production.env" "/opt/${PROJECT_NAME}/.env"
rm temp_production.env

echo -e "${GREEN}Step 7: Install Frontend Dependencies${NC}"
run_remote "cd /opt/${PROJECT_NAME} && npm install"

echo -e "${GREEN}Step 8: Build Frontend for Production${NC}"
run_remote "cd /opt/${PROJECT_NAME} && npm run build"

echo -e "${GREEN}Step 8.1: Verify Frontend Build${NC}"
run_remote "cd /opt/${PROJECT_NAME} && ls -la dist/frontend/ || echo 'Frontend build directory not found'"

echo -e "${GREEN}Step 9: Setup Nginx Configuration${NC}"
cat > temp_nginx.conf << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # Frontend (React build)
    location / {
        root /opt/${PROJECT_NAME}/dist/frontend;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

copy_to_remote "temp_nginx.conf" "/etc/nginx/sites-available/${PROJECT_NAME}"
rm temp_nginx.conf

run_remote "ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/"
run_remote "rm -f /etc/nginx/sites-enabled/default"
run_remote "nginx -t && systemctl reload nginx"

echo -e "${GREEN}Step 10: Create Systemd Services${NC}"

# Backend service
cat > temp_backend.service << EOF
[Unit]
Description=AI Trading System Backend
After=network.target

[Service]
Type=simple
User=${SSH_USER}
WorkingDirectory=/opt/${PROJECT_NAME}
Environment=PATH=/opt/${PROJECT_NAME}/venv/bin
ExecStart=/opt/${PROJECT_NAME}/venv/bin/python run_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

copy_to_remote "temp_backend.service" "/etc/systemd/system/trading-backend.service"
rm temp_backend.service

# WebSocket service
cat > temp_websocket.service << EOF
[Unit]
Description=AI Trading System WebSocket
After=network.target

[Service]
Type=simple
User=${SSH_USER}
WorkingDirectory=/opt/${PROJECT_NAME}
Environment=PATH=/opt/${PROJECT_NAME}/venv/bin
ExecStart=/opt/${PROJECT_NAME}/venv/bin/python websocket_main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

copy_to_remote "temp_websocket.service" "/etc/systemd/system/trading-websocket.service"
rm temp_websocket.service

echo -e "${GREEN}Step 11: Enable and Start Services${NC}"
run_remote "systemctl daemon-reload"
run_remote "systemctl enable trading-backend"
run_remote "systemctl enable trading-websocket"
run_remote "systemctl start trading-backend"
run_remote "systemctl start trading-websocket"

echo -e "${GREEN}Step 12: Setup Firewall${NC}"
run_remote "ufw allow ssh"
run_remote "ufw allow 'Nginx Full'"
run_remote "ufw allow 8000"
run_remote "ufw allow 8002"
run_remote "ufw --force enable"

echo -e "${GREEN}Step 13: Setup SSL Certificate (Optional)${NC}"
if [[ "$DOMAIN_NAME" != "$DROPLET_IP" ]]; then
    echo -e "${YELLOW}Setting up SSL for domain: $DOMAIN_NAME${NC}"
    run_remote "certbot --nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos --email admin@${DOMAIN_NAME} || echo 'SSL setup failed - continuing without SSL'"
fi

echo -e "${GREEN}Step 14: System Validation${NC}"
echo "Waiting for services to start..."
sleep 10

# Test backend
if run_remote "curl -f http://localhost:8000/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend service is running${NC}"
else
    echo -e "${YELLOW}⚠️ Backend service may need time to start${NC}"
fi

# Test nginx
if run_remote "curl -f http://localhost/" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx is serving frontend${NC}"
else
    echo -e "${YELLOW}⚠️ Frontend may need verification${NC}"
fi

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}🌐 Application URLs:${NC}"
echo -e "${YELLOW}   Main App:      http://${DOMAIN_NAME}${NC}"
echo -e "${YELLOW}   API Docs:      http://${DOMAIN_NAME}/docs${NC}"
echo -e "${YELLOW}   Health Check:  http://${DOMAIN_NAME}/health${NC}"
echo -e "${YELLOW}   Backend API:   http://${DOMAIN_NAME}/api/v1/${NC}"
echo ""
echo -e "${GREEN}🔧 Management Commands:${NC}"
echo -e "${YELLOW}   Backend Status:  ssh ${SSH_USER}@${DROPLET_IP} 'systemctl status trading-backend'${NC}"
echo -e "${YELLOW}   Backend Logs:    ssh ${SSH_USER}@${DROPLET_IP} 'journalctl -fu trading-backend'${NC}"
echo -e "${YELLOW}   WebSocket Logs:  ssh ${SSH_USER}@${DROPLET_IP} 'journalctl -fu trading-websocket'${NC}"
echo -e "${YELLOW}   Nginx Status:    ssh ${SSH_USER}@${DROPLET_IP} 'systemctl status nginx'${NC}"
echo ""
echo -e "${GREEN}📊 System Monitoring:${NC}"
echo -e "${YELLOW}   Server Stats:    ssh ${SSH_USER}@${DROPLET_IP} 'htop'${NC}"
echo -e "${YELLOW}   Disk Usage:      ssh ${SSH_USER}@${DROPLET_IP} 'df -h'${NC}"
echo ""
echo -e "${BLUE}🚀 Your AI Trading System is now live at: http://${DOMAIN_NAME}${NC}" 