# Digit Classifier

A Flask application that uses TensorFlow to classify handwritten digits.

## Features

- Handwritten digit classification using TensorFlow
- Real-time predictions via REST API
- TensorBoard integration for model monitoring
- Prometheus metrics
- Grafana dashboards

## Local Development

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/app.py
   ```

4. Start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

The application will be available at:
- API: http://localhost:5000
- TensorBoard: http://localhost:6006
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Testing

Run the test suite:
bash
pytest tests/ --cov=src

## Deployment

### Prerequisites

1. Install the Fly.io CLI:
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex

   # MacOS/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. Login to Fly.io:
   ```bash
   fly auth login
   ```

### Deploy the Application

1. Launch the application (first time only):
   ```bash
   fly launch
   ```

2. Deploy updates:
   ```bash
   fly deploy
   ```

3. Scale the application (if needed):
   ```bash
   fly scale memory 512
   fly scale vm shared-cpu-1x
   ```

4. View application status:
   ```bash
   fly status
   ```

5. View application logs:
   ```bash
   fly logs
   ```

### Monitoring

#### TensorBoard
Access TensorBoard through the `/dashboard` endpoint to view:
- Model architecture
- Training metrics
- Validation metrics
- Real-time prediction accuracy

#### Prometheus & Grafana
Monitor application metrics including:
- Request rates
- Response times
- Prediction accuracy
- System resources

## API Endpoints

- `GET /`: Drawing interface for digit classification
- `POST /predict`: Submit image for prediction
- `GET /health`: Health check endpoint
- `GET /dashboard`: TensorBoard dashboard
- `GET /metrics`: Prometheus metrics

## Environment Variables

- `PORT`: Application port (default: 8080)
- `FLASK_ENV`: Environment mode (development/production)
- `LOG_LEVEL`: Logging level (default: INFO)