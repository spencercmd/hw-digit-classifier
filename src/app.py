from flask import Flask, request, jsonify, render_template_string
from model import load_and_preprocess_data, create_and_train_model, predict
import numpy as np
import logging
import subprocess
import webbrowser
from pathlib import Path
import atexit
import time
import os
import signal
import base64
import re
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# set up the logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable for TensorBoard process
tensorboard_process = None

def start_tensorboard():
    """Start TensorBoard as a subprocess and return the process object"""
    global tensorboard_process
    
    if tensorboard_process is None:
        # Ensure logs directory exists
        Path("logs/fit").mkdir(parents=True, exist_ok=True)
        
        # Start TensorBoard process
        tensorboard_process = subprocess.Popen(
            ["tensorboard", "--logdir=logs/fit", "--port=6006", "--bind_all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for TensorBoard to start
        time.sleep(3)
        
        logging.info("TensorBoard started on port 6006")
    
    return tensorboard_process

def cleanup_tensorboard():
    """Cleanup function to kill TensorBoard process on application shutdown"""
    global tensorboard_process
    if tensorboard_process:
        logging.info("Shutting down TensorBoard...")
        try:
            os.kill(tensorboard_process.pid, signal.SIGTERM)
            tensorboard_process.wait(timeout=5)
        except:
            if tensorboard_process.poll() is None:
                tensorboard_process.kill()
        tensorboard_process = None

# Register cleanup function
atexit.register(cleanup_tensorboard)

# Load model at startup
logging.info("Starting application...")
logging.info("Loading MNIST data...")
x_train, y_train, _, _ = load_and_preprocess_data()
logging.info("Training model...")
model = create_and_train_model(x_train, y_train)
logging.info("Model training completed!")

# Start TensorBoard at application startup
start_tensorboard()

@app.route('/predict', methods=['POST'])
def predict_digit():
    """Receives the data from the client as a JSON object,
    makes a prediction of the digit and responds with a JSON
    object that contains the predicted_label and probabilities

    Returns:
       A JSON response with the predicted label and probabilities, or a JSON error.
    """
    try:
        # Get image data from the request JSON payload
        image_data = request.get_json().get('image_data')

        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400

        # convert to numpy array from list of numbers
        image_data = np.array(image_data)

        # Make the prediction
        predicted_label, probabilities = predict(model, image_data)

        # Return the prediction and probabilities
        return jsonify({
            'predicted_label': int(predicted_label),
            'probabilities': probabilities
        })
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """
    Health check endpoint for the load balancer
    """
    return "", 200

@app.route('/dashboard')
def dashboard():
    """
    Serve the dashboard page with TensorBoard iframe
    """
    # Ensure TensorBoard is running
    if not tensorboard_process or tensorboard_process.poll() is not None:
        start_tensorboard()
    
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Performance Dashboard</title>
        <style>
            body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
            h1 { color: #333; }
            .dashboard-container { 
                width: 100%;
                height: 90vh;
                border: none;
                margin-top: 20px;
            }
            .info {
                background-color: #e7f3fe;
                border-left: 6px solid #2196F3;
                padding: 10px;
                margin: 10px 0;
            }
            .status {
                display: flex;
                align-items: center;
                margin-bottom: 20px;
            }
            .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background-color: #4CAF50;
                margin-right: 10px;
            }
        </style>
        <script>
            function checkTensorBoard() {
                fetch('http://localhost:6006')
                    .then(response => {
                        document.getElementById('status-dot').style.backgroundColor = '#4CAF50';
                        document.getElementById('status-text').textContent = 'TensorBoard is running';
                    })
                    .catch(error => {
                        document.getElementById('status-dot').style.backgroundColor = '#f44336';
                        document.getElementById('status-text').textContent = 'TensorBoard is not responding';
                    });
            }
            
            // Check status every 5 seconds
            setInterval(checkTensorBoard, 5000);
            
            // Initial check
            checkTensorBoard();
        </script>
    </head>
    <body>
        <h1>Model Performance Dashboard</h1>
        <div class="status">
            <div id="status-dot" class="status-dot"></div>
            <span id="status-text">Checking TensorBoard status...</span>
        </div>
        <div class="info">
            TensorBoard is running at <a href="http://localhost:6006" target="_blank">http://localhost:6006</a>
        </div>
        <iframe src="http://localhost:6006" class="dashboard-container"></iframe>
    </body>
    </html>
    """
    return render_template_string(dashboard_html)

@app.route('/')
def draw_interface():
    """
    Serve the main drawing interface
    """
    interface_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Digit Recognition</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
                margin-top: 20px;
                max-width: 800px;
                width: 100%;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
            #canvas-container {
                position: relative;
                margin: 20px 0;
                display: inline-block;
            }
            #drawing-canvas {
                border: 2px solid #333;
                border-radius: 10px;
                cursor: crosshair;
                background-color: black;
            }
            #preview-canvas {
                position: absolute;
                top: 0;
                right: -100px;
                border: 1px solid #666;
                border-radius: 5px;
                background-color: black;
            }
            .button {
                background-color: #4CAF50;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
                transition: all 0.3s ease;
            }
            .button:hover {
                background-color: #45a049;
                transform: translateY(-2px);
            }
            .button.clear {
                background-color: #f44336;
            }
            .button.clear:hover {
                background-color: #da190b;
            }
            #result {
                margin-top: 20px;
                font-size: 24px;
                font-weight: bold;
                color: #333;
                min-height: 36px;
            }
            .controls {
                margin-top: 20px;
            }
            .loading {
                display: none;
                margin: 10px 0;
            }
            .loading:after {
                content: ' .';
                animation: dots 1.5s steps(5, end) infinite;
            }
            @keyframes dots {
                0%, 20% { content: ' .';}
                40% { content: ' ..';}
                60% { content: ' ...';}
                80%, 100% { content: ' ....';}
            }
            .probabilities {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
                margin-top: 20px;
            }
            .probability-bar {
                width: calc(20% - 20px);
                min-width: 100px;
                background: #f0f0f0;
                border-radius: 5px;
                padding: 10px;
                text-align: center;
            }
            .probability-value {
                height: 100px;
                background: #4CAF50;
                margin: 5px 0;
                border-radius: 3px;
                transition: height 0.3s ease;
            }
            .instructions {
                color: #666;
                margin: 20px 0;
                font-size: 14px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Draw a Digit</h1>
            <div class="instructions">
                Draw a single digit (0-9) in the black canvas below.<br>
                The digit should be centered and large enough to fill most of the canvas.
            </div>
            <div id="canvas-container">
                <canvas id="drawing-canvas" width="280" height="280"></canvas>
                <canvas id="preview-canvas" width="28" height="28"></canvas>
            </div>
            <div class="controls">
                <button class="button" onclick="identify()">Identify</button>
                <button class="button clear" onclick="clearCanvas()">Clear</button>
            </div>
            <div id="loading" class="loading">Identifying digit</div>
            <div id="result"></div>
            <div class="probabilities" id="probabilities"></div>
        </div>

        <script>
            const canvas = document.getElementById('drawing-canvas');
            const previewCanvas = document.getElementById('preview-canvas');
            const ctx = canvas.getContext('2d');
            const previewCtx = previewCanvas.getContext('2d');
            let isDrawing = false;
            let lastX = 0;
            let lastY = 0;

            // Set up the canvas
            ctx.strokeStyle = 'white';
            ctx.lineJoin = 'round';
            ctx.lineCap = 'round';
            ctx.lineWidth = 20;

            // Drawing event listeners
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', stopDrawing);
            canvas.addEventListener('mouseout', stopDrawing);
            canvas.addEventListener('touchstart', handleTouch);
            canvas.addEventListener('touchmove', handleTouch);
            canvas.addEventListener('touchend', stopDrawing);

            function updatePreview() {
                // Clear preview
                previewCtx.fillStyle = 'black';
                previewCtx.fillRect(0, 0, 28, 28);
                
                // Draw scaled down version
                previewCtx.drawImage(canvas, 0, 0, 280, 280, 0, 0, 28, 28);
            }

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
                updatePreview();
            }

            function stopDrawing() {
                isDrawing = false;
                updatePreview();
            }

            function handleTouch(e) {
                e.preventDefault();
                if (e.type === 'touchstart') {
                    isDrawing = true;
                    const touch = e.touches[0];
                    const rect = canvas.getBoundingClientRect();
                    [lastX, lastY] = [touch.clientX - rect.left, touch.clientY - rect.top];
                } else if (e.type === 'touchmove' && isDrawing) {
                    const touch = e.touches[0];
                    const rect = canvas.getBoundingClientRect();
                    const x = touch.clientX - rect.left;
                    const y = touch.clientY - rect.top;
                    ctx.beginPath();
                    ctx.moveTo(lastX, lastY);
                    ctx.lineTo(x, y);
                    ctx.stroke();
                    [lastX, lastY] = [x, y];
                    updatePreview();
                }
            }

            function clearCanvas() {
                ctx.fillStyle = 'black';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                previewCtx.fillStyle = 'black';
                previewCtx.fillRect(0, 0, previewCanvas.width, previewCanvas.height);
                document.getElementById('result').textContent = '';
                document.getElementById('probabilities').innerHTML = '';
            }

            function identify() {
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                loading.style.display = 'block';
                result.textContent = '';

                // Get the 28x28 image data directly from the preview canvas
                const imageData = previewCtx.getImageData(0, 0, 28, 28);
                const data = [];
                
                // Convert to grayscale and normalize
                for (let i = 0; i < imageData.data.length; i += 4) {
                    // Take red channel only (they're all the same in grayscale)
                    data.push(imageData.data[i] / 255.0);
                }

                // Send to server
                fetch('/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        image_data: data
                    })
                })
                .then(response => response.json())
                .then(data => {
                    loading.style.display = 'none';
                    result.textContent = `Predicted Digit: ${data.predicted_label}`;
                    updateProbabilities(data.probabilities);
                })
                .catch(error => {
                    loading.style.display = 'none';
                    result.textContent = 'Error: Could not identify digit';
                    console.error('Error:', error);
                });
            }

            function updateProbabilities(probabilities) {
                const container = document.getElementById('probabilities');
                container.innerHTML = '';
                
                probabilities.forEach((prob, index) => {
                    const bar = document.createElement('div');
                    bar.className = 'probability-bar';
                    const height = Math.round(prob * 100);
                    bar.innerHTML = `
                        <div>Digit ${index}</div>
                        <div class="probability-value" style="height: ${height}%"></div>
                        <div>${(prob * 100).toFixed(1)}%</div>
                    `;
                    container.appendChild(bar);
                });
            }

            // Initialize with a clear canvas
            clearCanvas();
        </script>
    </body>
    </html>
    """
    return render_template_string(interface_html)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)