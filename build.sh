#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input --clear

# Create cache directory
mkdir -p ./staticfiles

# Run the command passed as arguments (from the Dockerfile or render.yaml)
exec "$@"
