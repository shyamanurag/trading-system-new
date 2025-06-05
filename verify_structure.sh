#!/bin/bash

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ $1 (missing)"
    fi
}

# Function to check if a directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ $1 (missing)"
    fi
}

echo "Verifying project structure..."

# Check main directories
echo -e "\nChecking main directories:"
check_dir "trading-system"
check_dir "trading-system/src"
check_dir "trading-system/tests"
check_dir "trading-system/k8s"
check_dir "trading-system/docker"
check_dir "trading-system/scripts"
check_dir "trading-system/docs"
check_dir "trading-system/monitoring"
check_dir "trading-system/backups"
check_dir "trading-system/logs"

# Check source code directories
echo -e "\nChecking source code directories:"
check_dir "trading-system/src/core"
check_dir "trading-system/src/strategies"
check_dir "trading-system/src/utils"
check_dir "trading-system/src/api"
check_dir "trading-system/src/models"
check_dir "trading-system/src/services"
check_dir "trading-system/src/config"

# Check test directories
echo -e "\nChecking test directories:"
check_dir "trading-system/tests/unit"
check_dir "trading-system/tests/integration"
check_dir "trading-system/tests/e2e"

# Check Kubernetes files
echo -e "\nChecking Kubernetes files:"
check_file "trading-system/k8s/namespace.yaml"
check_file "trading-system/k8s/configmap.yaml"
check_file "trading-system/k8s/secrets.yaml"
check_file "trading-system/k8s/deployment.yaml"
check_file "trading-system/k8s/services.yaml"
check_file "trading-system/k8s/ingress.yaml"
check_file "trading-system/k8s/pvc.yaml"
check_file "trading-system/k8s/deploy.sh"

# Check Docker files
echo -e "\nChecking Docker files:"
check_file "trading-system/docker/Dockerfile"
check_file "trading-system/docker/docker-compose.yml"

# Check monitoring files
echo -e "\nChecking monitoring files:"
check_file "trading-system/monitoring/prometheus/prometheus.yml"
check_file "trading-system/monitoring/prometheus/alert_rules.yml"
check_file "trading-system/monitoring/grafana/dashboards.yaml"

# Check script files
echo -e "\nChecking script files:"
check_file "trading-system/scripts/backup.sh"
check_file "trading-system/scripts/restore.sh"
check_file "trading-system/scripts/health_check.sh"

# Check root files
echo -e "\nChecking root files:"
check_file "trading-system/README.md"
check_file "trading-system/requirements.txt"
check_file "trading-system/.env.example"
check_file "trading-system/.gitignore"

echo -e "\nVerification complete!" 