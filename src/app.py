from flask import Flask, request, jsonify, render_template_string, g
from .model import load_and_preprocess_data, create_and_train_model, predict, load_trained_model
from .monitor import before_request, record_prediction, set_model_info, start_request
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import numpy as np
import logging
import subprocess
from pathlib import Path
import atexit
import time
import os
import signal

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# Register the monitoring functions
app.before_request(start_request)
app.after_request(before_request)

# Global variables
tensorboard_process = None
model = None

def initialize_model():
    """Initialize the model based on environment"""
    global model
    
    try:
        is_development = os.environ.get('PYTHON_ENV', 'production') == 'development'
        logging.info(f"Initializing model in {'development' if is_development else 'production'} mode")
        
        if is_development:
            # In development, train a new model
            logging.info("Development mode: Training new model...")
            x_train, y_train, _, _ = load_and_preprocess_data()
            model = create_and_train_model(x_train, y_train, epochs=5)
        else:
            # In production, load pre-trained model
            logging.info("Production mode: Loading pre-trained model...")
            model = load_trained_model()
            if model is None:
                logging.warning("No pre-trained model found! Training new model...")
                x_train, y_train, _, _ = load_and_preprocess_data()
                model = create_and_train_model(x_train, y_train, epochs=10)
                logging.info("New model trained successfully")
        
        if model is not None:
            logging.info("Model initialized successfully")
            set_model_info(model)
            # Start TensorBoard after model is loaded/trained
            start_tensorboard()
        else:
            logging.error("Failed to initialize model")
        
        return model
    except Exception as e:
        logging.error(f"Error initializing model: {str(e)}")
        raise

def start_tensorboard():
    """Start TensorBoard server"""
    global tensorboard_process
    if tensorboard_process is None:
        try:
            Path("logs/fit").mkdir(parents=True, exist_ok=True)
            # Use PORT environment variable or fallback to 6006
            tensorboard_port = int(os.environ.get('TENSORBOARD_PORT', '6006'))
            tensorboard_process = subprocess.Popen(
                ["tensorboard", "--logdir=logs/fit", f"--port={tensorboard_port}", "--bind_all"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.info(f"TensorBoard started on port {tensorboard_port}")
        except Exception as e:
            logging.error(f"Failed to start TensorBoard: {e}")

def cleanup_tensorboard():
    """Cleanup TensorBoard process"""
    global tensorboard_process
    if tensorboard_process:
        logging.info("Shutting down TensorBoard...")
        try:
            os.kill(tensorboard_process.pid, signal.SIGTERM)
            tensorboard_process.wait(timeout=5)
        except Exception as e:
            logging.error(f"Error shutting down TensorBoard: {e}")
            if tensorboard_process.poll() is None:
                tensorboard_process.kill()
        tensorboard_process = None

# Register cleanup function
atexit.register(cleanup_tensorboard)

# Initialize model at startup
initialize_model()

@app.route('/predict', methods=['POST'])
def predict_digit():
    """Endpoint for digit prediction"""
    try:
        image_data = request.get_json().get('image_data')
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400

        image_data = np.array(image_data)
        predicted_label, probabilities = predict(model, image_data)
        record_prediction(predicted_label)

        return jsonify({
            'predicted_label': int(predicted_label),
            'probabilities': probabilities
        })
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        if model is None:
            logging.error("Health check failed: Model not initialized")
            return "Model not initialized", 503
            
        # Try a simple prediction to ensure model is working
        test_data = np.zeros((28, 28))
        try:
            predict(model, test_data)
            logging.debug("Health check passed")
            return "OK", 200
        except Exception as e:
            logging.error(f"Health check failed: Model prediction error: {str(e)}")
            return f"Model prediction error: {str(e)}", 503
            
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return f"Health check error: {str(e)}", 503

@app.route('/')
def home():
    """Home page with digit drawing interface"""
    is_development = os.environ.get('PYTHON_ENV', 'production') == 'development'
    
    # Construct TensorBoard URL based on environment
    if is_development:
        tensorboard_url = "http://localhost:6006"
    else:
        # In production, use the app's domain with the TensorBoard port
        host = request.host.split(':')[0]
        tensorboard_url = f"https://{host}"  # Fly.io handles SSL termination
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digit Classifier - CNN Demo</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }
            h1 { color: #333; }
            .container { margin: 20px 0; }
            canvas {
                border: 2px solid #333;
                border-radius: 4px;
                margin: 10px;
            }
            .button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            .button:hover { background-color: #45a049; }
            .result {
                font-size: 24px;
                margin: 20px;
                font-weight: bold;
            }
            .links {
                margin: 20px 0;
                padding: 10px;
                background: #f5f5f5;
                border-radius: 4px;
            }
            .links a {
                color: #4CAF50;
                margin: 0 10px;
                text-decoration: none;
            }
            .links a:hover { text-decoration: underline; }
            .dev-only {
                display: """ + ('block' if is_development else 'none') + """;
            }
            .description {
                margin: 20px auto;
                max-width: 600px;
                line-height: 1.6;
                color: #666;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>Digit Classifier CNN Demo</h1>
        
        <div class="description">
            <p>This application demonstrates a Convolutional Neural Network (CNN) trained on the MNIST dataset to recognize handwritten digits. The model architecture includes:</p>
            <ul>
                <li>Two convolutional blocks with batch normalization and dropout</li>
                <li>Dense layers for classification</li>
                <li>Real-time monitoring with Prometheus metrics</li>
                <li>TensorBoard visualization for model training metrics</li>
            </ul>
        </div>

        <div class="links">
            <a href="/metrics" target="_blank">Prometheus Metrics</a>
            <a href="/health" target="_blank">Health Check</a>
            <a href="{{ tensorboard_url }}" target="_blank">TensorBoard</a>
        </div>

        <div class="container">
            <canvas id="drawingCanvas" width="280" height="280"></canvas>
            <div>
                <button class="button" onclick="predict()">Predict</button>
                <button class="button" onclick="clearCanvas()">Clear</button>
            </div>
            <div id="result" class="result"></div>
        </div>
        <script>
            const canvas = document.getElementById('drawingCanvas');
            const ctx = canvas.getContext('2d');
            let isDrawing = false;
            let lastX = 0;
            let lastY = 0;

            // Setup canvas
            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 20;
            ctx.lineCap = 'round';

            function startDrawing(e) {
                isDrawing = true;
                [lastX, lastY] = [e.offsetX, e.offsetY];
            }

            function draw(e) {
                if (!isDrawing) return;
                ctx.beginPath();
                ctx.moveTo(lastX, lastY);
                ctx.lineTo(e.offsetX, e.offsetY);
                ctx.stroke();
                [lastX, lastY] = [e.offsetX, e.offsetY];
            }

            function stopDrawing() {
                isDrawing = false;
            }

            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', stopDrawing);
            canvas.addEventListener('mouseout', stopDrawing);

            function getPixelData() {
                const scaledCanvas = document.createElement('canvas');
                scaledCanvas.width = 28;
                scaledCanvas.height = 28;
                const scaledCtx = scaledCanvas.getContext('2d');
                scaledCtx.drawImage(canvas, 0, 0, 28, 28);
                const imageData = scaledCtx.getImageData(0, 0, 28, 28);
                const data = [];
                for (let i = 0; i < imageData.data.length; i += 4) {
                    data.push(imageData.data[i] / 255.0);
                }
                return data;
            }

            function predict() {
                const data = getPixelData();
                fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_data: data })
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').textContent = 
                        `Predicted Digit: ${data.predicted_label}`;
                })
                .catch(error => {
                    document.getElementById('result').textContent = 
                        'Error: Could not predict digit';
                    console.error('Error:', error);
                });
            }

            function clearCanvas() {
                ctx.fillStyle = 'black';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                document.getElementById('result').textContent = '';
            }
        </script>
    </body>
    </html>
    """, is_development=is_development, tensorboard_url=tensorboard_url)