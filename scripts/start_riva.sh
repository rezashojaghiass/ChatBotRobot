#!/bin/bash
# Start NVIDIA Riva speech server
# Assumes Riva QuickStart is installed in /home/reza/riva_quickstart_arm64_v2.14.0

RIVA_DIR="/mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0"

if [ ! -d "$RIVA_DIR" ]; then
    echo "Error: Riva directory not found at $RIVA_DIR"
    echo "Please install Riva first. See docs/RIVA_GUIDE.md"
    exit 1
fi

cd "$RIVA_DIR"

echo "Starting Riva speech server..."
# Use the official start script which includes proper Jetson GPU configuration
bash start_riva_v2_14.sh

# Wait for server to be ready
echo "Waiting for Riva server to initialize..."
sleep 5

# Check if container is running
if docker ps | grep -q riva-speech; then
    echo "✓ Riva server is running"
    echo "  Container: riva-speech"
    echo "  Port: 50051 (gRPC)"
    echo ""
    echo "To stop: ./scripts/stop_riva.sh"
else
    echo "✗ Failed to start Riva server"
    echo "Check logs: docker logs riva-speech"
    exit 1
fi
