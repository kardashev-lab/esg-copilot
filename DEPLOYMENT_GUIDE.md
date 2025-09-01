# Reggie - AI Regulations Co-Pilot - Deployment Guide

This guide provides multiple deployment options for the Reggie - AI Regulations Co-Pilot application, from simple local deployment to production-ready setups.

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key

### 1. Setup
```bash
# Clone and setup
git clone <repository-url>
cd new-esg-copilot
./setup.sh

# Configure environment
nano backend/.env  # Add your OpenAI API key
```

### 2. Run Locally
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm start
```

**Access**: http://localhost:3000

---

## 🌐 Production Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker and Docker Compose
- Domain name
- SSL certificate

#### 1. Create Docker Files

**Backend Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads chroma_db logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile** (`frontend/Dockerfile`):
```dockerfile
FROM node:16-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Nginx Configuration** (`frontend/nginx.conf`):
```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend:8000/health;
        }
    }
}
```

#### 2. Docker Compose Setup

**docker-compose.yml**:
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
      - DEBUG=False
      - LOG_LEVEL=INFO
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_db:/app/chroma_db
      - ./backend/logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: esg_copilot
      POSTGRES_USER: esg_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 3. Environment Setup

**Create `.env` file**:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Security
SECRET_KEY=your-very-secure-secret-key-here

# Database
DB_PASSWORD=your_secure_db_password

# Frontend Configuration
REACT_APP_API_URL=http://localhost
```

#### 4. Deploy
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

### Option 2: Cloud Deployment (AWS/GCP/Azure)

#### AWS Deployment with ECS

**1. Create ECR repositories**:
```bash
aws ecr create-repository --repository-name esg-copilot-backend
aws ecr create-repository --repository-name esg-copilot-frontend
```

**2. Build and push images**:
```bash
# Backend
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t esg-copilot-backend ./backend
docker tag esg-copilot-backend:latest $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/esg-copilot-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/esg-copilot-backend:latest

# Frontend
docker build -t esg-copilot-frontend ./frontend
docker tag esg-copilot-frontend:latest $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/esg-copilot-frontend:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/esg-copilot-frontend:latest
```

**3. Create ECS Task Definition**:
```json
{
  "family": "esg-copilot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/esg-copilot-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "OPENAI_API_KEY", "value": "your-key"},
        {"name": "SECRET_KEY", "value": "your-secret"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/esg-copilot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

### Option 3: Traditional Server Deployment

#### Prerequisites
- Ubuntu 20.04+ server
- Domain name
- SSL certificate

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server

# Create application user
sudo useradd -m -s /bin/bash esgapp
sudo usermod -aG sudo esgapp
```

#### 2. Backend Deployment
```bash
# Switch to application user
sudo su - esgapp

# Clone repository
git clone <repository-url> /home/esgapp/esg-copilot
cd /home/esgapp/esg-copilot/backend

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create environment file
cp env.production.example .env
nano .env  # Configure with your values

# Create systemd service
sudo nano /etc/systemd/system/esg-copilot.service
```

**Systemd service file**:
```ini
[Unit]
Description=Reggie - AI Regulations Co-Pilot Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=esgapp
Group=esgapp
WorkingDirectory=/home/esgapp/esg-copilot/backend
Environment=PATH=/home/esgapp/esg-copilot/backend/venv/bin
ExecStart=/home/esgapp/esg-copilot/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. Frontend Deployment
```bash
# Build frontend
cd /home/esgapp/esg-copilot/frontend
npm install
npm run build

# Configure nginx
sudo nano /etc/nginx/sites-available/esg-copilot
```

**Nginx configuration**:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /home/esgapp/esg-copilot/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

#### 4. Start Services
```bash
# Enable and start services
sudo systemctl enable esg-copilot
sudo systemctl start esg-copilot
sudo systemctl enable nginx
sudo systemctl start nginx

# Enable nginx site
sudo ln -s /etc/nginx/sites-available/esg-copilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

### Option 4: Platform-as-a-Service (PaaS)

#### Heroku Deployment

**1. Create Heroku apps**:
```bash
# Backend
heroku create esg-copilot-backend
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Frontend
heroku create esg-copilot-frontend
```

**2. Backend configuration**:
```bash
# Set environment variables
heroku config:set OPENAI_API_KEY=your_key
heroku config:set SECRET_KEY=your_secret
heroku config:set DEBUG=False

# Deploy
git push heroku main
```

**3. Frontend configuration**:
```bash
# Set buildpack
heroku buildpacks:set mars/create-react-app

# Set environment
heroku config:set REACT_APP_API_URL=https://esg-copilot-backend.herokuapp.com

# Deploy
git push heroku main
```

---

## 🔧 Post-Deployment Configuration

### 1. Environment Variables Checklist
- [ ] `OPENAI_API_KEY` - Your OpenAI API key
- [ ] `SECRET_KEY` - Strong random secret key
- [ ] `DEBUG=False` - Disable debug mode
- [ ] `LOG_LEVEL=INFO` - Set appropriate log level
- [ ] `CORS_ORIGINS` - Configure allowed origins

### 2. Security Checklist
- [ ] HTTPS enabled
- [ ] Strong secret keys
- [ ] CORS properly configured
- [ ] Firewall rules set
- [ ] Regular security updates

### 3. Monitoring Setup
```bash
# View application logs
sudo journalctl -u esg-copilot -f

# Monitor system resources
htop
df -h
free -h
```

### 4. Backup Strategy
```bash
# Database backup
pg_dump esg_copilot > backup_$(date +%Y%m%d).sql

# Application data backup
tar -czf app_backup_$(date +%Y%m%d).tar.gz uploads/ chroma_db/
```

---

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**: Check CORS configuration in backend
2. **API Connection**: Verify API URL in frontend environment
3. **File Uploads**: Check file permissions and disk space
4. **Database Connection**: Verify database credentials

### Debug Mode
```bash
# Temporarily enable debug mode
export DEBUG=True
export LOG_LEVEL=DEBUG

# Restart services
sudo systemctl restart esg-copilot
```

### Health Checks
- Backend: `https://yourdomain.com/api/v1/health`
- Frontend: `https://yourdomain.com/`

---

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment configuration
3. Test API endpoints
4. Review security settings
5. Contact support with detailed error information

## 🔄 Updates and Maintenance

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
