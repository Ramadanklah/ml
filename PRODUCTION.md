# Production Deployment Guide

## 🚀 **Production-Ready LIS System**

This guide covers the complete production deployment of the Laboratory Information System with enterprise-grade security, monitoring, and operational procedures.

## 📋 **Prerequisites**

### **System Requirements**
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **CPU**: 4+ cores (8+ recommended)
- **Memory**: 8GB+ RAM (16GB+ recommended)
- **Storage**: 50GB+ available space (100GB+ recommended)
- **Network**: Stable internet connection for updates

### **Software Requirements**
- Docker 20.10+
- Docker Compose 2.0+
- OpenSSL
- UFW or firewalld
- Systemd

### **Security Requirements**
- Root/sudo access
- Firewall configuration
- SSL certificates (Let's Encrypt or CA)
- Secure passwords for all services

## 🔒 **Security Configuration**

### **1. Environment Variables**
```bash
# Copy production environment template
cp .env.production .env

# Edit and secure all passwords
nano .env
```

**Critical Security Variables:**
- `SECRET_KEY`: Generate unique Django secret key
- `DB_PASSWORD`: Strong PostgreSQL password
- `REDIS_PASSWORD`: Strong Redis password
- `ELASTIC_PASSWORD`: Strong Elasticsearch password
- `MIRTH_ADMIN_PASSWORD`: Strong Mirth Connect password
- `GRAFANA_ADMIN_PASSWORD`: Strong Grafana password

### **2. SSL/TLS Configuration**
```bash
# Generate self-signed certificates (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
  -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# For production, use Let's Encrypt or CA certificates
sudo certbot --nginx -d your-domain.com
```

### **3. Firewall Configuration**
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 🚀 **Deployment Process**

### **1. Automated Deployment**
```bash
# Run production deployment script
sudo ./deploy-production.sh
```

The script will:
- ✅ Check system requirements
- ✅ Create necessary directories
- ✅ Generate SSL certificates
- ✅ Deploy all services
- ✅ Configure monitoring
- ✅ Set up systemd services
- ✅ Configure firewall
- ✅ Verify deployment

### **2. Manual Deployment Steps**
If you prefer manual deployment:

```bash
# Create directories
sudo mkdir -p /opt/lis/{postgres_data,redis_data,elasticsearch_data,mirth_data,backend_static,backend_media,logs,ssl}

# Set permissions
sudo chown -R 999:999 /opt/lis/postgres_data /opt/lis/redis_data /opt/lis/elasticsearch_data

# Deploy services
docker-compose -f docker-compose.production.yml up -d

# Initialize database
docker exec lis_backend_prod python manage.py migrate
docker exec lis_backend_prod python manage.py collectstatic --noinput
docker exec lis_backend_prod python manage.py createsuperuser
```

## 📊 **Monitoring & Observability**

### **1. Prometheus Metrics**
- **URL**: http://localhost:9090
- **Metrics**: System, application, and business metrics
- **Retention**: 30 days
- **Scraping**: Every 15 seconds

### **2. Grafana Dashboards**
- **URL**: http://localhost:3001
- **Login**: admin / [password from .env]
- **Dashboards**: Pre-configured LIS dashboards
- **Alerts**: Email, Slack, PagerDuty integration

### **3. Log Aggregation (ELK Stack)**
- **Elasticsearch**: Log storage and indexing
- **Logstash**: Log processing and transformation
- **Filebeat**: Log collection from containers

### **4. Health Checks**
```bash
# System health
curl http://localhost/health/

# Service health
docker-compose -f docker-compose.production.yml ps

# Database health
docker exec lis_postgres_prod pg_isready -U lis_prod_user -d lis_production
```

## 🔄 **Operational Procedures**

### **1. Service Management**
```bash
# Start all services
sudo systemctl start lis

# Stop all services
sudo systemctl stop lis

# Restart all services
sudo systemctl restart lis

# View service status
sudo systemctl status lis

# View logs
sudo journalctl -u lis -f
```

### **2. Backup Procedures**
```bash
# Manual backup
sudo systemctl start lis-backup

# View backup status
sudo systemctl status lis-backup

# Backup files location
ls -la /opt/lis/backups/
```

**Automated Backups:**
- **Schedule**: Daily at 2:00 AM
- **Retention**: 30 days
- **Compression**: Enabled
- **Encryption**: Enabled

### **3. Maintenance Procedures**
```bash
# Enter maintenance mode
docker exec lis_backend_prod python manage.py maintenance_mode on

# Exit maintenance mode
docker exec lis_backend_prod python manage.py maintenance_mode off

# View maintenance status
docker exec lis_backend_prod python manage.py maintenance_mode status
```

### **4. Scaling Operations**
```bash
# Scale Celery workers
docker-compose -f docker-compose.production.yml up -d --scale celery_worker=8

# Scale backend services
docker-compose -f docker-compose.production.yml up -d --scale backend=3
```

## 🚨 **Alerting & Incident Response**

### **1. Critical Alerts**
- **Critical Values**: Immediate notification
- **System Errors**: Immediate notification
- **Performance Issues**: Hourly notification
- **Disk Space**: Daily notification

### **2. Escalation Matrix**
| Level | Response Time | Contacts |
|-------|---------------|----------|
| 1 | 5 minutes | On-call team |
| 2 | 15 minutes | Team lead |
| 3 | 30 minutes | Manager |
| 4 | 1 hour | Director |
| 5 | 2 hours | CTO |

### **3. Alert Channels**
- **Email**: Primary notification method
- **SMS**: Critical alerts only
- **Slack**: Team collaboration
- **PagerDuty**: Escalation management

## 📈 **Performance Optimization**

### **1. Database Optimization**
```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### **2. Redis Optimization**
```bash
# Redis configuration
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### **3. Application Optimization**
```python
# Django settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://:password@localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery optimization
CELERY_WORKER_CONCURRENCY = 4
CELERY_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_ACKS_LATE = True
```

## 🔧 **Troubleshooting**

### **1. Common Issues**

**Service Won't Start:**
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs service_name

# Check resource usage
docker stats

# Check disk space
df -h
```

**Database Connection Issues:**
```bash
# Check PostgreSQL status
docker exec lis_postgres_prod pg_isready

# Check connection pool
docker exec lis_postgres_prod psql -U lis_prod_user -d lis_production -c "SELECT * FROM pg_stat_activity;"
```

**Memory Issues:**
```bash
# Check memory usage
free -h

# Check swap usage
swapon --show

# Check container memory limits
docker stats --no-stream
```

### **2. Recovery Procedures**

**Database Recovery:**
```bash
# Restore from backup
docker exec -i lis_postgres_prod psql -U lis_prod_user -d lis_production < backup_file.sql

# Point-in-time recovery
docker exec lis_postgres_prod pg_restore -U lis_prod_user -d lis_production --clean backup_file.dump
```

**Service Recovery:**
```bash
# Restart specific service
docker-compose -f docker-compose.production.yml restart service_name

# Rebuild and restart
docker-compose -f docker-compose.production.yml up -d --build service_name
```

## 📚 **Documentation & Training**

### **1. System Documentation**
- **Architecture**: System design and components
- **API**: REST API documentation
- **Workflows**: Business process documentation
- **Procedures**: Operational procedures

### **2. User Training**
- **Administrators**: System administration
- **Laboratory Staff**: Daily operations
- **Clinicians**: Result interpretation
- **IT Support**: Troubleshooting and maintenance

### **3. Compliance Documentation**
- **HIPAA**: Privacy and security compliance
- **CLIA**: Laboratory certification
- **CAP**: Accreditation requirements
- **GDPR**: Data protection compliance

## 🔄 **Updates & Maintenance**

### **1. System Updates**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Update application code
git pull origin main
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

### **2. Security Updates**
```bash
# Check for security updates
sudo apt list --upgradable | grep security

# Apply security updates
sudo apt upgrade -y

# Update Docker base images
docker-compose -f docker-compose.production.yml build --no-cache --pull
```

### **3. Maintenance Windows**
- **Schedule**: Weekly, Sunday 2:00-4:00 AM UTC
- **Notification**: 7 days in advance
- **Duration**: 2 hours maximum
- **Rollback**: Automatic if issues detected

## 📊 **Performance Monitoring**

### **1. Key Metrics**
- **Response Time**: API response times
- **Throughput**: Requests per second
- **Error Rate**: Error percentage
- **Resource Usage**: CPU, memory, disk, network

### **2. Business Metrics**
- **Sample Processing**: Samples per hour
- **Result Turnaround**: Time to result
- **User Activity**: Active users, sessions
- **System Uptime**: Availability percentage

### **3. Capacity Planning**
- **Growth Trends**: Historical data analysis
- **Resource Projection**: Future requirements
- **Scaling Triggers**: When to scale
- **Cost Optimization**: Resource efficiency

## 🚀 **High Availability**

### **1. Load Balancing**
```nginx
# Nginx load balancer configuration
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **2. Database Clustering**
```yaml
# PostgreSQL cluster configuration
services:
  postgres_master:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: lis_production
      POSTGRES_USER: lis_prod_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_master_data:/var/lib/postgresql/data
      
  postgres_replica:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: lis_production
      POSTGRES_USER: lis_prod_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
```

### **3. Disaster Recovery**
- **RPO**: 15 minutes (Recovery Point Objective)
- **RTO**: 4 hours (Recovery Time Objective)
- **Backup Strategy**: Incremental + full backups
- **Recovery Testing**: Monthly recovery drills

## 📞 **Support & Contact**

### **1. Support Levels**
- **Level 1**: Basic troubleshooting
- **Level 2**: Technical issues
- **Level 3**: Complex problems
- **Level 4**: Vendor support

### **2. Contact Information**
- **Emergency**: 24/7 on-call support
- **Technical**: tech-support@your-domain.com
- **Business**: business-support@your-domain.com
- **Vendor**: vendor-support@vendor.com

### **3. Escalation Procedures**
1. **Immediate**: Critical system failure
2. **4 Hours**: Major functionality issues
3. **24 Hours**: Minor issues
4. **72 Hours**: Enhancement requests

## 📋 **Checklist**

### **Pre-Deployment**
- [ ] System requirements verified
- [ ] Security configurations reviewed
- [ ] Environment variables secured
- [ ] SSL certificates obtained
- [ ] Firewall configured
- [ ] Backup procedures tested

### **Deployment**
- [ ] Services deployed successfully
- [ ] Database initialized
- [ ] Monitoring configured
- [ ] Health checks passed
- [ ] Performance baseline established
- [ ] Security scan completed

### **Post-Deployment**
- [ ] User training completed
- [ ] Documentation updated
- [ ] Monitoring alerts configured
- [ ] Backup procedures verified
- [ ] Disaster recovery tested
- [ ] Compliance audit passed

---

**⚠️ Important Notes:**
- Always test in staging environment first
- Keep backups before major changes
- Monitor system performance closely
- Document all changes and procedures
- Regular security audits and updates
- Compliance with healthcare regulations

**🚀 Ready for Production!**
Your LIS system is now production-ready with enterprise-grade security, monitoring, and operational procedures.