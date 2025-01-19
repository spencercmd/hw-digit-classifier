from flask import Flask, request, jsonify, render_template_string, g, Response
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
import requests
import threading

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
model_initialization_thread = None
model_initialization_started = False

def initialize_model():
    """Initialize the model based on environment"""
    global model
    
    try:
        is_development = os.environ.get('PYTHON_ENV', 'production') == 'development'
        logging.info(f"Initializing model in {'development' if is_development else 'production'} mode")
        
        # Create necessary directories
        Path("logs/fit").mkdir(parents=True, exist_ok=True)
        Path("models").mkdir(parents=True, exist_ok=True)
        
        if model is not None:
            logging.info("Model already initialized")
            return model
            
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
        model = None  # Ensure model is None on failure
        raise

def start_tensorboard():
    """Start TensorBoard server"""
    global tensorboard_process
    
    # Skip TensorBoard in production/Fly.io environment
    if os.environ.get('FLY_APP_NAME'):
        logging.info("Skipping TensorBoard in Fly.io environment")
        return
        
    if tensorboard_process is not None:
        logging.info("TensorBoard already running")
        return
        
    try:
        Path("logs/fit").mkdir(parents=True, exist_ok=True)
        tensorboard_port = int(os.environ.get('TENSORBOARD_PORT', '6006'))
        
        # Kill any existing TensorBoard processes
        try:
            subprocess.run(['pkill', '-f', 'tensorboard'], check=False)
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Failed to kill existing TensorBoard processes: {e}")
        
        # Start TensorBoard
        tensorboard_process = subprocess.Popen(
            ["tensorboard", "--logdir=logs/fit", f"--port={tensorboard_port}", 
             "--bind_all", "--reload_multifile=false"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for TensorBoard to start
        time.sleep(3)
        
        if tensorboard_process.poll() is not None:
            stderr = tensorboard_process.stderr.read().decode('utf-8')
            logging.error(f"TensorBoard process died unexpectedly: {stderr}")
            tensorboard_process = None
            return
            
        logging.info("TensorBoard started successfully")
        
    except Exception as e:
        logging.error(f"Failed to start TensorBoard: {e}")
        if tensorboard_process is not None:
            tensorboard_process.kill()
            tensorboard_process = None

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
                try:
                    tensorboard_process.kill()
                except Exception:
                    pass
        tensorboard_process = None

# Register cleanup function
atexit.register(cleanup_tensorboard)

# Initialize model at startup in production only
if os.environ.get('PYTHON_ENV', 'production') == 'production':
    initialize_model()

def initialize_model_async():
    """Initialize model in a separate thread"""
    global model, model_initialization_thread
    try:
        initialize_model()
    except Exception as e:
        logging.error(f"Async model initialization failed: {str(e)}")

@app.route('/predict', methods=['POST'])
def predict_digit():
    """Endpoint for digit prediction"""
    try:
        logging.info("Received prediction request")
        
        if not request.is_json:
            logging.error("Request Content-Type is not application/json")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        logging.info(f"Received data keys: {data.keys() if data else 'None'}")
        
        if not data or 'image_data' not in data:
            logging.error("No image data in request")
            return jsonify({'error': 'No image data provided'}), 400

        image_data = np.array(data['image_data'])
        logging.info(f"Image data shape before reshape: {image_data.shape}")
        
        # Ensure the data is properly shaped
        if len(image_data.shape) != 1 or image_data.shape[0] != 784:  # 28*28 = 784
            logging.error(f"Invalid image data shape: {image_data.shape}")
            return jsonify({'error': 'Invalid image data shape'}), 400
            
        image_data = image_data.reshape(28, 28)
        logging.info(f"Image data shape after reshape: {image_data.shape}")

        if model is None:
            logging.error("Model not initialized")
            return jsonify({'error': 'Model not initialized'}), 503

        logging.info("Making prediction")
        predicted_label, probabilities = predict(model, image_data)
        logging.info(f"Prediction result: {predicted_label}")
        
        record_prediction(predicted_label)

        # probabilities is already a list of floats from the predict function
        response_data = {
            'predicted_label': int(predicted_label),
            'probabilities': probabilities
        }
        logging.info("Sending prediction response")
        return jsonify(response_data)
        
    except ValueError as ve:
        logging.error(f"ValueError in prediction: {ve}")
        return jsonify({'error': f'Invalid input data: {str(ve)}'}), 400
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    global model, model_initialization_thread, model_initialization_started
    
    try:
        # Start model initialization in background if not started
        if not model_initialization_started and model is None:
            model_initialization_started = True
            model_initialization_thread = threading.Thread(target=initialize_model_async)
            model_initialization_thread.start()
            logging.info("Started async model initialization")
        
        # Always return 200 during initialization
        if model is None:
            return "Application starting", 200
            
        # Once model is loaded, do a quick prediction
        test_data = np.zeros((28, 28))
        try:
            predict(model, test_data)
            return "OK", 200
        except Exception as e:
            logging.error(f"Health check prediction failed: {str(e)}")
            return "Model prediction error", 503
            
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return f"Health check error: {str(e)}", 503

# Set application start time
app.start_time = time.time()

@app.route('/')
def home():
    """Home page with digit drawing interface"""
    is_development = os.environ.get('PYTHON_ENV', 'production') == 'development'
    
    # Construct TensorBoard URL based on environment
    if is_development:
        tensorboard_url = "http://localhost:6006"
    else:
        # In production, use the TensorBoard Fly.io app
        tensorboard_url = "https://digit-classifier-tensorboard.fly.dev"
    
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
                
                // Use nearest-neighbor interpolation for better digit recognition
                scaledCtx.imageSmoothingEnabled = false;
                scaledCtx.drawImage(canvas, 0, 0, 28, 28);
                
                const imageData = scaledCtx.getImageData(0, 0, 28, 28);
                const data = [];
                
                // Convert to grayscale and normalize
                for (let i = 0; i < imageData.data.length; i += 4) {
                    // Take red channel only since it's grayscale
                    data.push(imageData.data[i] / 255.0);
                }
                
                return data;
            }

            function predict() {
                const data = getPixelData();
                document.getElementById('result').textContent = 'Predicting...';
                
                fetch('/predict', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ image_data: data })
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => {
                            throw new Error(err.error || `HTTP error! status: ${response.status}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    document.getElementById('result').textContent = 
                        `Predicted Digit: ${data.predicted_label}`;
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('result').textContent = 
                        `Error: ${error.message || 'Could not predict digit'}`;
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

if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    port = int(os.environ.get('PORT', 8080))
    
    # Bind to 0.0.0.0 to make the app accessible from outside the container
    app.run(host='0.0.0.0', port=port)