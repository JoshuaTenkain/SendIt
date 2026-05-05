# SEND-IT Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Management](#database-management)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker:** 20.10+ and Docker Compose 2.0+
- **Git:** For version control
- **Node.js:** 18+ (for local frontend development)
- **Python:** 3.11+ (for local backend development)

### System Requirements

**Development:**
- CPU: 2+ cores
- RAM: 4GB minimum, 8GB recommended
- Disk: 10GB free space

**Production:**
- CPU: 4+ cores
- RAM: 8GB minimum, 16GB recommended
- Disk: 50GB+ free space
- Network: Static IP or domain name

---

## Development Setup

### Quick Start (Docker Compose)

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/send-it.git
cd send-it
```

2. **Create environment files:**

**Backend (.env):**
```bash
# Database
DATABASE_URL=postgresql://sendit:sendit123@db:5432/sendit

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
CORS_ORIGINS=http://localhost:3000

# PayFast
PAYFAST_MERCHANT_ID=10000100
PAYFAST_MERCHANT_KEY=46f0cd694581a
PAYFAST_PASSPHRASE=your-passphrase
PAYFAST_MODE=sandbox
PAYFAST_RETURN_URL=http://localhost:3000/payment/success
PAYFAST_CANCEL_URL=http://localhost:3000/payment/cancel
PAYFAST_NOTIFY_URL=http://localhost:8000/webhooks/payfast
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start all services:**
```bash
docker compose up -d
```

4. **Run database migrations:**
```bash
docker compose exec backend alembic upgrade head
```

5. **Seed test data:**
```bash
docker compose exec backend python scripts/seed_data.py
```

6. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Test Credentials

**Regular User:**
- Email: `test@send-it.local`
- Password: `pass123`

**Admin User:**
- Email: `admin@send-it.local`
- Password: `admin123`

---

## Local Development (Without Docker)

### Backend Setup

1. **Create virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup PostgreSQL:**
```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb sendit
createuser sendit -P  # Enter password: sendit123
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your local database URL
```

5. **Run migrations:**
```bash
alembic upgrade head
```

6. **Seed data:**
```bash
python scripts/seed_data.py
```

7. **Start development server:**
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env.local
# Edit .env.local if needed
```

3. **Start development server:**
```bash
npm run dev
```

---

## Production Deployment

### Option 1: Docker Compose (Simple)

1. **Prepare production environment:**
```bash
# Clone repository on server
git clone https://github.com/your-org/send-it.git
cd send-it
```

2. **Create production environment files:**

**backend/.env:**
```bash
DATABASE_URL=postgresql://sendit:STRONG_PASSWORD@db:5432/sendit
SECRET_KEY=GENERATE_STRONG_SECRET_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

CORS_ORIGINS=https://yourdomain.com

# PayFast Production
PAYFAST_MERCHANT_ID=your_merchant_id
PAYFAST_MERCHANT_KEY=your_merchant_key
PAYFAST_PASSPHRASE=your_passphrase
PAYFAST_MODE=production
PAYFAST_RETURN_URL=https://yourdomain.com/payment/success
PAYFAST_CANCEL_URL=https://yourdomain.com/payment/cancel
PAYFAST_NOTIFY_URL=https://api.yourdomain.com/webhooks/payfast
```

**frontend/.env.local:**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

3. **Update docker-compose.yml for production:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: sendit
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: sendit
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - sendit-network

  backend:
    build: ./backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    networks:
      - sendit-network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    depends_on:
      - backend
    networks:
      - sendit-network

volumes:
  postgres_data:

networks:
  sendit-network:
    driver: bridge
```

4. **Build and start services:**
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

5. **Run migrations:**
```bash
docker compose exec backend alembic upgrade head
```

6. **Setup nginx reverse proxy:**
```nginx
# /etc/nginx/sites-available/sendit

# Frontend
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

7. **Enable SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

---

### Option 2: Cloud Deployment (AWS/GCP/Azure)

#### AWS Deployment Example

**Architecture:**
- **Frontend:** AWS Amplify or S3 + CloudFront
- **Backend:** ECS Fargate or EC2
- **Database:** RDS PostgreSQL
- **Load Balancer:** Application Load Balancer

**Steps:**

1. **Create RDS PostgreSQL instance:**
```bash
aws rds create-db-instance \
    --db-instance-identifier sendit-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username sendit \
    --master-user-password YOUR_PASSWORD \
    --allocated-storage 20
```

2. **Deploy backend to ECS:**
```bash
# Build and push Docker image
docker build -t sendit-backend ./backend
docker tag sendit-backend:latest YOUR_ECR_REPO/sendit-backend:latest
docker push YOUR_ECR_REPO/sendit-backend:latest

# Create ECS task definition and service
aws ecs create-service --service-name sendit-backend ...
```

3. **Deploy frontend to Amplify:**
```bash
# Connect GitHub repository to AWS Amplify
# Configure build settings
# Deploy automatically on git push
```

---

## Environment Configuration

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `SECRET_KEY` | JWT signing key | Yes | - |
| `ALGORITHM` | JWT algorithm | No | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | No | 10080 (7 days) |
| `CORS_ORIGINS` | Allowed origins | Yes | - |
| `PAYFAST_MERCHANT_ID` | PayFast merchant ID | Yes | - |
| `PAYFAST_MERCHANT_KEY` | PayFast merchant key | Yes | - |
| `PAYFAST_PASSPHRASE` | PayFast passphrase | Yes | - |
| `PAYFAST_MODE` | sandbox/production | Yes | sandbox |
| `PAYFAST_RETURN_URL` | Payment success URL | Yes | - |
| `PAYFAST_CANCEL_URL` | Payment cancel URL | Yes | - |
| `PAYFAST_NOTIFY_URL` | Webhook URL | Yes | - |

### Frontend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes | http://localhost:8000 |

### Generating Secure Keys

**SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**PAYFAST_PASSPHRASE:**
```bash
openssl rand -base64 32
```

---

## Database Management

### Migrations

**Create new migration:**
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

### Backup & Restore

**Backup database:**
```bash
# Docker
docker compose exec db pg_dump -U sendit sendit > backup_$(date +%Y%m%d).sql

# Local
pg_dump -U sendit sendit > backup_$(date +%Y%m%d).sql
```

**Restore database:**
```bash
# Docker
docker compose exec -T db psql -U sendit sendit < backup_20240115.sql

# Local
psql -U sendit sendit < backup_20240115.sql
```

**Automated backups (cron):**
```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

**backup-script.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T db pg_dump -U sendit sendit | gzip > $BACKUP_DIR/sendit_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "sendit_*.sql.gz" -mtime +30 -delete
```

---

## Monitoring & Maintenance

### Health Checks

**Backend health endpoint:**
```bash
curl http://localhost:8000/health
```

**Database connection check:**
```bash
docker compose exec db pg_isready -U sendit
```

### Logging

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Last 100 lines
docker compose logs --tail=100 backend
```

**Log rotation (production):**
```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Performance Monitoring

**Database performance:**
```sql
-- Slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

**Application metrics:**
```bash
# Request rate
docker compose logs backend | grep "GET\|POST\|PATCH\|DELETE" | wc -l

# Error rate
docker compose logs backend | grep "ERROR" | wc -l
```

### Maintenance Tasks

**Weekly tasks:**
- Review error logs
- Check disk space
- Verify backups
- Monitor database size

**Monthly tasks:**
- Update dependencies
- Review security patches
- Optimize database (VACUUM)
- Review performance metrics

**Database optimization:**
```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE sendit;
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Symptom:** `could not connect to server`

**Solutions:**
```bash
# Check if database is running
docker compose ps db

# Check database logs
docker compose logs db

# Verify connection string
docker compose exec backend env | grep DATABASE_URL

# Test connection
docker compose exec backend python -c "from app.database import engine; engine.connect()"
```

#### 2. Migration Errors

**Symptom:** `alembic.util.exc.CommandError`

**Solutions:**
```bash
# Check current version
docker compose exec backend alembic current

# View pending migrations
docker compose exec backend alembic heads

# Force to specific version
docker compose exec backend alembic stamp head

# Rollback and retry
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

#### 3. Frontend Can't Connect to Backend

**Symptom:** `Network Error` or `CORS error`

**Solutions:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify CORS settings
docker compose exec backend env | grep CORS_ORIGINS

# Check frontend environment
docker compose exec frontend env | grep NEXT_PUBLIC_API_URL

# Restart services
docker compose restart backend frontend
```

#### 4. PayFast Webhook Not Working

**Symptom:** Payments not confirming

**Solutions:**
```bash
# Check webhook URL is accessible
curl -X POST http://your-domain.com/webhooks/payfast

# Verify PayFast configuration
docker compose exec backend env | grep PAYFAST

# Check webhook logs
docker compose logs backend | grep webhook

# Test with PayFast sandbox
# Use PayFast testing tools
```

#### 5. Out of Disk Space

**Symptom:** `No space left on device`

**Solutions:**
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up Docker
docker system prune -a --volumes

# Remove old logs
docker compose logs --tail=0 backend > /dev/null

# Check database size
docker compose exec db du -sh /var/lib/postgresql/data
```

#### 6. High Memory Usage

**Symptom:** System slowdown, OOM errors

**Solutions:**
```bash
# Check memory usage
docker stats

# Limit container memory
# In docker-compose.yml:
services:
  backend:
    mem_limit: 512m
    mem_reservation: 256m

# Restart services
docker compose restart
```

### Debug Mode

**Enable debug logging:**

**Backend:**
```python
# app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```bash
# .env.local
NEXT_PUBLIC_DEBUG=true
```

### Getting Help

1. **Check logs first:**
   ```bash
   docker compose logs -f
   ```

2. **Review documentation:**
   - API docs: http://localhost:8000/docs
   - This guide
   - README.md

3. **Common error patterns:**
   - Authentication: Check JWT token
   - Database: Check migrations
   - CORS: Verify origins
   - PayFast: Check webhook URL

4. **Contact support:**
   - GitHub Issues
   - Email: support@send-it.example.com

---

## Security Checklist

### Pre-Production

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Configure CORS properly
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Review environment variables
- [ ] Enable database encryption
- [ ] Set up backup strategy
- [ ] Configure monitoring
- [ ] Review PayFast settings
- [ ] Test payment flow
- [ ] Verify webhook security

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check SSL certificate expiry
- [ ] Review access logs
- [ ] Test disaster recovery
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance testing
- [ ] Load testing

---

## Scaling Guide

### Horizontal Scaling

**Backend:**
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

**Load Balancer (nginx):**
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

### Database Scaling

**Read Replicas:**
```python
# app/database.py
from sqlalchemy import create_engine

# Write database
write_engine = create_engine(WRITE_DATABASE_URL)

# Read replicas
read_engine = create_engine(READ_DATABASE_URL)
```

**Connection Pooling:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## Conclusion

This deployment guide covers development setup, production deployment, and operational maintenance for the SEND-IT platform. Follow the security checklist and monitoring guidelines to ensure a stable, secure production environment.

For additional support, refer to:
- [API Documentation](./API.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [User Guide](./USER_GUIDE.md)
