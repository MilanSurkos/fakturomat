#!/usr/bin/env bash
# Exit on error
set -o errexit

# Run database migrations
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input

# Run the command passed as arguments (from the Dockerfile or render.yaml)
exec "$@"
