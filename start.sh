#!/bin/bash
set -e

# Print environment variables for debugging
echo "HOST: ${HOST}"
echo "PORT: ${PORT}"

# Start TensorBoard with explicit binding
exec tensorboard \
  --logdir=/app/logs \
  --port="${PORT}" \
  --host="${HOST}" \
  --bind_all 