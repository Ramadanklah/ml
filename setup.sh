#!/bin/bash

# Laboratory Information System (LIS) Setup Script
# This script sets up the complete LIS development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    local missing_requirements=()
    
    # Check Docker
    if ! command_exists docker; then
        missing_requirements+=("Docker")
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose; then
        missing_requirements+=("Docker Compose")
    fi
    
    # Check Python
    if ! command_exists python3; then
        missing_requirements+=("Python 3.11+")
    fi
    
    # Check Node.js
    if ! command_exists node; then
        missing_requirements+=("Node.js 18+")
    fi
    
    # Check Git
    if ! command_exists git; then
        missing_requirements+=("Git")
    fi
    
    if [ ${#missing_requirements[@]} -ne 0 ]; then
        print_error "Missing required software:"
        for req in "${missing_requirements[@]}"; do
            echo "  - $req"
        done
        echo ""
        echo "Please install the missing software and run this script again."
        exit 1
    fi
    
    print_success "All system requirements met!"
}

# Function to create project structure
create_project_structure() {
    print_status "Creating project structure..."
    
    # Create necessary directories
    mkdir -p backend/logs
    mkdir -p backend/static
    mkdir -p backend/media
    mkdir -p backend/staticfiles
    mkdir -p frontend/src
    mkdir -p frontend/public
    mkdir -p infrastructure/nginx/conf.d
    mkdir -p infrastructure/prometheus
    mkdir -p infrastructure/grafana/provisioning/datasources
    mkdir -p infrastructure/grafana/provisioning/dashboards
    mkdir -p infrastructure/grafana/dashboards
    mkdir -p docs
    mkdir -p scripts
    mkdir -p tests
    
    print_success "Project structure created!"
}

# Function to create environment files
create_environment_files() {
    print_status "Creating environment configuration files..."
    
    # Backend environment file
    cat > backend/.env << EOF
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=lis_db
DB_USER=lis_user
DB_PASSWORD=lis_password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings
REDIS_URL=redis://localhost:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@lis-system.com

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF

    # Frontend environment file
    cat > frontend/.env << EOF
# React App Environment Variables
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=1.0.0
EOF

    print_success "Environment files created!"
}

# Function to create database initialization script
create_db_init_script() {
    print_status "Creating database initialization script..."
    
    cat > backend/scripts/init-db.sql << EOF
-- Database initialization script for LIS system
-- This script creates the initial database structure

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types if needed
-- (Django will handle most of the schema creation)

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE lis_db TO lis_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO lis_user;

-- Create indexes for better performance
-- (These will be created by Django models)

-- Insert initial data if needed
-- (This can be done through Django fixtures or management commands)
EOF

    print_success "Database initialization script created!"
}

# Function to create Nginx configuration
create_nginx_config() {
    print_status "Creating Nginx configuration..."
    
    # Main nginx.conf
    cat > infrastructure/nginx/nginx.conf << EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
    
    # Upstream servers
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    # Include server configurations
    include /etc/nginx/conf.d/*.conf;
}
EOF

    # Default server configuration
    cat > infrastructure/nginx/conf.d/default.conf << EOF
server {
    listen 80;
    server_name localhost;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Admin interface
    location /admin/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Health checks
    location /health/ {
        proxy_pass http://backend;
        access_log off;
    }
    
    # Metrics
    location /metrics/ {
        proxy_pass http://backend;
        access_log off;
    }
}
EOF

    print_success "Nginx configuration created!"
}

# Function to create Prometheus configuration
create_prometheus_config() {
    print_status "Creating Prometheus configuration..."
    
    cat > infrastructure/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'django'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics/'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
    scrape_interval: 30s
EOF

    print_success "Prometheus configuration created!"
}

# Function to create Grafana configuration
create_grafana_config() {
    print_status "Creating Grafana configuration..."
    
    # Datasource configuration
    cat > infrastructure/grafana/provisioning/datasources/datasource.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Dashboard configuration
    cat > infrastructure/grafana/provisioning/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    print_success "Grafana configuration created!"
}

# Function to create management scripts
create_management_scripts() {
    print_status "Creating management scripts..."
    
    # Database management script
    cat > scripts/manage_db.sh << 'EOF'
#!/bin/bash

# Database management script for LIS system

case "$1" in
    "reset")
        echo "Resetting database..."
        docker-compose down -v
        docker-compose up -d postgres
        sleep 10
        docker-compose exec backend python manage.py migrate
        docker-compose exec backend python manage.py createsuperuser
        ;;
    "migrate")
        echo "Running migrations..."
        docker-compose exec backend python manage.py migrate
        ;;
    "makemigrations")
        echo "Creating migrations..."
        docker-compose exec backend python manage.py makemigrations
        ;;
    "shell")
        echo "Opening Django shell..."
        docker-compose exec backend python manage.py shell
        ;;
    "createsuperuser")
        echo "Creating superuser..."
        docker-compose exec backend python manage.py createsuperuser
        ;;
    *)
        echo "Usage: $0 {reset|migrate|makemigrations|shell|createsuperuser}"
        exit 1
        ;;
esac
EOF

    # Development script
    cat > scripts/dev.sh << 'EOF'
#!/bin/bash

# Development environment management script

case "$1" in
    "start")
        echo "Starting development environment..."
        docker-compose up -d
        echo "Waiting for services to be ready..."
        sleep 30
        echo "Development environment is ready!"
        echo "Frontend: http://localhost:3000"
        echo "Backend API: http://localhost:8000/api/v1"
        echo "Admin: http://localhost:8000/admin"
        echo "Grafana: http://localhost:3001 (admin/admin)"
        echo "Prometheus: http://localhost:9090"
        echo "MailHog: http://localhost:8025"
        ;;
    "stop")
        echo "Stopping development environment..."
        docker-compose down
        ;;
    "restart")
        echo "Restarting development environment..."
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "backend-logs")
        docker-compose logs -f backend
        ;;
    "frontend-logs")
        docker-compose logs -f frontend
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|backend-logs|frontend-logs}"
        exit 1
        ;;
esac
EOF

    # Make scripts executable
    chmod +x scripts/manage_db.sh
    chmod +x scripts/dev.sh
    
    print_success "Management scripts created!"
}

# Function to create documentation
create_documentation() {
    print_status "Creating documentation..."
    
    # API documentation
    cat > docs/API.md << EOF
# LIS System API Documentation

## Overview
The Laboratory Information System (LIS) provides a comprehensive REST API for managing laboratory workflows, samples, tests, and results.

## Base URL
- Development: http://localhost:8000/api/v1
- Production: https://your-domain.com/api/v1

## Authentication
The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:
\`\`\`
Authorization: Bearer <your-jwt-token>
\`\`\`

## Endpoints

### Authentication
- POST /auth/login/ - User login
- POST /auth/logout/ - User logout
- POST /auth/refresh/ - Refresh token
- POST /auth/register/ - User registration

### Samples
- GET /samples/ - List samples
- POST /samples/ - Create sample
- GET /samples/{id}/ - Get sample details
- PUT /samples/{id}/ - Update sample
- DELETE /samples/{id}/ - Delete sample

### Tests
- GET /tests/ - List tests
- POST /tests/ - Create test
- GET /tests/{id}/ - Get test details
- PUT /tests/{id}/ - Update test
- DELETE /tests/{id}/ - Delete test

### Results
- GET /results/ - List results
- POST /results/ - Create result
- GET /results/{id}/ - Get result details
- PUT /results/{id}/ - Update result
- DELETE /results/{id}/ - Delete result

## Response Format
All API responses follow this format:
\`\`\`json
{
    "status": "success",
    "data": {...},
    "message": "Operation completed successfully"
}
\`\`\`

## Error Handling
Errors are returned with appropriate HTTP status codes and error messages:
\`\`\`json
{
    "status": "error",
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {...}
    }
}
\`\`\`

## Rate Limiting
- Anonymous users: 100 requests per hour
- Authenticated users: 1000 requests per hour

## Pagination
List endpoints support pagination with the following parameters:
- page: Page number (default: 1)
- page_size: Items per page (default: 50, max: 100)

## Filtering and Search
Most list endpoints support filtering and search:
- search: Text search across multiple fields
- filter: Field-specific filtering
- ordering: Sort results by specific fields

## WebSocket Support
Real-time updates are available via WebSocket connections:
- URL: ws://localhost:8000/ws
- Events: sample_status_change, test_result_ready, etc.
EOF

    # Development guide
    cat > docs/DEVELOPMENT.md << EOF
# LIS System Development Guide

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Initial Setup
1. Clone the repository
2. Run the setup script: \`./setup.sh\`
3. Start the development environment: \`./scripts/dev.sh start\`

### Development Workflow
1. Make changes to the code
2. Tests will run automatically in some containers
3. Use \`./scripts/dev.sh restart\` to restart services if needed
4. Check logs with \`./scripts/dev.sh logs\`

### Database Management
- Reset database: \`./scripts/manage_db.sh reset\`
- Run migrations: \`./scripts/manage_db.sh migrate\`
- Create superuser: \`./scripts/manage_db.sh createsuperuser\`

### Testing
- Backend tests: \`docker-compose exec backend python manage.py test\`
- Frontend tests: \`docker-compose exec frontend npm test\`

### Code Quality
- Backend linting: \`docker-compose exec backend flake8\`
- Frontend linting: \`docker-compose exec frontend npm run lint\`
- Frontend formatting: \`docker-compose exec frontend npm run format\`

## Architecture

### Backend (Django)
- Django 4.2+ with Django REST Framework
- PostgreSQL database
- Redis for caching and Celery
- Elasticsearch for search
- JWT authentication

### Frontend (React)
- React 18+ with TypeScript
- Material-UI components
- Redux Toolkit for state management
- React Query for data fetching
- Chart.js for visualizations

### Infrastructure
- Docker containers for all services
- Nginx reverse proxy
- Prometheus monitoring
- Grafana dashboards

## Development Tips

### Hot Reloading
- Backend: Django development server with auto-reload
- Frontend: React development server with hot reloading

### Debugging
- Backend: Use Django debug toolbar and logging
- Frontend: Use React DevTools and browser console
- Database: Connect to PostgreSQL container directly

### Performance
- Use Django Debug Toolbar to identify slow queries
- Monitor memory usage in containers
- Check Prometheus metrics for system performance

## Deployment

### Production Setup
1. Update environment variables
2. Build production images
3. Configure SSL certificates
4. Set up monitoring and alerting
5. Configure backup strategies

### Environment Variables
- SECRET_KEY: Django secret key
- DEBUG: Set to False in production
- Database credentials
- Redis configuration
- Email settings
- Security settings
EOF

    print_success "Documentation created!"
}

# Function to create initial data fixtures
create_fixtures() {
    print_status "Creating initial data fixtures..."
    
    # Create fixtures directory
    mkdir -p backend/fixtures
    
    # Sample types fixture
    cat > backend/fixtures/sample_types.json << EOF
[
    {
        "model": "samples.sampletype",
        "pk": "550e8400-e29b-41d4-a716-446655440001",
        "fields": {
            "name": "Whole Blood",
            "code": "WB",
            "description": "Whole blood sample collected via venipuncture",
            "collection_method": "VENIPUNCTURE",
            "processing_type": "ROUTINE",
            "required_volume": "3-5 mL",
            "minimum_volume": "2 mL",
            "container_type": "Vacutainer",
            "container_color": "Red",
            "additives": ["EDTA", "Heparin"],
            "special_handling": "Store at 4°C",
            "hazardous": false,
            "biohazard_level": "BSL-1"
        }
    },
    {
        "model": "samples.sampletype",
        "pk": "550e8400-e29b-41d4-a716-446655440002",
        "fields": {
            "name": "Serum",
            "code": "SER",
            "description": "Serum sample for chemistry tests",
            "collection_method": "VENIPUNCTURE",
            "processing_type": "ROUTINE",
            "required_volume": "2-3 mL",
            "minimum_volume": "1 mL",
            "container_type": "Vacutainer",
            "container_color": "Red",
            "additives": [],
            "special_handling": "Allow to clot, centrifuge, separate serum",
            "hazardous": false,
            "biohazard_level": "BSL-1"
        }
    },
    {
        "model": "samples.sampletype",
        "pk": "550e8400-e29b-41d4-a716-446655440003",
        "fields": {
            "name": "Urine",
            "code": "UR",
            "description": "Random urine sample",
            "collection_method": "URINE_COLLECTION",
            "processing_type": "ROUTINE",
            "required_volume": "10-20 mL",
            "minimum_volume": "5 mL",
            "container_type": "Urine Cup",
            "container_color": "Clear",
            "additives": [],
            "special_handling": "Store at 4°C, test within 2 hours",
            "hazardous": false,
            "biohazard_level": "BSL-1"
        }
    }
]
EOF

    # Test categories fixture
    cat > backend/fixtures/test_categories.json << EOF
[
    {
        "model": "tests.testcategory",
        "pk": "660e8400-e29b-41d4-a716-446655440001",
        "fields": {
            "name": "Chemistry",
            "code": "CHEM",
            "description": "Clinical chemistry tests",
            "display_order": 1,
            "is_active": true,
            "icon": "science"
        }
    },
    {
        "model": "tests.testcategory",
        "pk": "660e8400-e29b-41d4-a716-446655440002",
        "fields": {
            "name": "Hematology",
            "code": "HEMA",
            "description": "Blood cell analysis",
            "display_order": 2,
            "is_active": true,
            "icon": "bloodtype"
        }
    },
    {
        "model": "tests.testcategory",
        "pk": "660e8400-e29b-41d4-a716-446655440003",
        "fields": {
            "name": "Immunology",
            "code": "IMMU",
            "description": "Immune system tests",
            "display_order": 3,
            "is_active": true,
            "icon": "immune"
        }
    }
]
EOF

    print_success "Initial data fixtures created!"
}

# Function to create Celery configuration
create_celery_config() {
    print_status "Creating Celery configuration..."
    
    cat > backend/lis_project/celery.py << EOF
"""
Celery configuration for LIS project.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lis_project.settings')

app = Celery('lis_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
EOF

    print_success "Celery configuration created!"
}

# Function to create WSGI configuration
create_wsgi_config() {
    print_status "Creating WSGI configuration..."
    
    cat > backend/lis_project/wsgi.py << EOF
"""
WSGI config for LIS project.

It exposes the WSGI callable as a module-level variable named \`application\`.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lis_project.settings')

application = get_wsgi_application()
EOF

    print_success "WSGI configuration created!"
}

# Function to create ASGI configuration
create_asgi_config() {
    print_status "Creating ASGI configuration..."
    
    cat > backend/lis_project/asgi.py << EOF
"""
ASGI config for LIS project.

It exposes the ASGI callable as a module-level variable named \`application\`.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lis_project.settings')

application = get_asgi_application()
EOF

    print_success "ASGI configuration created!"
}

# Function to create manage.py
create_manage_py() {
    print_status "Creating manage.py..."
    
    cat > backend/manage.py << EOF
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lis_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
EOF

    chmod +x backend/manage.py
    
    print_success "manage.py created!"
}

# Function to create app configuration files
create_app_configs() {
    print_status "Creating app configuration files..."
    
    # Users app config
    cat > backend/users/apps.py << EOF
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'User Management'
EOF

    # Samples app config
    cat > backend/samples/apps.py << EOF
from django.apps import AppConfig


class SamplesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'samples'
    verbose_name = 'Sample Management'
EOF

    # Tests app config
    cat > backend/tests/apps.py << EOF
from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests'
    verbose_name = 'Test Management'
EOF

    # Results app config
    cat > backend/results/apps.py << EOF
from django.apps import AppConfig


class ResultsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'results'
    verbose_name = 'Test Results'
EOF

    # Reports app config
    cat > backend/reports/apps.py << EOF
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'
    verbose_name = 'Reporting System'
EOF

    # Workflows app config
    cat > backend/workflows/apps.py << EOF
from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflows'
    verbose_name = 'Workflow Management'
EOF

    # Analytics app config
    cat > backend/analytics/apps.py << EOF
from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    verbose_name = 'Analytics and Reporting'
EOF

    print_success "App configuration files created!"
}

# Function to create __init__.py files
create_init_files() {
    print_status "Creating __init__.py files..."
    
    touch backend/users/__init__.py
    touch backend/samples/__init__.py
    touch backend/tests/__init__.py
    touch backend/results/__init__.py
    touch backend/reports/__init__.py
    touch backend/workflows/__init__.py
    touch backend/analytics/__init__.py
    
    print_success "__init__.py files created!"
}

# Function to create production settings
create_production_settings() {
    print_status "Creating production settings..."
    
    cat > backend/lis_project/settings_production.py << EOF
"""
Production settings for LIS project.
"""

from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Production secret key should be set via environment variable
SECRET_KEY = os.environ.get('SECRET_KEY')

# Production hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
EOF

    print_success "Production settings created!"
}

# Main setup function
main() {
    echo "=========================================="
    echo "  Laboratory Information System Setup"
    echo "=========================================="
    echo ""
    
    # Check requirements
    check_requirements
    
    # Create project structure
    create_project_structure
    
    # Create configuration files
    create_environment_files
    create_db_init_script
    create_nginx_config
    create_prometheus_config
    create_grafana_config
    
    # Create management scripts
    create_management_scripts
    
    # Create documentation
    create_documentation
    
    # Create initial data
    create_fixtures
    
    # Create Django configuration files
    create_celery_config
    create_wsgi_config
    create_asgi_config
    create_manage_py
    create_app_configs
    create_init_files
    create_production_settings
    
    echo ""
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Start the development environment:"
    echo "   ./scripts/dev.sh start"
    echo ""
    echo "2. Initialize the database:"
    echo "   ./scripts/manage_db.sh reset"
    echo ""
    echo "3. Access the system:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8000/api/v1"
    echo "   - Admin: http://localhost:8000/admin"
    echo "   - Grafana: http://localhost:3001 (admin/admin)"
    echo "   - Prometheus: http://localhost:9090"
    echo ""
    echo "4. Check the documentation in the docs/ folder"
    echo ""
    echo "Happy coding! 🧪🔬"
}

# Run main function
main "$@"