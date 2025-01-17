param (
    [string]$RepositoryUri,
    [string]$Region
)

Write-Host "Logging in to ECR..."
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $RepositoryUri

Write-Host "Tagging image..."
docker tag mnist-app $RepositoryUri

Write-Host "Pushing image to ECR..."
docker push $RepositoryUri

Write-Host "Image push complete."