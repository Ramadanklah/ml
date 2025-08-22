#!/bin/bash

# Production Deployment Script for LIS System
# This script handles the complete production deployment process

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
BACKUP_DIR="/opt/lis/backups"
LOG_DIR="/opt/lis/logs"
DEPLOYMENT_LOG="$LOG_DIR/deployment-$(date +%Y%m%d-%H%M%S).log"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root for production deployment"
    fi
}

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        error "Unsupported operating system"
    fi
    
    # Check available memory (minimum 8GB)
    local mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local mem_gb=$((mem_total / 1024 / 1024))
    if [[ $mem_gb -lt 8 ]]; then
        error "Insufficient memory. Required: 8GB, Available: ${mem_gb}GB"
    fi
    
    # Check available disk space (minimum 50GB)
    local disk_space=$(df / | tail -1 | awk '{print $4}')
    local disk_gb=$((disk_space / 1024 / 1024))
    if [[ $disk_space -lt 52428800 ]]; then
        error "Insufficient disk space. Required: 50GB, Available: ${disk_gb}GB"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    log "System requirements check passed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    local dirs=(
        "/opt/lis"
        "/opt/lis/postgres_data"
        "/opt/lis/redis_data"
        "/opt/lis/elasticsearch_data"
        "/opt/lis/mirth_data"
        "/opt/lis/mirth_logs"
        "/opt/lis/backend_static"
        "/opt/lis/backend_media"
        "/opt/lis/backend_logs"
        "/opt/lis/frontend_logs"
        "/opt/lis/nginx_logs"
        "/opt/lis/prometheus_data"
        "/opt/lis/grafana_data"
        "/opt/lis/alertmanager_data"
        "/opt/lis/logstash_data"
        "/opt/lis/backup_data"
        "/opt/lis/backups"
        "/opt/lis/logs"
        "/opt/lis/certs"
        "/opt/lis/ssl"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            chmod 750 "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Set proper ownership
    chown -R 999:999 /opt/lis/postgres_data
    chown -R 999:999 /opt/lis/redis_data
    chown -R 999:999 /opt/lis/elasticsearch_data
    chown -R 999:999 /opt/lis/mirth_data
    chown -R 999:999 /opt/lis/mirth_logs
    chown -R 999:999 /opt/lis/backend_static
    chown -R 999:999 /opt/lis/backend_media
    chown -R 999:999 /opt/lis/backend_logs
    chown -R 999:999 /opt/lis/frontend_logs
    chown -R 999:999 /opt/lis/nginx_logs
    chown -R 999:999 /opt/lis/prometheus_data
    chown -R 999:999 /opt/lis/grafana_data
    chown -R 999:999 /opt/lis/alertmanager_data
    chown -R 999:999 /opt/lis/logstash_data
    chown -R 999:999 /opt/lis/backup_data
}

# Check environment file
check_environment() {
    log "Checking environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
    fi
    
    # Check required variables
    local required_vars=(
        "SECRET_KEY"
        "DB_PASSWORD"
        "REDIS_PASSWORD"
        "ELASTIC_PASSWORD"
        "MIRTH_ADMIN_PASSWORD"
        "GRAFANA_ADMIN_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            error "Required environment variable not set: $var"
        fi
        
        local value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2)
        if [[ "$value" == "your-*" ]] || [[ -z "$value" ]]; then
            error "Environment variable $var has default/empty value"
        fi
    done
    
    log "Environment configuration check passed"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log "Generating SSL certificates..."
    
    local ssl_dir="/opt/lis/ssl"
    local cert_file="$ssl_dir/cert.pem"
    local key_file="$ssl_dir/key.pem"
    
    if [[ ! -f "$cert_file" ]] || [[ ! -f "$key_file" ]]; then
        # Generate self-signed certificate for development
        # In production, you should use proper certificates from a CA
        openssl req -x509 -newkey rsa:4096 -keyout "$key_file" -out "$cert_file" \
            -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        chmod 600 "$key_file"
        chmod 644 "$cert_file"
        log "Generated self-signed SSL certificates"
    else
        log "SSL certificates already exist"
    fi
}

# Create database backup
create_backup() {
    log "Creating database backup..."
    
    local backup_file="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).sql"
    
    # Check if PostgreSQL is running
    if docker ps --format "table {{.Names}}" | grep -q "lis_postgres"; then
        docker exec lis_postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$backup_file"
        log "Database backup created: $backup_file"
    else
        warn "PostgreSQL not running, skipping backup"
    fi
}

# Stop existing services
stop_services() {
    log "Stopping existing services..."
    
    cd "$PROJECT_DIR"
    
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose down --remove-orphans || true
    fi
    
    if [[ -f "docker-compose.production.yml" ]]; then
        docker-compose -f docker-compose.production.yml down --remove-orphans || true
    fi
    
    # Stop any remaining containers
    docker stop $(docker ps -q --filter "name=lis_") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=lis_") 2>/dev/null || true
    
    log "Services stopped"
}

# Clean up old images and volumes
cleanup_docker() {
    log "Cleaning up Docker resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    log "Docker cleanup completed"
}

# Build and start production services
deploy_services() {
    log "Deploying production services..."
    
    cd "$PROJECT_DIR"
    
    # Build images
    log "Building Docker images..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Start services
    log "Starting production services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f docker-compose.production.yml ps | grep -q "healthy"; then
            log "All services are healthy"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Services failed to become healthy after $max_attempts attempts"
        fi
        
        log "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Wait for PostgreSQL to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker exec lis_postgres_prod pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "PostgreSQL failed to become ready after $max_attempts attempts"
        fi
        
        log "Waiting for PostgreSQL to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Run migrations
    log "Running database migrations..."
    docker exec lis_backend_prod python manage.py migrate --noinput
    
    # Collect static files
    log "Collecting static files..."
    docker exec lis_backend_prod python manage.py collectstatic --noinput
    
    # Create superuser if it doesn't exist
    log "Checking for superuser..."
    if ! docker exec lis_backend_prod python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found')
    exit(1)
else:
    print('Superuser exists')
    exit(0)
" 2>/dev/null; then
        log "Creating superuser..."
        docker exec -it lis_backend_prod python manage.py createsuperuser
    fi
    
    log "Database initialization completed"
}

# Configure monitoring
configure_monitoring() {
    log "Configuring monitoring..."
    
    # Wait for Prometheus to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            warn "Prometheus health check failed, continuing anyway"
            break
        fi
        
        log "Waiting for Prometheus to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Wait for Grafana to be ready
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:3001/api/health >/dev/null 2>&1; then
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            warn "Grafana health check failed, continuing anyway"
            break
        fi
        
        log "Waiting for Grafana to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    log "Monitoring configuration completed"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        # Allow SSH
        ufw allow ssh
        
        # Allow HTTP and HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # Allow monitoring ports (only from localhost)
        ufw allow from 127.0.0.1 to any port 9090  # Prometheus
        ufw allow from 127.0.0.1 to any port 3001  # Grafana
        ufw allow from 127.0.0.1 to any port 9093  # Alertmanager
        
        # Enable firewall
        ufw --force enable
        
        log "Firewall configured with ufw"
    elif command -v firewall-cmd &> /dev/null; then
        # Configure firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        
        # Reload firewall
        firewall-cmd --reload
        
        log "Firewall configured with firewalld"
    else
        warn "No supported firewall found, manual configuration required"
    fi
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/lis << EOF
/opt/lis/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker exec lis_nginx_prod nginx -s reload >/dev/null 2>&1 || true
    endscript
}

/opt/lis/backend_logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 999 999
}

/opt/lis/mirth_logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 999 999
}
EOF
    
    log "Log rotation configured"
}

# Setup systemd services
setup_systemd_services() {
    log "Setting up systemd services..."
    
    # Create systemd service for LIS
    cat > /etc/systemd/system/lis.service << EOF
[Unit]
Description=LIS Production System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.production.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.production.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    # Create systemd service for backup
    cat > /etc/systemd/system/lis-backup.service << EOF
[Unit]
Description=LIS Backup Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=$PROJECT_DIR
ExecStart=$SCRIPT_DIR/backup.sh
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF
    
    # Create systemd timer for backup
    cat > /etc/systemd/system/lis-backup.timer << EOF
[Unit]
Description=Run LIS backup daily
Requires=lis-backup.service

[Timer]
OnCalendar=02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable lis.service
    systemctl enable lis-backup.timer
    
    log "Systemd services configured"
}

# Setup cron jobs
setup_cron_jobs() {
    log "Setting up cron jobs..."
    
    # Add maintenance cron job
    (crontab -l 2>/dev/null; echo "0 2 * * 0 $SCRIPT_DIR/maintenance.sh") | crontab -
    
    # Add log cleanup cron job
    (crontab -l 2>/dev/null; echo "0 3 * * 0 $SCRIPT_DIR/cleanup-logs.sh") | crontab -
    
    log "Cron jobs configured"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check if all services are running
    local services=(
        "lis_postgres_prod"
        "lis_redis_prod"
        "lis_elasticsearch_prod"
        "lis_mirth_prod"
        "lis_backend_prod"
        "lis_celery_worker_prod"
        "lis_celery_beat_prod"
        "lis_frontend_prod"
        "lis_nginx_prod"
        "lis_prometheus_prod"
        "lis_grafana_prod"
    )
    
    for service in "${services[@]}"; do
        if ! docker ps --format "table {{.Names}}" | grep -q "$service"; then
            error "Service $service is not running"
        fi
    done
    
    # Check service health
    log "Checking service health..."
    
    # Check backend health
    if ! curl -s http://localhost:8000/health/ >/dev/null; then
        error "Backend health check failed"
    fi
    
    # Check frontend
    if ! curl -s http://localhost:3000/ >/dev/null; then
        error "Frontend health check failed"
    fi
    
    # Check nginx
    if ! curl -s http://localhost/ >/dev/null; then
        error "Nginx health check failed"
    fi
    
    log "All services are running and healthy"
}

# Display deployment information
display_deployment_info() {
    log "Deployment completed successfully!"
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    LIS Production System Deployed    ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Main Application: ${GREEN}http://localhost${NC}"
    echo -e "  API Documentation: ${GREEN}http://localhost/api/schema/swagger-ui/${NC}"
    echo -e "  Admin Interface: ${GREEN}http://localhost:8000/admin${NC}"
    echo -e "  Grafana Dashboards: ${GREEN}http://localhost:3001${NC}"
    echo -e "  Prometheus: ${GREEN}http://localhost:9090${NC}"
    echo -e "  Mirth Connect: ${GREEN}http://localhost:8080${NC}"
    echo
    echo -e "${BLUE}Default Credentials:${NC}"
    echo -e "  Grafana: admin / ${YELLOW}[password from .env file]${NC}"
    echo -e "  Mirth Connect: admin / ${YELLOW}[password from .env file]${NC}"
    echo
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Change default passwords"
    echo -e "  2. Configure SSL certificates"
    echo -e "  3. Set up monitoring alerts"
    echo -e "  4. Configure backup schedules"
    echo -e "  5. Test critical workflows"
    echo
    echo -e "${BLUE}Log Files:${NC}"
    echo -e "  Deployment Log: ${GREEN}$DEPLOYMENT_LOG${NC}"
    echo -e "  Application Logs: ${GREEN}/opt/lis/logs${NC}"
    echo
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  View logs: ${GREEN}docker-compose -f docker-compose.production.yml logs -f${NC}"
    echo -e "  Restart services: ${GREEN}systemctl restart lis${NC}"
    echo -e "  Manual backup: ${GREEN}systemctl start lis-backup${NC}"
    echo
}

# Main deployment function
main() {
    log "Starting LIS production deployment..."
    
    # Check prerequisites
    check_root
    check_system_requirements
    check_environment
    
    # Create backup
    create_backup
    
    # Prepare system
    create_directories
    generate_ssl_certificates
    
    # Stop existing services
    stop_services
    cleanup_docker
    
    # Deploy
    deploy_services
    initialize_database
    configure_monitoring
    
    # Configure system
    configure_firewall
    setup_log_rotation
    setup_systemd_services
    setup_cron_jobs
    
    # Verify
    verify_deployment
    
    # Display information
    display_deployment_info
    
    log "Deployment completed successfully!"
}

# Run main function
main "$@"