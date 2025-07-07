#!/bin/sh
set -e

# Create media directory if it doesn't exist
mkdir -p /app/media

# Set proper permissions for the media directory
chmod -R 755 /app/media

# Run the command passed to the container
exec "$@"
