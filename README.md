# Digit Classifier API

A machine learning API that classifies handwritten digits using a neural network trained on the MNIST dataset.

## Project Structure

```
digit-classifier/
├── src/                    # Application source code
│   ├── app.py             # Flask application
│   ├── model.py           # Neural network model
│   └── monitor.py         # Monitoring utilities
├── tests/                 # Test files
│   └── test_app.py        # API tests
├── docker/                # Docker-related files
│   └── Dockerfile        # Main Dockerfile
├── terraform/             # Infrastructure as Code
│   ├── main.tf           # Main Terraform configuration
│   ├── vpc.tf            # VPC configuration
│   ├── ecs.tf            # ECS configuration
│   ├── iam.tf            # IAM roles and policies
│   ├── variables.tf      # Variable definitions
│   └── outputs.tf        # Output definitions
├── monitoring/           # Monitoring configuration
│   ├── prometheus/       # Prometheus configuration
│   └── grafana/         # Grafana dashboards
├── scripts/             # Utility scripts
├── .github/             # GitHub configuration
│   └── workflows/       # GitHub Actions workflows
├── docker-compose.yml   # Local development setup
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## Features

- Handwritten digit classification using a neural network
- Real-time predictions through REST API
- Interactive drawing interface for digit input
- Model performance monitoring with TensorBoard
- Metrics collection with Prometheus
- Visualization with Grafana
- Containerized deployment with Docker
- Infrastructure as Code with Terraform
- CI/CD pipeline with GitHub Actions

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- AWS CLI configured with appropriate credentials
- Terraform 1.0+

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/digit-classifier.git
   cd digit-classifier
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # Linux/macOS
   .\env\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
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
```bash
pytest tests/ --cov=src
```

## Deployment

1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

3. Deploy infrastructure:
   ```bash
   terraform apply
   ```

4. Push Docker image:
   ```powershell
   .\scripts\push_image.ps1 -AWS_ACCOUNT_ID your-account-id -AWS_REGION your-region
   ```

## Monitoring

### TensorBoard
Access TensorBoard through the `/dashboard` endpoint to view:
- Model architecture
- Training metrics
- Validation metrics
- Real-time prediction accuracy

### Prometheus & Grafana
Monitor application metrics including:
- Request rates
- Response times
- Prediction accuracy
- System resources

## API Endpoints

- `GET /`: Drawing interface for digit classification
- `POST /predict`: Submit digit image for classification
- `GET /dashboard`: TensorBoard dashboard
- `GET /metrics`: Prometheus metrics
- `GET /health`: Health check endpoint

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

    