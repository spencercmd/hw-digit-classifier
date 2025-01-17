#!/bin/bash

# Build a temporary Docker image for training
docker build -f docker/Dockerfile.train -t digit-classifier-train .

# Run the training
docker run -v $(pwd)/models:/app/models digit-classifier-train

echo "Training completed. Model saved in ./models directory" 