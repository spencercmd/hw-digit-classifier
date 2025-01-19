FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    numpy==1.23.5 \
    protobuf==3.20.3 \
    grpcio==1.59.3 \
    markdown==3.5.1 \
    werkzeug==3.0.1 \
    tensorboard==2.11.0 \
    six==1.16.0 \
    html5lib==1.1 \
    bleach==6.1.0

# Create logs directory
RUN mkdir -p /app/logs

# Copy TensorBoard logs to a temporary location
COPY logs/events.out.tfevents.1737240195.25cd1de72728.1.0.v2 /app/tb_logs

# Create startup script
RUN echo '#!/bin/sh\n\
echo "Starting TensorBoard..."\n\
echo "Contents of /app/logs:"\n\
ls -la /app/logs\n\
echo "Copying TensorBoard logs..."\n\
cp /app/tb_logs /app/logs/events.out.tfevents.1737240195.25cd1de72728.1.0.v2\n\
echo "Starting TensorBoard server..."\n\
tensorboard serve --logdir=/app/logs --port=6006 --host=0.0.0.0' > /app/start.sh && \
    chmod +x /app/start.sh

# Start TensorBoard
CMD ["/app/start.sh"] 