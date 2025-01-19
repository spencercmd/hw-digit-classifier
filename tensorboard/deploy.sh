#!/bin/bash
set -e

# Create a temporary build directory
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

echo "Creating build directory at $BUILD_DIR"

# Create logs directory
mkdir -p $BUILD_DIR/logs

# Copy necessary files to build directory
cp Dockerfile $BUILD_DIR/
cp fly.toml $BUILD_DIR/

# Copy TensorBoard logs
echo "Copying TensorBoard logs..."
if [ -f "../tb_logs/events.out.tfevents.1737240195.25cd1de72728.1.0.v2" ]; then
    cp ../tb_logs/events.out.tfevents.1737240195.25cd1de72728.1.0.v2 $BUILD_DIR/logs/
    echo "Successfully copied TensorBoard log file"
else
    echo "Error: TensorBoard log file not found"
    exit 1
fi

# List contents for verification
echo "Build directory contents:"
ls -la $BUILD_DIR
echo "Logs directory contents:"
ls -la $BUILD_DIR/logs

# Switch to build directory
cd $BUILD_DIR

# Deploy to fly.io
echo "Deploying to fly.io..."
fly deploy -a digit-classifier-tensorboard

echo "Deployment complete!" 