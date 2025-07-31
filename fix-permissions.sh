#!/bin/bash

# Fix Docker Permission Issues for Telegram Recon Bot
# This script resolves permission denied errors when writing PDF reports

set -e

echo "🔧 Fixing Docker permission issues..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "Don't run this script as root!"
   exit 1
fi

# Stop running containers
print_status "Stopping Docker containers..."
docker-compose down 2>/dev/null || true

# Create directories if they don't exist
print_status "Creating required directories..."
mkdir -p reports logs

# Method 1: Fix permissions using Docker user ID (1000)
print_status "Setting permissions for Docker user (UID: 1000)..."

# Check if we need sudo
if [[ ! -w reports ]] || [[ ! -w logs ]]; then
    print_warning "Need sudo privileges to fix permissions..."
    sudo chown -R 1000:1000 reports logs
    sudo chmod -R 755 reports logs
else
    chmod -R 755 reports logs
fi

# Verify permissions
print_status "Verifying permissions..."
ls -la reports/ logs/

# Rebuild and start containers
print_status "Rebuilding and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Wait for container to start
print_status "Waiting for container to start..."
sleep 5

# Check container status
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Container started successfully!"
    print_status "📋 Checking logs..."
    docker-compose logs --tail=10 telegram-recon-bot
else
    print_error "❌ Container failed to start!"
    print_error "📋 Error logs:"
    docker-compose logs telegram-recon-bot
    exit 1
fi

echo ""
print_status "🎉 Permission fix completed!"
print_status "📁 Reports will be saved to: $(pwd)/reports/"
print_status "📝 Logs will be saved to: $(pwd)/logs/"
echo ""
print_warning "If you still get permission errors, try:"
echo "   1. docker-compose down"
echo "   2. sudo rm -rf reports logs"
echo "   3. ./fix-permissions.sh"
echo ""