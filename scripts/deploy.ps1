# Deployment script for the Digit Classifier application

param(
    [Parameter(Mandatory=$true)]
    [string]$AWS_ACCOUNT_ID,
    
    [Parameter(Mandatory=$true)]
    [string]$AWS_REGION = "us-west-1"
)

# Set environment variables
$ENV:AWS_REGION = $AWS_REGION
$ECR_REPOSITORY = "digit-classifier"
$ECR_REPOSITORY_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

Write-Host "Starting deployment process..."

# Build the Docker image
Write-Host "Building Docker image..."
docker build -t $ECR_REPOSITORY -f docker/Dockerfile .

# Log in to ECR
Write-Host "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Tag and push the image
Write-Host "Tagging and pushing image to ECR..."
docker tag "${ECR_REPOSITORY}:latest" "${ECR_REPOSITORY_URI}:latest"
docker push "${ECR_REPOSITORY_URI}:latest"

# Apply Terraform changes
Write-Host "Applying Terraform changes..."
Push-Location terraform
terraform init
terraform apply -auto-approve
Pop-Location

Write-Host "Deployment completed successfully!"
Write-Host "You can access the application through the ALB DNS name (check AWS Console or Terraform outputs)" 