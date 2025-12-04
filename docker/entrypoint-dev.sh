#!/bin/bash
set -e

# Fix data directory permissions if mounted as volume
if [ -d "/home/gofr-plot/devroot/gofr-plot/data" ]; then
    # Check if we can write to data directory
    if [ ! -w "/home/gofr-plot/devroot/gofr-plot/data" ]; then
        echo "Fixing permissions for /home/gofr-plot/devroot/gofr-plot/data..."
        # This will work if container is started with appropriate privileges
        sudo chown -R gofr-plot:gofr-plot /home/gofr-plot/devroot/gofr-plot/data 2>/dev/null || \
            echo "Warning: Could not fix permissions. Run container with --user $(id -u):$(id -g)"
    fi
fi

# Create subdirectories if they don't exist
mkdir -p /home/gofr-plot/devroot/gofr-plot/data/storage /home/gofr-plot/devroot/gofr-plot/data/auth

# Install/sync Python dependencies if requirements.txt exists
if [ -f "/home/gofr-plot/devroot/gofr-plot/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    cd /home/gofr-plot/devroot/gofr-plot
    # Use 'uv pip install' instead of 'sync' to ensure transitive dependencies are installed
    VIRTUAL_ENV=/home/gofr-plot/devroot/gofr-plot/.venv uv pip install -r requirements.txt || \
        echo "Warning: Could not install dependencies"
fi

# Execute the main command
exec "$@"
