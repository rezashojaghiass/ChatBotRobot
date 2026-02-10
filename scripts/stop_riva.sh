#!/bin/bash
# Stop NVIDIA Riva speech server

echo "Stopping Riva speech server..."
docker stop riva-speech

if docker ps | grep -q riva-speech; then
    echo "✗ Failed to stop Riva server"
    exit 1
else
    echo "✓ Riva server stopped"
fi
