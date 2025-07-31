# Docker Deployment Guide

This guide explains how to deploy the Telegram Recon Bot using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git (for cloning the repository)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repository-url>
cd telegram-recon-bot

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env  # or use your preferred editor
```

### 2. Configure Environment

Edit the `.env` file with your settings:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id
TARGET_TOPIC_ID=your_target_topic_id

# Bot Settings
MAX_FILE_SIZE=5242880
REQUEST_TIMEOUT=30
MAX_CONCURRENT_SCANS=3
LOG_LEVEL=INFO
```

### 3. Start with Docker Compose

```bash
# Using the startup script (recommended)
./start.sh docker

# Or manually
docker-compose up -d --build
```

## 🛠️ Management Commands

### Using the Startup Script

```bash
# Start the bot
./start.sh docker

# View logs
./start.sh logs

# Stop the bot
./start.sh stop

# Check configuration
./start.sh check
```

### Manual Docker Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# View container status
docker-compose ps
```

## 📊 Monitoring

### Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect telegram-recon-bot --format='{{.State.Health.Status}}'
```

### Logs Management

```bash
# View real-time logs
docker-compose logs -f

# View logs from specific time
docker-compose logs --since="1h"

# View last 100 lines
docker-compose logs --tail=100
```

### Resource Usage

```bash
# View resource usage
docker stats telegram-recon-bot

# View detailed container info
docker inspect telegram-recon-bot
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BOT_TOKEN` | Telegram bot token | - | ✅ |
| `ADMIN_CHAT_ID` | Admin chat ID | - | ✅ |
| `TARGET_TOPIC_ID` | Target topic ID | - | ✅ |
| `MAX_FILE_SIZE` | Maximum file size (bytes) | 5242880 | ❌ |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | 30 | ❌ |
| `MAX_CONCURRENT_SCANS` | Max concurrent scans | 3 | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |

### Volume Mounts

- `./reports:/app/reports` - Scan reports storage
- `./logs:/app/logs` - Application logs

### Network Configuration

The bot uses a custom bridge network `telegram-recon-network` for isolation.

## 🔒 Security Considerations

### Container Security

- Runs as non-root user (`botuser`)
- Minimal base image (Python slim)
- No unnecessary packages installed
- Resource limits configured

### Environment Security

```bash
# Ensure .env file permissions
chmod 600 .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

### Network Security

- Container only exposes necessary ports
- Uses custom network for isolation
- No direct host network access

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs for errors
docker-compose logs

# Verify environment variables
docker-compose config

# Check if ports are available
netstat -tulpn | grep :8080
```

#### Bot Not Responding

```bash
# Check bot health
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Restart the bot
docker-compose restart
```

#### Permission Issues

```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./logs ./reports

# Or recreate with correct permissions
docker-compose down
docker-compose up -d
```

#### Memory Issues

```bash
# Check memory usage
docker stats telegram-recon-bot

# Increase memory limits in docker-compose.yml
# memory: 2G  # Increase from 1G
```

### Debug Mode

```bash
# Run in debug mode
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

# Or set debug environment
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart
```

## 🔄 Updates and Maintenance

### Updating the Bot

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup and Restore

```bash
# Backup reports and logs
tar -czf backup-$(date +%Y%m%d).tar.gz reports/ logs/ .env

# Restore from backup
tar -xzf backup-20231201.tar.gz
```

### Cleanup

```bash
# Remove containers and volumes
docker-compose down -v

# Remove images
docker rmi telegram-recon-bot_telegram-recon-bot

# Clean up Docker system
docker system prune -a
```

## 📈 Production Deployment

### Recommended Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  telegram-recon-bot:
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

### Using with Reverse Proxy

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    
    location /health {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
    }
}
```

### Monitoring with Prometheus

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## 📞 Support

If you encounter issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review container logs: `docker-compose logs`
3. Verify environment configuration: `./start.sh check`
4. Check Docker system: `docker system info`

For additional help, please refer to the main [README.md](README.md) and [SETUP_GUIDE.md](SETUP_GUIDE.md).