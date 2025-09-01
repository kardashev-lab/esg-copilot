# Reggie - AI Regulations Co-Pilot - Production Deployment Guide

This guide provides instructions for deploying the Reggie - AI Regulations Co-Pilot application in a production environment.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- PostgreSQL (recommended for production)
- Redis (recommended for caching)
- OpenAI API key
- Domain name and SSL certificate
- Server with at least 4GB RAM and 2 CPU cores

## Environment Setup

### 1. Clone and Setup Repository

```bash
git clone <repository-url>
cd new-esg-copilot
```

### 2. Backend Configuration

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy production environment file
cp env.production.example .env

# Edit .env with your production values
nano .env
```

### 3. Frontend Configuration

```bash
cd ../frontend

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=https://your-api-domain.com
REACT_APP_NAME=Reggie - AI Regulations Co-Pilot
REACT_APP_VERSION=1.0.0
EOF
```

## Production Configuration

### Environment Variables

Update `backend/.env` with your production values:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_actual_openai_api_key

# Security
SECRET_KEY=your-very-secure-secret-key-here

# API Configuration
DEBUG=False
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost/esg_copilot

# Redis (if using Redis)
REDIS_URL=redis://localhost:6379
```

### Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Secret Key**: Use a strong, randomly generated secret key
3. **CORS**: Restrict CORS origins to your actual domains
4. **HTTPS**: Always use HTTPS in production
5. **Firewall**: Configure firewall rules appropriately

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Backend Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
```

#### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_db:/app/chroma_db
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: esg_copilot
      POSTGRES_USER: esg_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Option 2: Traditional Server Deployment

#### Backend Setup

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Setup application
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/esg-copilot.service
```

Systemd service file:
```ini
[Unit]
Description=Reggie - AI Regulations Co-Pilot Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment=PATH=/path/to/backend/venv/bin
ExecStart=/path/to/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Frontend Setup

```bash
# Build frontend
cd frontend
npm run build

# Configure nginx
sudo nano /etc/nginx/sites-available/esg-copilot
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Logging

### Application Logs

```bash
# View application logs
sudo journalctl -u esg-copilot -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

The application provides health check endpoints:

- Backend: `https://yourdomain.com/api/v1/health`
- Frontend: `https://yourdomain.com/`

### Monitoring Setup

Consider setting up monitoring with:

1. **Application Performance Monitoring (APM)**: New Relic, DataDog, or Sentry
2. **Server Monitoring**: Prometheus + Grafana
3. **Log Aggregation**: ELK Stack or similar

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
pg_dump esg_copilot > backup_$(date +%Y%m%d_%H%M%S).sql

# ChromaDB backup
tar -czf chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz chroma_db/
```

### File Uploads Backup

```bash
# Backup uploaded files
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

## SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Performance Optimization

### Backend Optimization

1. **Database Indexing**: Ensure proper database indexes
2. **Caching**: Implement Redis caching for frequently accessed data
3. **Connection Pooling**: Configure database connection pooling
4. **Async Processing**: Use background tasks for heavy operations

### Frontend Optimization

1. **CDN**: Use a CDN for static assets
2. **Compression**: Enable gzip compression
3. **Caching**: Implement proper caching headers
4. **Bundle Optimization**: Optimize JavaScript bundles

## Security Checklist

- [ ] HTTPS enabled
- [ ] Strong secret keys configured
- [ ] CORS properly configured
- [ ] API rate limiting implemented
- [ ] Input validation enabled
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Security headers configured
- [ ] Regular security updates

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check CORS configuration in backend
2. **API Connection**: Verify API URL in frontend environment
3. **File Uploads**: Check file permissions and disk space
4. **Database Connection**: Verify database credentials and connectivity

### Debug Mode

For troubleshooting, temporarily enable debug mode:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

Remember to disable debug mode in production after troubleshooting.

## Support

For production deployment issues:

1. Check application logs
2. Verify environment configuration
3. Test API endpoints
4. Review security settings
5. Contact support with detailed error information

## Updates and Maintenance

### Application Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt
npm install

# Restart services
sudo systemctl restart esg-copilot
sudo systemctl reload nginx
```

### Regular Maintenance

- Monitor disk space usage
- Review and rotate logs
- Update system packages
- Backup data regularly
- Monitor application performance
- Review security settings
