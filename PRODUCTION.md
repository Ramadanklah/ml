# LIS SaaS Platform - Production Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the LIS (Laboratory Information System) SaaS platform to production. The platform has been transformed into a German-compliant multi-tenant SaaS solution with integrated billing and analyzer integrations.

## Architecture

The production deployment consists of the following components:

- **Django Backend**: Multi-tenant SaaS application with German compliance
- **PostgreSQL Database**: Multi-tenant database with django-tenants
- **Redis**: Caching and message broker for Celery
- **Celery**: Background task processing
- **Nginx**: Reverse proxy and static file serving
- **Frontend**: React/Vue.js application
- **Monitoring**: Prometheus and Grafana
- **SSL/TLS**: Secure communication

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ or CentOS 8+
- **CPU**: 4+ cores
- **RAM**: 8GB+ (16GB recommended)
- **Storage**: 100GB+ SSD
- **Network**: Public IP with DNS configured

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (Let's Encrypt or commercial)

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd lis-saas-platform
```

### 2. Configure Environment Variables

Copy the production environment file and customize it:

```bash
cp .env.production .env
nano .env
```

**Important**: Update the following critical values:
- `SECRET_KEY`: Generate a strong secret key
- `DB_PASSWORD`: Strong database password
- `REDIS_PASSWORD`: Strong Redis password
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`: SMTP credentials
- `ALLOWED_HOSTS`: Your domain names
- `CORS_ALLOWED_ORIGINS`: Your frontend URLs

### 3. Generate Secret Key

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to project directory
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chown -R $USER:$USER ssl/
```

#### Option B: Commercial SSL Certificate

Place your SSL certificate files in the `ssl/` directory:
- `ssl/fullchain.pem`
- `ssl/privkey.pem`

### 5. Create Required Directories

```bash
mkdir -p logs/nginx
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
```

### 6. Database Initialization

Create the database initialization script:

```bash
cat > backend/init-db.sh << 'EOF'
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOSQL
EOF

chmod +x backend/init-db.sh
```

### 7. Deploy Application

```bash
# Build and start services
docker-compose -f docker-compose.production.yml up -d --build

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### 8. Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### 9. Create Initial Tenant

```bash
# Access Django shell
docker-compose -f docker-compose.production.yml exec backend python manage.py shell

# Create tenant (in Django shell)
from tenants.models import Tenant, Domain
from datetime import date, timedelta

tenant = Tenant.objects.create(
    name="Default Organization",
    paid_until=date.today() + timedelta(days=30),
    on_trial=True
)

domain = Domain.objects.create(
    domain="yourdomain.com",
    tenant=tenant,
    is_primary=True
)

print(f"Tenant created: {tenant.name}")
print(f"Domain created: {domain.domain}")
exit()
```

## Configuration

### Nginx Configuration

The production deployment includes Nginx as a reverse proxy. Ensure your domain points to the server's IP address.

### Database Backup

Set up automated database backups:

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.production.yml exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### Monitoring Setup

Access monitoring dashboards:
- **Prometheus**: http://yourdomain.com:9090
- **Grafana**: http://yourdomain.com:3001 (admin/admin)

## Security Considerations

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
```

### 3. Security Headers

The application includes security headers:
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection

## Performance Optimization

### 1. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_tenant_name ON tenants_tenant(name);
CREATE INDEX CONCURRENTLY idx_subscription_user ON billing_subscription(user_id);
CREATE INDEX CONCURRENTLY idx_usage_date ON billing_usage(date);
```

### 2. Caching Strategy

- Redis caching for database queries
- Static file caching via Nginx
- API response caching

### 3. Load Balancing

For high-traffic deployments, consider:
- Multiple backend instances
- Load balancer (HAProxy, Nginx Plus)
- Database read replicas

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check database status
docker-compose -f docker-compose.production.yml exec db pg_isready -U $DB_USER

# View database logs
docker-compose -f docker-compose.production.yml logs db
```

#### 2. Redis Connection Issues

```bash
# Test Redis connection
docker-compose -f docker-compose.production.yml exec redis redis-cli ping

# Check Redis logs
docker-compose -f docker-compose.production.yml logs redis
```

#### 3. Static Files Not Loading

```bash
# Recollect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput

# Check Nginx configuration
docker-compose -f docker-compose.production.yml exec nginx nginx -t
```

### Log Analysis

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f backend

# View Nginx logs
docker-compose -f docker-compose.production.yml logs -f nginx

# View database logs
docker-compose -f docker-compose.production.yml logs -f db
```

## Maintenance

### Regular Tasks

1. **Daily**: Monitor application health and logs
2. **Weekly**: Review security logs and performance metrics
3. **Monthly**: Update dependencies and security patches
4. **Quarterly**: Review and optimize database performance

### Backup Verification

```bash
# Test database restore
docker-compose -f docker-compose.production.yml exec db psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM tenants_tenant;"
```

## Support

For production support:
- Monitor application metrics via Grafana
- Set up alerting for critical issues
- Maintain regular backup schedules
- Document any custom configurations

## Compliance Notes

The platform includes German healthcare compliance features:
- **LDT 3.2.19**: KBV Laboratory Data Transfer Standard
- **ICD-10-GM**: German Modification of ICD-10
- **OPS**: German Operation and Procedure Classification
- **EBM/GOÄ**: German Medical Fee Schedules

Ensure all compliance requirements are met for your specific use case.