#!/bin/bash

# Telegram Recon Bot Startup Script
# This script helps you start the bot in different modes

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

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_status "Please copy .env.example to .env and configure your settings:"
        echo "cp .env.example .env"
        exit 1
    fi
}

# Function to check if required environment variables are set
check_env_vars() {
    print_status "Checking environment variables..."
    
    if ! grep -q "BOT_TOKEN=" .env || grep -q "BOT_TOKEN=$" .env; then
        print_error "BOT_TOKEN is not set in .env file"
        exit 1
    fi
    
    if ! grep -q "ADMIN_CHAT_ID=" .env || grep -q "ADMIN_CHAT_ID=$" .env; then
        print_error "ADMIN_CHAT_ID is not set in .env file"
        exit 1
    fi
    
    if ! grep -q "TARGET_TOPIC_ID=" .env || grep -q "TARGET_TOPIC_ID=$" .env; then
        print_error "TARGET_TOPIC_ID is not set in .env file"
        exit 1
    fi
    
    print_success "Environment variables are configured"
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    print_success "Dependencies installed successfully"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs reports
    print_success "Directories created"
}

# Function to start the bot normally
start_bot() {
    print_status "Starting Telegram Recon Bot..."
    python3 main.py
}

# Function to start the bot with Docker
start_docker() {
    print_status "Starting bot with Docker Compose..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found!"
        exit 1
    fi
    
    # Build and start the container
    docker-compose up --build -d
    
    print_success "Bot started with Docker"
    print_status "Use 'docker-compose logs -f' to view logs"
    print_status "Use 'docker-compose down' to stop the bot"
}

# Function to stop Docker containers
stop_docker() {
    print_status "Stopping Docker containers..."
    docker-compose down
    print_success "Docker containers stopped"
}

# Function to show Docker logs
show_logs() {
    print_status "Showing Docker logs..."
    docker-compose logs -f
}

# Function to show help
show_help() {
    echo "Telegram Recon Bot Startup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start       Start the bot normally (default)"
    echo "  docker      Start the bot with Docker Compose"
    echo "  stop        Stop Docker containers"
    echo "  logs        Show Docker logs"
    echo "  install     Install Python dependencies"
    echo "  check       Check environment configuration"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start bot normally"
    echo "  $0 docker    # Start with Docker"
    echo "  $0 logs      # View Docker logs"
}

# Main script logic
case "${1:-start}" in
    "start")
        check_env_file
        check_env_vars
        create_directories
        start_bot
        ;;
    "docker")
        check_env_file
        check_env_vars
        start_docker
        ;;
    "stop")
        stop_docker
        ;;
    "logs")
        show_logs
        ;;
    "install")
        install_dependencies
        ;;
    "check")
        check_env_file
        check_env_vars
        print_success "Configuration is valid"
        ;;
    "help")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac