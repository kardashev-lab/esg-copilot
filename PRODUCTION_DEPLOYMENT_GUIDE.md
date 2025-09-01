# Reggie - AI Regulations Co-Pilot - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Reggie - AI Regulations Co-Pilot application to production environments.

## 🚀 Quick Production Deployment

### Prerequisites

1. **System Requirements**
   - Docker 20.10+ and Docker Compose 2.0+
   - 4GB+ RAM, 2+ CPU cores
   - 20GB+ disk space
   - Ubuntu 20.04+ or similar Linux distribution

2. **Required Services**
   - Domain name with DNS configured
   - SSL certificate (recommended: Let's Encrypt)
   - OpenAI API key

### One-Command Deployment

```bash
# Clone and deploy
git clone <repository-url>
cd new-esg-copilot
cp backend/env.production.template .env
# Edit .env with your configuration
./deploy-production.sh
```

## 📋 Detailed Configuration

### 1. Environment Configuration

Copy the production template and configure your environment:

```bash
cp backend/env.production.template .env
```

#### Critical Settings to Configure:

```bash
# Security (REQUIRED)
SECRET_KEY=your-super-secure-secret-key-minimum-32-chars
OPENAI_API_KEY=your-openai-api-key-here
DB_PASSWORD=your-secure-database-password

# Domain and CORS (REQUIRED for production)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
REACT_APP_API_URL=https://api.yourdomain.com

# Optional: API Authentication
API_KEYS=api-key-1,api-key-2,api-key-3

# Optional: Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Optional: Backup Configuration
S3_BUCKET=your-backup-bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=your-s3-access-key
S3_SECRET_KEY=your-s3-secret-key
```

### 2. SSL/HTTPS Setup

#### Option 1: Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
sudo chown $USER:$USER ./nginx/ssl/*
```

#### Option 2: Using Custom Certificates

```bash
# Place your certificates in ./nginx/ssl/
mkdir -p ./nginx/ssl/
cp your-certificate.crt ./nginx/ssl/fullchain.pem
cp your-private-key.key ./nginx/ssl/privkey.pem
```

### 3. Production Deployment Options

#### Option A: Full Deployment with Monitoring

```bash
# Deploy with all services including monitoring
docker-compose --profile monitoring up -d
```

#### Option B: Core Services Only

```bash
# Deploy core services only
./deploy-production.sh
```

#### Option C: Behind Reverse Proxy

```bash
# Deploy with nginx reverse proxy
docker-compose --profile nginx up -d
```

## 🔧 Production Features

### Security Features

✅ **Authentication & Authorization**
- API key authentication
- Rate limiting (configurable)
- IP allowlisting/blocklisting
- CORS protection

✅ **Security Headers**
- HSTS, CSP, X-Frame-Options
- XSS Protection
- Content-Type validation

✅ **Data Protection**
- Encrypted communications
- Secure session management
- Input validation & sanitization

### Monitoring & Observability

✅ **Health Checks**
- Application health endpoint
- Database connectivity
- External service status
- System resource monitoring

✅ **Logging**
- Structured JSON logging
- Request/response logging
- Error tracking and alerting
- Audit trails

✅ **Metrics**
- Application performance metrics
- API usage statistics
- System resource utilization
- Custom business metrics

### Performance Optimization

✅ **Caching**
- Redis-based caching
- In-memory fallback
- API response caching
- Computation result caching

✅ **Database Optimization**
- Connection pooling
- Query optimization
- Automatic indexing
- Performance monitoring

✅ **Resource Management**
- Memory limits and reservations
- CPU limits and scaling
- Disk space monitoring
- Automatic cleanup

### Backup & Recovery

✅ **Automated Backups**
- Scheduled daily backups
- S3 cloud storage support
- Retention policy management
- Point-in-time recovery

✅ **Data Persistence**
- PostgreSQL for structured data
- ChromaDB for vector embeddings
- File storage with versioning
- Configuration backup

## 🌐 Deployment Environments

### Local Development

```bash
# Development with hot reload
export BUILD_TARGET=development
docker-compose up -d
```

### Staging Environment

```bash
# Staging environment
export ENVIRONMENT=staging
export BUILD_TARGET=production
docker-compose up -d
```

### Production Environment

```bash
# Production deployment
export ENVIRONMENT=production
export BUILD_TARGET=production
./deploy-production.sh
```

## 📊 Monitoring & Maintenance

### Health Monitoring

```bash
# Check application health
curl https://yourdomain.com/health

# Check metrics
curl https://yourdomain.com/metrics

# Check service status
docker-compose ps
```

### Log Management

```bash
# View application logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f

# Export logs
docker-compose logs --no-color > application.log
```

### Database Management

```bash
# Connect to database
docker-compose exec postgres psql -U esg_user -d esg_copilot

# Create backup
docker-compose exec postgres pg_dump -U esg_user esg_copilot > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U esg_user -d esg_copilot < backup.sql
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Check container health
docker-compose exec backend curl -f http://localhost:8000/health

# Monitor database performance
docker-compose exec postgres psql -U esg_user -d esg_copilot -c "SELECT * FROM pg_stat_activity;"
```

## 🔄 Updates & Maintenance

### Application Updates

```bash
# Pull latest changes
git pull origin main

# Deploy update
./deploy-production.sh

# Verify deployment
curl https://yourdomain.com/health
```

### Database Migrations

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head
```

### Certificate Renewal

```bash
# Renew Let's Encrypt certificates
sudo certbot renew

# Restart nginx to use new certificates
docker-compose restart frontend
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check configuration
docker-compose config

# Restart services
docker-compose restart
```

#### 2. Database Connection Issues

```bash
# Check database status
docker-compose exec postgres pg_isready -U esg_user

# Reset database connection
docker-compose restart postgres backend
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in ./nginx/ssl/fullchain.pem -text -noout

# Test SSL configuration
docker-compose exec frontend nginx -t
```

#### 4. Performance Issues

```bash
# Check resource usage
docker stats

# Scale services
docker-compose up -d --scale backend=2

# Check database performance
docker-compose exec postgres psql -U esg_user -d esg_copilot -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Emergency Procedures

#### Rollback Deployment

```bash
# Automatic rollback (if deployment script fails)
# The script will automatically rollback on failure

# Manual rollback
docker-compose down
git checkout previous-stable-commit
./deploy-production.sh
```

#### Database Recovery

```bash
# Restore from latest backup
docker-compose exec -T postgres psql -U esg_user -d esg_copilot < latest-backup.sql

# Restore from S3 backup
aws s3 cp s3://your-backup-bucket/latest-backup.sql ./
docker-compose exec -T postgres psql -U esg_user -d esg_copilot < latest-backup.sql
```

## 🔐 Security Checklist

- [ ] Strong passwords and secrets configured
- [ ] SSL/TLS certificates properly configured
- [ ] Firewall rules configured (ports 80, 443 only)
- [ ] Regular security updates enabled
- [ ] API keys rotated regularly
- [ ] Access logs monitored
- [ ] Backup encryption enabled
- [ ] Database access restricted
- [ ] Environment variables secured
- [ ] Container images scanned for vulnerabilities

## 📈 Performance Optimization

### Scaling Strategies

1. **Horizontal Scaling**
   ```bash
   # Scale backend services
   docker-compose up -d --scale backend=3
   ```

2. **Load Balancing**
   - Use nginx reverse proxy
   - Configure upstream servers
   - Implement health checks

3. **Database Optimization**
   - Regular VACUUM and ANALYZE
   - Index optimization
   - Connection pooling

4. **Caching Strategy**
   - Redis for session data
   - Application-level caching
   - CDN for static assets

### Resource Limits

```yaml
# Recommended production limits
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.25'
```

## 📞 Support & Maintenance

### Monitoring Alerts

Set up alerts for:
- High memory/CPU usage
- Failed health checks
- Database connection errors
- SSL certificate expiration
- Disk space low

### Regular Maintenance Tasks

**Daily:**
- Check health endpoints
- Review error logs
- Monitor resource usage

**Weekly:**
- Update system packages
- Review security logs
- Test backup restoration

**Monthly:**
- Rotate API keys
- Review performance metrics
- Update dependencies

## 🎯 Production Checklist

Before going live:

### Infrastructure
- [ ] Production server provisioned
- [ ] Domain name configured
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Backup storage configured

### Application
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] API keys generated
- [ ] Health checks passing
- [ ] Monitoring configured

### Security
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Authentication working
- [ ] Audit logging enabled

### Performance
- [ ] Caching configured
- [ ] Database optimized
- [ ] Resource limits set
- [ ] Load testing completed
- [ ] Monitoring dashboards ready

---

For additional support or questions, please refer to the application documentation or contact the development team.
