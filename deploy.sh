#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
for cmd in docker docker-compose curl; do
    if ! command_exists $cmd; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Function to check system health
check_health() {
    echo "Checking system health..."
    curl -f http://localhost:8000/health || {
        echo "Error: System health check failed"
        exit 1
    }
}

# Function to backup data
backup_data() {
    echo "Creating backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backups/backup_$timestamp"
    mkdir -p "$backup_dir"
    
    # Backup database
    docker-compose exec db pg_dump -U postgres trading > "$backup_dir/db_backup.sql"
    
    # Backup Redis
    docker-compose exec redis redis-cli SAVE
    docker cp $(docker-compose ps -q redis):/data/dump.rdb "$backup_dir/redis_backup.rdb"
    
    echo "Backup created in $backup_dir"
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        echo "Error: Backup directory not specified"
        exit 1
    fi
    
    echo "Restoring from backup $1..."
    
    # Restore database
    if [ -f "$1/db_backup.sql" ]; then
        docker-compose exec -T db psql -U postgres trading < "$1/db_backup.sql"
    fi
    
    # Restore Redis
    if [ -f "$1/redis_backup.rdb" ]; then
        docker cp "$1/redis_backup.rdb" $(docker-compose ps -q redis):/data/dump.rdb
        docker-compose exec redis redis-cli BGREWRITEAOF
    fi
    
    echo "Restore completed"
}

# Function to deploy
deploy() {
    echo "Starting deployment..."
    
    # Pull latest changes
    git pull origin main
    
    # Build and start services
    docker-compose build
    docker-compose up -d
    
    # Wait for services to be ready
    echo "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    check_health
    
    echo "Deployment completed successfully"
}

# Function to rollback
rollback() {
    echo "Starting rollback..."
    
    # Stop services
    docker-compose down
    
    # Restore from latest backup
    latest_backup=$(ls -td backups/backup_* | head -1)
    if [ -n "$latest_backup" ]; then
        restore_data "$latest_backup"
    else
        echo "Error: No backup found"
        exit 1
    fi
    
    # Start services
    docker-compose up -d
    
    echo "Rollback completed"
}

# Main script
case "$1" in
    "deploy")
        backup_data
        deploy
        ;;
    "rollback")
        rollback
        ;;
    "backup")
        backup_data
        ;;
    "restore")
        restore_data "$2"
        ;;
    "health")
        check_health
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|backup|restore|health}"
        exit 1
        ;;
esac 