# 🚀 LIS System Quick Start Guide

## ⚡ Get Up and Running in 5 Minutes

### 1. Prerequisites Check
Make sure you have the following installed:
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### 2. Setup the System
```bash
# Run the automated setup script
./setup.sh
```

This will create all necessary files, configurations, and project structure.

### 3. Start the Development Environment
```bash
# Start all services
./scripts/dev.sh start
```

Wait about 30 seconds for all services to be ready.

### 4. Initialize the Database
```bash
# Reset and initialize the database
./scripts/manage_db.sh reset
```

This will:
- Create the database schema
- Run migrations
- Create a superuser account

### 5. Access Your LIS System

🎯 **Main Application**: http://localhost:3000
🔧 **Backend API**: http://localhost:8000/api/v1
👨‍💼 **Admin Panel**: http://localhost:8000/admin
📊 **Grafana Dashboards**: http://localhost:3001 (admin/admin)
📈 **Prometheus Metrics**: http://localhost:9090
📧 **Email Testing**: http://localhost:8025

---

## 🛠️ Development Commands

### Start/Stop Services
```bash
./scripts/dev.sh start      # Start all services
./scripts/dev.sh stop       # Stop all services
./scripts/dev.sh restart    # Restart all services
./scripts/dev.sh logs       # View all logs
```

### Database Management
```bash
./scripts/manage_db.sh migrate          # Run migrations
./scripts/manage_db.sh makemigrations   # Create new migrations
./scripts/manage_db.sh shell            # Open Django shell
./scripts/manage_db.sh createsuperuser  # Create admin user
```

### Frontend Development
```bash
# Access the frontend container
docker-compose exec frontend bash

# Run tests
npm test

# Build for production
npm run build
```

### Backend Development
```bash
# Access the backend container
docker-compose exec backend bash

# Run tests
python manage.py test

# Create new app
python manage.py startapp myapp
```

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Django Backend │    │  PostgreSQL DB  │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Redis Cache   │    │ Elasticsearch   │
│   (Port 80)     │    │   (Port 6379)   │    │  (Port 9200)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔑 Default Credentials

- **Grafana**: admin / admin
- **PostgreSQL**: lis_user / lis_password
- **Redis**: (no auth in dev, password: redis_password in prod)

---

## 📱 Key Features Available

✅ **User Management** - Role-based access control
✅ **Sample Management** - Track samples through the lab
✅ **Test Management** - Define and manage laboratory tests
✅ **Result Management** - Store and validate test results
✅ **Quality Control** - QC procedures and monitoring
✅ **Reporting** - Generate lab reports
✅ **Analytics** - Lab performance metrics
✅ **Workflow Engine** - Automated lab processes

---

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check if ports are in use
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Restart Docker
sudo systemctl restart docker
```

**Database connection errors:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres
```

**Frontend not loading:**
```bash
# Check frontend logs
./scripts/dev.sh frontend-logs

# Rebuild frontend
docker-compose restart frontend
```

**Backend errors:**
```bash
# Check backend logs
./scripts/dev.sh backend-logs

# Run migrations
./scripts/manage_db.sh migrate
```

---

## 📚 Next Steps

1. **Explore the Admin Panel** - Add sample types, tests, and users
2. **Check the API Documentation** - Visit http://localhost:8000/api/schema/swagger-ui/
3. **Review the Code** - Start with `backend/samples/models.py` for sample management
4. **Customize the System** - Modify models, add new features
5. **Deploy to Production** - Update environment variables and security settings

---

## 🆘 Need Help?

- 📖 **Documentation**: Check the `docs/` folder
- 🐛 **Issues**: Create an issue in the repository
- 💬 **Questions**: Review the code comments and docstrings

---

**Happy Laboratory Management! 🧪🔬**