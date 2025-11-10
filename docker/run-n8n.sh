#!/bin/sh

# Parse command line arguments
RECREATE_VOLUME=false
while getopts "r" opt; do
    case $opt in
        r)
            RECREATE_VOLUME=true
            ;;
        \?)
            echo "Usage: $0 [-r]"
            echo "  -r    Recreate gmcp_volume (drop and recreate if it exists)"
            exit 1
            ;;
    esac
done

# Get timezone (default to UTC if not set)
TIMEZONE="${TIMEZONE:-UTC}"

# Create n8n_share directory on host if it doesn't exist
N8N_SHARE_DIR="${HOME}/n8n_share"
echo "Checking for n8n_share directory at ${N8N_SHARE_DIR}..."
if [ ! -d "$N8N_SHARE_DIR" ]; then
    echo "Creating n8n_share directory..."
    mkdir -p "$N8N_SHARE_DIR"
    echo "Directory created at ${N8N_SHARE_DIR}"
else
    echo "Directory ${N8N_SHARE_DIR} already exists"
fi

# Create docker network if it doesn't exist
echo "Checking for gmcp_net network..."
if ! docker network inspect gmcp_net >/dev/null 2>&1; then
    echo "Creating gmcp_net network..."
    docker network create gmcp_net
else
    echo "Network gmcp_net already exists"
fi

# Handle gmcp_volume creation/recreation
if [ "$RECREATE_VOLUME" = true ]; then
    echo "Recreate flag (-r) detected"
    if docker volume inspect gmcp_volume >/dev/null 2>&1; then
        echo "Removing existing gmcp_volume..."
        docker volume rm gmcp_volume 2>/dev/null || {
            echo "ERROR: Failed to remove gmcp_volume. It may be in use."
            echo "Stop all containers using the volume first."
            exit 1
        }
    fi
    echo "Creating gmcp_volume..."
    docker volume create gmcp_volume
else
    # Create gmcp_volume if it doesn't exist
    echo "Checking for gmcp_volume..."
    if ! docker volume inspect gmcp_volume >/dev/null 2>&1; then
        echo "Creating gmcp_volume..."
        docker volume create gmcp_volume
    else
        echo "Volume gmcp_volume already exists"
    fi
fi

# Stop and remove existing container if it exists
echo "Stopping existing n8n container..."
docker stop n8n 2>/dev/null || true

echo "Removing existing n8n container..."
docker rm n8n 2>/dev/null || true

echo "Starting n8n container..."
docker run -d \
  --name n8n \
  --network gmcp_net \
  -p 5678:5678 \
  -e GENERIC_TIMEZONE="$TIMEZONE" \
  -e TZ="$TIMEZONE" \
  -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
  -e N8N_RUNNERS_ENABLED=true \
  -v gmcp_volume:/home/node/.n8n \
  -v "${N8N_SHARE_DIR}":/data/n8n_share \
  docker.n8n.io/n8nio/n8n

if docker ps -q -f name=n8n | grep -q .; then
    echo "Container n8n is now running"
    echo ""
    echo "n8n is accessible at http://localhost:5678"
    echo "On gmcp_net, other containers can reach it at http://n8n:5678"
    echo "Data stored in Docker volume: gmcp_volume"
    echo "Shared directory: ${N8N_SHARE_DIR} -> /data/n8n_share (inside container)"
    echo ""
    echo "To view logs: docker logs -f n8n"
    echo "To stop: docker stop n8n"
    echo "To recreate volume: ./docker/run-n8n.sh -r"
else
    echo "ERROR: Container n8n failed to start"
    docker logs n8n
    exit 1
fi
