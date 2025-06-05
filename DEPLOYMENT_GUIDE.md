# 🚀 DigitalOcean Deployment Guide

Complete guide to deploy your AI Trading System to DigitalOcean droplet at **165.22.212.171**.

## 📋 Prerequisites

- ✅ DigitalOcean droplet created (165.22.212.171)
- ✅ SSH access configured
- ✅ Domain name (optional) or using IP address
- ✅ GitHub repository ready

## 🎯 Deployment Options

### Option 1: 🚀 Automated Script Deployment (Recommended)

The fastest way to deploy your complete system:

```bash
# Make script executable
chmod +x deploy-to-digitalocean.sh

# Deploy to your droplet
./deploy-to-digitalocean.sh 165.22.212.171 root

# Or with custom domain
./deploy-to-digitalocean.sh 165.22.212.171 root yourdomain.com
```

**What the script does:**
1. ✅ Updates system packages
2. ✅ Installs Python 3, Node.js, Docker, Nginx
3. ✅ Clones your GitHub repository
4. ✅ Sets up Python virtual environment
5. ✅ Installs all dependencies
6. ✅ Builds React frontend
7. ✅ Configures Nginx reverse proxy
8. ✅ Creates systemd services
9. ✅ Sets up firewall rules
10. ✅ Validates deployment

### Option 2: 🔄 GitHub Actions Auto-Deployment

For continuous deployment on every code push:

#### 1. Setup GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions, add:

```bash
# Required Secrets
DIGITALOCEAN_SSH_KEY=your_private_ssh_key_content
JWT_SECRET_KEY=your-super-secret-jwt-key-32-chars-long
ENCRYPTION_KEY=your-encryption-key-16-chars

# Optional Secrets
DATABASE_URL=sqlite:///./trading_system.db
REDIS_URL=redis://localhost:6379/0
ENABLE_REAL_TRADING=false
MAX_POSITION_SIZE=10000
RISK_LIMIT=0.02
TRADING_API_KEY=your_api_key
TRADING_API_SECRET=your_api_secret
```

#### 2. Push to GitHub

```bash
git add .
git commit -m "🚀 Setup automated deployment"
git push origin main
```

The GitHub Actions workflow will automatically:
- ✅ Run 17 comprehensive tests
- ✅ Deploy to your droplet on success
- ✅ Run health checks
- ✅ Send deployment notifications

### Option 3: 📱 Manual Step-by-Step

If you prefer manual control:

#### 1. SSH into your droplet

```bash
ssh root@165.22.212.171
```

#### 2. Install dependencies

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nodejs npm git nginx
```

#### 3. Clone repository

```bash
cd /opt
git clone https://github.com/shyamanurag/trading-system-new.git
cd trading-system-new
```

#### 4. Setup Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. Build frontend

```bash
npm install
npm run build
```

#### 6. Configure Nginx

```bash
# Create Nginx configuration
cat > /etc/nginx/sites-available/trading-system << EOF
server {
    listen 80;
    server_name 165.22.212.171;

    location / {
        root /opt/trading-system-new/build;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/trading-system /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

#### 7. Create systemd service

```bash
cat > /etc/systemd/system/trading-backend.service << EOF
[Unit]
Description=AI Trading System Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/trading-system-new
Environment=PATH=/opt/trading-system-new/venv/bin
ExecStart=/opt/trading-system-new/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable trading-backend
systemctl start trading-backend
```

## 🌐 Access Your Application

After deployment, your trading system will be available at:

### 🔗 Application URLs
- **🏠 Main Dashboard**: http://165.22.212.171
- **📚 API Documentation**: http://165.22.212.171/docs
- **🩺 Health Check**: http://165.22.212.171/health
- **🔧 API Endpoints**: http://165.22.212.171/api/v1/

### 📱 Features Available
- ✅ **Real-time Trading Dashboard**
- ✅ **AI-Powered Recommendations**
- ✅ **Material-UI Interface**
- ✅ **WebSocket Live Data**
- ✅ **Risk Management Tools**
- ✅ **Portfolio Analytics**

## 🔧 Post-Deployment Management

### Service Management

```bash
# Check service status
systemctl status trading-backend
systemctl status nginx

# View logs
journalctl -fu trading-backend
journalctl -fu nginx

# Restart services
systemctl restart trading-backend
systemctl restart nginx
```

### Update Deployment

```bash
# SSH into server
ssh root@165.22.212.171

# Pull latest changes
cd /opt/trading-system-new
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt
npm install
npm run build

# Restart services
systemctl restart trading-backend
```

### System Monitoring

```bash
# Check system resources
htop
df -h
free -h

# Check application health
curl http://localhost:8000/health

# Monitor logs in real-time
tail -f /var/log/nginx/access.log
journalctl -fu trading-backend
```

## 🔒 Security Configuration

### Firewall Setup

```bash
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

### SSL Certificate (Optional)

If you have a domain name:

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d yourdomain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Service won't start
```bash
# Check logs
journalctl -fu trading-backend

# Check dependencies
cd /opt/trading-system-new
source venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"
```

#### 2. Nginx configuration error
```bash
# Test configuration
nginx -t

# Check error logs
tail -f /var/log/nginx/error.log
```

#### 3. Port conflicts
```bash
# Check what's using port 8000
lsof -i :8000
netstat -tulpn | grep 8000
```

#### 4. Permission issues
```bash
# Fix ownership
chown -R root:root /opt/trading-system-new
chmod +x /opt/trading-system-new/run_server.py
```

### Health Checks

```bash
# Backend health
curl -f http://localhost:8000/health

# Frontend access
curl -f http://localhost/

# API functionality
curl -f http://localhost:8000/docs
```

## 📊 Performance Optimization

### System Optimization

```bash
# Increase file limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize Nginx
# Edit /etc/nginx/nginx.conf
worker_connections 1024;
keepalive_timeout 65;
client_max_body_size 10M;
```

### Application Optimization

```bash
# Use production build
npm run build

# Enable gzip compression in Nginx
gzip on;
gzip_types text/plain application/json application/javascript text/css;
```

## 🚀 Success Checklist

After deployment, verify:

- ✅ **Backend API** responds at http://165.22.212.171/health
- ✅ **Frontend Dashboard** loads at http://165.22.212.171
- ✅ **API Documentation** available at http://165.22.212.171/docs
- ✅ **Services running** (trading-backend, nginx)
- ✅ **Firewall configured** (SSH, HTTP/HTTPS allowed)
- ✅ **Logs accessible** (systemctl, journalctl)

## 📞 Support

If you encounter issues:

1. **Check the logs** first:
   ```bash
   journalctl -fu trading-backend
   tail -f /var/log/nginx/error.log
   ```

2. **Run system validation**:
   ```bash
   cd /opt/trading-system-new
   source venv/bin/activate
   python complete_system_test.py
   ```

3. **Contact support**:
   - 🐛 Create issue: [GitHub Issues](https://github.com/shyamanurag/trading-system-new/issues)
   - 📧 Email: [Create an issue](https://github.com/shyamanurag/trading-system-new/issues/new)

---

**🎉 Congratulations! Your AI Trading System is now live at http://165.22.212.171**

Built with FastAPI, React, Material-UI, and deployed on DigitalOcean! 🚀 