#!/bin/bash

# Create main project directory
mkdir -p trading-system

# Create source code directories
mkdir -p trading-system/src/{core,strategies,utils,api,models,services,config}

# Create test directories
mkdir -p trading-system/tests/{unit,integration,e2e}

# Create deployment directories
mkdir -p trading-system/k8s
mkdir -p trading-system/docker
mkdir -p trading-system/scripts

# Create documentation directory
mkdir -p trading-system/docs

# Create monitoring directory
mkdir -p trading-system/monitoring/{prometheus,grafana}

# Create backup directory
mkdir -p trading-system/backups

# Create logs directory
mkdir -p trading-system/logs

# Move Kubernetes files to k8s directory
mv k8s/*.yaml trading-system/k8s/
mv k8s/deploy.sh trading-system/k8s/

# Create necessary empty files
touch trading-system/README.md
touch trading-system/requirements.txt
touch trading-system/.env.example
touch trading-system/.gitignore

# Create Docker files
touch trading-system/docker/Dockerfile
touch trading-system/docker/docker-compose.yml

# Create monitoring configuration files
touch trading-system/monitoring/prometheus/prometheus.yml
touch trading-system/monitoring/prometheus/alert_rules.yml
touch trading-system/monitoring/grafana/dashboards.yaml

# Create script files
touch trading-system/scripts/backup.sh
touch trading-system/scripts/restore.sh
touch trading-system/scripts/health_check.sh

# Set permissions
chmod +x trading-system/k8s/deploy.sh
chmod +x trading-system/scripts/*.sh

echo "Directory structure created successfully!"
echo "Project structure:"
tree trading-system 