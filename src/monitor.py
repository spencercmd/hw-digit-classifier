import subprocess
import webbrowser
from pathlib import Path
import time
import logging
from prometheus_client import Counter, Histogram, Info
from functools import wraps
from flask import request, g

def start_tensorboard(logdir="logs/fit", port=6006):
    """
    Start TensorBoard server and open it in the default web browser
    
    Args:
        logdir (str): Directory containing the TensorBoard logs
        port (int): Port to run TensorBoard on
    """
    logging.info(f"Starting TensorBoard server on port {port}")
    
    # Ensure the log directory exists
    Path(logdir).mkdir(parents=True, exist_ok=True)
    
    # Start TensorBoard server
    tensorboard = subprocess.Popen(
        ["tensorboard", "--logdir", logdir, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for TensorBoard to start
    time.sleep(3)
    
    # Open TensorBoard in browser
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    
    logging.info(f"TensorBoard is running at {url}")
    return tensorboard

# Create metrics
REQUEST_COUNT = Counter(
    'flask_request_count', 'App Request Count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'flask_http_request_duration_seconds',
    'Flask Request Latency',
    ['method', 'endpoint']
)

PREDICTION_COUNT = Counter(
    'digit_prediction_count',
    'Number of digit predictions made',
    ['predicted_digit']
)

MODEL_INFO = Info('digit_classifier_model', 'Information about the digit classifier model')

def start_request():
    """Store request start time"""
    g.start_time = time.time()

def before_request(response):
    """Update metrics before each request"""
    if not hasattr(g, 'start_time'):
        return response
        
    request_latency = time.time() - g.start_time
    if request.endpoint:
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint
        ).observe(request_latency)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint,
            http_status=response.status_code
        ).inc()
    
    return response

def record_prediction(digit):
    """Record a prediction in the metrics"""
    PREDICTION_COUNT.labels(predicted_digit=str(digit)).inc()

def set_model_info(model):
    """Set information about the model in the metrics"""
    config = model.get_config()
    MODEL_INFO.info({
        'type': 'CNN',
        'layers': str(len(config['layers'])),
        'optimizer': model.optimizer.__class__.__name__
    })

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Start TensorBoard
    tensorboard_process = start_tensorboard()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        logging.info("Shutting down TensorBoard...")
        tensorboard_process.terminate()
        tensorboard_process.wait() 