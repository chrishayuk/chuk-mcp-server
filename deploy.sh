#!/bin/bash
# ChukMCPServer Deployment Script
# Quick deployment helper for Docker-based deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_info "✓ Prerequisites satisfied"
}

# Setup environment
setup_env() {
    print_info "Setting up environment..."

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warn "Created .env from .env.example. Please edit it with your credentials."
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_info "✓ .env file exists"
    fi

    if [ ! -f config.yaml ]; then
        if [ -f config.example.yaml ]; then
            cp config.example.yaml config.yaml
            print_info "Created config.yaml from config.example.yaml"
        else
            print_warn "No config files found. Using default configuration."
        fi
    else
        print_info "✓ config.yaml exists"
    fi
}

# Build Docker image
build_image() {
    print_info "Building Docker image..."
    docker-compose build mcp-server
    print_info "✓ Docker image built successfully"
}

# Start services
start_services() {
    local profile="${1:-default}"

    print_info "Starting services (profile: $profile)..."

    if [ "$profile" = "default" ]; then
        docker-compose up -d mcp-server
    else
        docker-compose --profile "$profile" up -d
    fi

    print_info "✓ Services started"
}

# Stop services
stop_services() {
    print_info "Stopping services..."
    docker-compose down
    print_info "✓ Services stopped"
}

# Show logs
show_logs() {
    docker-compose logs -f mcp-server
}

# Show status
show_status() {
    print_info "Service status:"
    docker-compose ps

    print_info "\nTesting health endpoint..."
    sleep 2
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_info "✓ Server is healthy and responding"
    else
        print_warn "Server health check failed. Check logs with: ./deploy.sh logs"
    fi
}

# Main command handler
case "${1:-}" in
    setup)
        check_prerequisites
        setup_env
        print_info "Setup complete. Edit .env and config.yaml, then run: ./deploy.sh start"
        ;;

    build)
        check_prerequisites
        build_image
        ;;

    start)
        check_prerequisites
        setup_env
        build_image
        start_services "${2:-default}"
        show_status
        print_info "\nServer is running at http://localhost:8000"
        print_info "View logs: ./deploy.sh logs"
        print_info "Stop server: ./deploy.sh stop"
        ;;

    stop)
        stop_services
        ;;

    restart)
        stop_services
        sleep 2
        start_services "${2:-default}"
        show_status
        ;;

    logs)
        show_logs
        ;;

    status)
        show_status
        ;;

    dev)
        check_prerequisites
        setup_env
        print_info "Starting development server with hot reload..."
        docker-compose --profile dev up --build
        ;;

    *)
        echo "ChukMCPServer Deployment Script"
        echo ""
        echo "Usage: $0 {setup|build|start|stop|restart|logs|status|dev}"
        echo ""
        echo "Commands:"
        echo "  setup      - Initial setup (create .env and config.yaml)"
        echo "  build      - Build Docker image"
        echo "  start      - Start the server (builds if needed)"
        echo "  stop       - Stop the server"
        echo "  restart    - Restart the server"
        echo "  logs       - Show and follow server logs"
        echo "  status     - Show service status and health"
        echo "  dev        - Start development server with hot reload"
        echo ""
        echo "Examples:"
        echo "  $0 setup          # First time setup"
        echo "  $0 start          # Start production server"
        echo "  $0 start dev      # Start with dev profile"
        echo "  $0 start cache    # Start with Redis cache"
        echo "  $0 logs           # View logs"
        exit 1
        ;;
esac
