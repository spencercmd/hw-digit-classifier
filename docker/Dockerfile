FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-traditional \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p logs/fit models && \
    chmod -R 777 logs models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080
ENV TENSORBOARD_PORT=6006
ENV PYTHONDONTWRITEBYTECODE=1
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV STARTUP_GRACE_PERIOD=180
ENV TENSORBOARD_LOG_DIR=/app/logs/fit/

# Copy requirements and install Python dependencies first
COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

# Copy application code
COPY . .

# Pre-download MNIST dataset
RUN python3 -c "import tensorflow as tf; tf.keras.datasets.mnist.load_data()"

# Verify application can be imported
RUN python3 -c "from src.app import app" || exit 1

# Set permissions for start script
RUN chmod +x docker/start.sh

# Health check with increased grace period and timeouts
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose ports
EXPOSE $PORT $TENSORBOARD_PORT

# Run the application
CMD ["docker/start.sh"]