# 🚀 Production Deployment Guide - AI-Powered Trading System

## 📋 **Overview**

This guide provides complete instructions for deploying the professional AI-powered trading system to DigitalOcean for real money trading. The system includes advanced machine learning models, comprehensive security, and production-grade infrastructure.

---

## 🏗️ **Architecture Overview**

### **System Components**
- **Main API** (Port 8000): FastAPI application with comprehensive trading endpoints
- **Trading Engine** (Port 8001): Core AI trading strategies and risk management
- **WebSocket Server** (Port 8002): Real-time market data and live updates
- **AI/ML Models**: Price prediction, sentiment analysis, risk assessment, portfolio optimization
- **Database**: PostgreSQL with performance-optimized indexes
- **Cache**: Redis for high-performance data caching
- **Monitoring**: Prometheus + Grafana + comprehensive dashboards

### **Infrastructure Stack**
- **Platform**: DigitalOcean Kubernetes (DOKS)
- **Container Registry**: DigitalOcean Container Registry
- **Database**: DigitalOcean Managed PostgreSQL
- **Load Balancer**: DigitalOcean Load Balancer
- **Storage**: DigitalOcean Block Storage
- **Monitoring**: Prometheus + Grafana Cloud
- **CI/CD**: GitHub Actions + Automated Deployment

---

## 🔧 **Prerequisites**

### **Required Accounts & Services**
1. **DigitalOcean Account** with billing enabled
2. **GitHub Account** with repository access
3. **Trading Broker Accounts** (Zerodha KiteConnect, TrueData)
4. **Domain Name** for production URLs
5. **SSL Certificates** (Let's Encrypt recommended)

### **Required Tools**
```bash
# Install required CLI tools
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.98.0/doctl-1.98.0-linux-amd64.tar.gz | tar -xzv
sudo mv doctl /usr/local/bin

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

---

## 🚀 **Step 1: DigitalOcean Infrastructure Setup**

### **1.1 Create Kubernetes Cluster**
```bash
# Authenticate with DigitalOcean
doctl auth init

# Create Kubernetes cluster
doctl kubernetes cluster create trading-cluster \
  --region nyc1 \
  --version 1.28.2-do.0 \
  --node-pool "name=worker-pool;size=s-4vcpu-8gb;count=3;auto-scale=true;min-nodes=3;max-nodes=10" \
  --maintenance-window="saturday=12:00" \
  --surge-upgrade=true \
  --ha=true

# Get cluster credentials
doctl kubernetes cluster kubeconfig save trading-cluster
```

### **1.2 Create Container Registry**
```bash
# Create container registry
doctl registry create trading-system --region nyc3

# Configure Docker to use the registry
doctl registry login
```

### **1.3 Create Managed Database**
```bash
# Create PostgreSQL database
doctl databases create trading-db \
  --engine pg \
  --version 15 \
  --region nyc1 \
  --size db-s-2vcpu-4gb \
  --num-nodes 2

# Create database user
doctl databases user create trading-db trading-user

# Create production database
doctl databases db create trading-db trading_production
```

### **1.4 Create Load Balancer**
```bash
# Load balancer will be created automatically via Kubernetes service
# with annotations in deployment.yaml
```

---

## 🔐 **Step 2: Security Configuration**

### **2.1 Create Kubernetes Secrets**
```bash
# Create namespace
kubectl create namespace trading-production

# Create database secrets
kubectl create secret generic trading-secrets -n trading-production \
  --from-literal=database-url="postgresql://trading-user:PASSWORD@trading-db-do-user-DATABASE_ID-0.b.db.ondigitalocean.com:25060/trading_production?sslmode=require" \
  --from-literal=redis-url="redis://localhost:6379/0" \
  --from-literal=jwt-secret="$(openssl rand -base64 32)" \
  --from-literal=encryption-key="$(openssl rand -base64 32)"

# Create broker API secrets
kubectl create secret generic broker-secrets -n trading-production \
  --from-literal=zerodha-api-key="YOUR_ZERODHA_API_KEY" \
  --from-literal=zerodha-api-secret="YOUR_ZERODHA_API_SECRET" \
  --from-literal=truedata-username="YOUR_TRUEDATA_USERNAME" \
  --from-literal=truedata-password="YOUR_TRUEDATA_PASSWORD"

# Create service account
kubectl create serviceaccount trading-system-sa -n trading-production
```

### **2.2 Configure Network Policies**
```bash
# Network policies are included in k8s/production/deployment.yaml
# They restrict traffic between pods and external access
kubectl apply -f k8s/production/deployment.yaml
```

---

## 🤖 **Step 3: AI/ML Model Setup**

### **3.1 Prepare Model Storage**
```bash
# Create persistent volume for models
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: models-pvc
  namespace: trading-production
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
  storageClassName: do-block-storage
EOF
```

### **3.2 Initialize MLflow Tracking**
```bash
# Set up MLflow for model tracking
export MLFLOW_TRACKING_URI="postgresql://mlflow-user:PASSWORD@mlflow-db/mlflow"
export MODEL_REGISTRY_URL="https://models.yourdomain.com"
export MODEL_SERVING_ENDPOINT="https://inference.yourdomain.com"
```

---

## 📊 **Step 4: GitHub Actions Configuration**

### **4.1 Set Repository Secrets**
Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```bash
# DigitalOcean Configuration
DIGITALOCEAN_ACCESS_TOKEN=your_do_access_token
DO_REGISTRY_NAME=trading-system
DO_K8S_CLUSTER_NAME=trading-cluster

# Database Configuration
PRODUCTION_DATABASE_URL=postgresql://...
STAGING_DATABASE_URL=postgresql://...
PRODUCTION_REDIS_URL=redis://...
STAGING_REDIS_URL=redis://...

# Security Configuration
PRODUCTION_JWT_SECRET=base64_encoded_secret
STAGING_JWT_SECRET=base64_encoded_secret

# Broker API Configuration (Encrypted)
ZERODHA_PRODUCTION_API_KEY=encrypted_key
ZERODHA_PRODUCTION_API_SECRET=encrypted_secret
TRUEDATA_PRODUCTION_USERNAME=encrypted_username
TRUEDATA_PRODUCTION_PASSWORD=encrypted_password

# ML Model Configuration
MODEL_REGISTRY_URL=https://models.yourdomain.com
MODEL_REGISTRY_TOKEN=your_registry_token
MODEL_SERVING_ENDPOINT=https://inference.yourdomain.com
MODEL_SERVING_TOKEN=your_serving_token

# Notification Configuration
SLACK_WEBHOOK_URL=your_slack_webhook_url

# URLs for testing
STAGING_URL=https://staging-api.yourdomain.com
STAGING_API_TOKEN=staging_test_token
```

### **4.2 Verify GitHub Actions**
The CI/CD pipeline (`.github/workflows/deploy.yml`) includes:
- ✅ Comprehensive testing (unit, integration, performance, security)
- ✅ Multi-stage Docker builds with security scanning
- ✅ Automated deployment to staging and production
- ✅ AI model deployment and validation
- ✅ Health checks and rollback capabilities

---

## 🏭 **Step 5: Production Deployment**

### **5.1 Initial Deployment**
```bash
# Clone repository
git clone https://github.com/yourusername/trading-system.git
cd trading-system

# Build and deploy to production
git checkout main
git tag v2.0.0
git push origin v2.0.0

# The GitHub Actions pipeline will automatically:
# 1. Run all tests and security scans
# 2. Build optimized Docker images
# 3. Deploy to staging for validation
# 4. Deploy to production after approval
# 5. Deploy AI/ML models
# 6. Run comprehensive health checks
```

### **5.2 Manual Deployment (if needed)**
```bash
# Build production image
docker build -f Dockerfile.production -t registry.digitalocean.com/trading-system/trading-system:latest .

# Push to registry
docker push registry.digitalocean.com/trading-system/trading-system:latest

# Deploy to Kubernetes
envsubst < k8s/production/deployment.yaml | kubectl apply -f -

# Verify deployment
kubectl get pods -n trading-production
kubectl get services -n trading-production
```

---

## 📈 **Step 6: Monitoring Setup**

### **6.1 Deploy Prometheus and Grafana**
```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set grafana.adminPassword="secure-admin-password"

# Get Grafana admin password
kubectl get secret --namespace monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

### **6.2 Import Trading Dashboards**
```bash
# Import pre-built Grafana dashboards
python monitoring/grafana_dashboards.py export

# Upload dashboards to Grafana
for dashboard in monitoring/dashboards/*.json; do
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_GRAFANA_API_KEY" \
    -d @"$dashboard" \
    "https://grafana.yourdomain.com/api/dashboards/db"
done
```

---

## 💾 **Step 7: Database Setup**

### **7.1 Run Migrations**
```bash
# Run database migrations
kubectl exec -it deployment/trading-system-production -n trading-production -- \
  python -m alembic upgrade head

# Apply performance indexes
kubectl exec -it deployment/trading-system-production -n trading-production -- \
  psql $DATABASE_URL -f database/migrations/001_add_performance_indexes.sql
```

### **7.2 Setup Backups**
```bash
# Create backup CronJob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: trading-production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: database-url
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL | gzip > /backup/trading_production_$(date +%Y%m%d_%H%M%S).sql.gz
              # Upload to DigitalOcean Spaces or S3
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
EOF
```

---

## 🔧 **Step 8: Production Configuration**

### **8.1 Environment Configuration**
Ensure production configuration in `config/production.yaml`:

```yaml
environment: production
debug: false
version: "2.0.0"

database:
  ssl_mode: "require"
  pool_size: 20
  max_overflow: 30

security:
  require_2fa: true
  max_login_attempts: 3
  lockout_duration_minutes: 60

trading:
  max_daily_trades: 1000
  max_position_size_percent: 5.0
  risk_per_trade_percent: 0.5

compliance:
  sebi_reporting_enabled: true
  audit_trail_retention_days: 2555
```

### **8.2 DNS Configuration**
```bash
# Point your domain to the load balancer
# Get load balancer IP
kubectl get service trading-system-production -n trading-production

# Create DNS A records:
# api.yourdomain.com → LOAD_BALANCER_IP
# ws.yourdomain.com → LOAD_BALANCER_IP
# admin.yourdomain.com → LOAD_BALANCER_IP
```

### **8.3 SSL Certificates**
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Create ingress with SSL
kubectl apply -f k8s/production/ingress.yaml
```

---

## 🧪 **Step 9: Testing & Validation**

### **9.1 Health Checks**
```bash
# Check application health
curl -f https://api.yourdomain.com/health

# Check all endpoints
curl -f https://api.yourdomain.com/api/v1/health
curl -f https://ws.yourdomain.com/ws/health

# Check AI model endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.yourdomain.com/api/v1/models/status
```

### **9.2 Load Testing**
```bash
# Install k6 for load testing
curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz -L | tar xvz --strip-components 1

# Run load tests
./k6 run tests/performance/api-load-test.js
```

### **9.3 Security Validation**
```bash
# Run security scans
docker run --rm -v $(pwd):/app aquasec/trivy fs /app

# Check SSL configuration
curl -I https://api.yourdomain.com

# Verify security headers
curl -I https://api.yourdomain.com | grep -E "(X-Content-Type-Options|X-Frame-Options|Strict-Transport-Security)"
```

---

## 📊 **Step 10: Monitoring & Alerting**

### **10.1 Key Metrics to Monitor**
- **Application Metrics**: Request rate, response time, error rate
- **Business Metrics**: Trade volume, P&L, position limits
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Security Metrics**: Failed logins, rate limit hits, anomalies

### **10.2 Critical Alerts**
```bash
# Configure alerts for:
# - High error rates (>5%)
# - Slow response times (>2s)
# - Failed trades
# - Security breaches
# - System resource exhaustion
# - Database connection issues
```

### **10.3 Dashboard URLs**
After deployment, access these dashboards:
- **Grafana**: `https://grafana.yourdomain.com`
- **Trading Overview**: Dashboard ID 1
- **System Health**: Dashboard ID 2
- **Security Monitoring**: Dashboard ID 3
- **Business Metrics**: Dashboard ID 4

---

## 🔄 **Step 11: Operational Procedures**

### **11.1 Deployment Process**
1. **Development** → Push to `main` branch
2. **Staging** → Automatic deployment and testing
3. **Production** → Manual approval required
4. **Validation** → Automated health checks
5. **Rollback** → Automatic on failure

### **11.2 Backup Procedures**
- **Database**: Daily automated backups to DigitalOcean Spaces
- **Models**: Versioned in MLflow registry
- **Configuration**: Stored in Git repository
- **Logs**: Centralized in ELK stack

### **11.3 Disaster Recovery**
```bash
# Emergency procedures documented in:
# - docs/disaster-recovery.md
# - docs/incident-response.md
# - docs/rollback-procedures.md

# RTO (Recovery Time Objective): 15 minutes
# RPO (Recovery Point Objective): 1 hour
```

---

## 🚀 **Step 12: Go Live Checklist**

### **Pre-Production Checklist**
- [ ] All tests passing (unit, integration, security)
- [ ] AI models trained and validated
- [ ] Database migrations applied
- [ ] SSL certificates configured
- [ ] Monitoring dashboards operational
- [ ] Backup procedures tested
- [ ] Security scans completed
- [ ] Load testing performed
- [ ] Disaster recovery plan reviewed

### **Go-Live Activities**
- [ ] Final production deployment
- [ ] DNS cutover to production
- [ ] Monitor system metrics
- [ ] Validate all endpoints
- [ ] Test trading functionality
- [ ] Verify AI model predictions
- [ ] Check compliance logging

### **Post-Go-Live**
- [ ] 24/7 monitoring for first week
- [ ] Daily health checks
- [ ] Weekly performance reviews
- [ ] Monthly security audits
- [ ] Quarterly disaster recovery tests

---

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Pod Startup Failures**
```bash
kubectl describe pod POD_NAME -n trading-production
kubectl logs POD_NAME -n trading-production
```

2. **Database Connection Issues**
```bash
kubectl exec -it deployment/trading-system-production -n trading-production -- \
  psql $DATABASE_URL -c "SELECT 1"
```

3. **Model Loading Failures**
```bash
kubectl logs deployment/trading-system-production -n trading-production | grep "model"
```

4. **High Memory Usage**
```bash
kubectl top pods -n trading-production
kubectl describe hpa trading-system-hpa -n trading-production
```

### **Emergency Contacts**
- **DevOps Team**: devops@yourdomain.com
- **Trading Team**: trading@yourdomain.com  
- **Security Team**: security@yourdomain.com
- **On-Call Engineer**: +1-XXX-XXX-XXXX

---

## 📈 **Performance Expectations**

### **System Performance**
- **API Response Time**: < 200ms (95th percentile)
- **WebSocket Latency**: < 50ms
- **Trade Execution**: < 100ms
- **AI Predictions**: < 500ms
- **System Uptime**: 99.9%

### **Trading Performance**
- **Maximum Positions**: 1000 concurrent
- **Order Rate**: 10,000 orders/minute  
- **Market Data**: 100,000 ticks/second
- **P&L Calculation**: Real-time updates

---

## 🔒 **Security Considerations**

### **Production Security Measures**
- ✅ **End-to-end encryption** (TLS 1.3)
- ✅ **Multi-factor authentication** required
- ✅ **Rate limiting** on all endpoints
- ✅ **Input validation** and sanitization
- ✅ **SQL injection** protection
- ✅ **CSRF protection** enabled
- ✅ **Security headers** configured
- ✅ **Regular security scans**

### **Compliance**
- ✅ **SEBI regulations** compliance
- ✅ **Audit trails** for all transactions
- ✅ **Data retention** policies
- ✅ **Risk management** controls
- ✅ **Position limits** enforcement

---

## 🎯 **Success Metrics**

### **Technical KPIs**
- Zero-downtime deployments
- Sub-second API response times
- 99.9% system availability
- Real-time AI predictions
- Comprehensive monitoring coverage

### **Business KPIs**
- Profitable trading strategies
- Risk-adjusted returns
- Regulatory compliance
- Operational efficiency
- Scalable architecture

---

**🎉 Congratulations! Your professional AI-powered trading system is now live in production, handling real money with enterprise-grade security, monitoring, and performance.**

For ongoing support and maintenance, refer to the operational runbooks in the `docs/` directory. 