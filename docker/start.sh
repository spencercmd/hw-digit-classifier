#!/bin/bash
set -e

echo "Initializing model..."

# Initialize the model
python3 -c "from src.app import initialize_model; initialize_model()"

# Start Flask application...
echo "Starting Flask application..."
echo "Waiting for Flask to start on 0.0.0.0:${PORT:-8080}..."

# Start the Flask application with gunicorn
exec gunicorn --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --timeout 120 \
    --graceful-timeout 30 \
    "src.app:app" 