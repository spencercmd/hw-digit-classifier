# Terraform Infrastructure

This directory contains the Terraform configuration for deploying the Digit Classifier API on AWS using ECS Fargate.

## Infrastructure Overview

The infrastructure includes:

- VPC with public subnets across two availability zones
- Application Load Balancer (ALB)
- ECS Fargate cluster
- ECR repository for Docker images
- IAM roles and policies
- Security groups
- Route tables and Internet Gateway

## Architecture

```
                                    ┌─────────────────┐
                                    │                 │
                                    │    Internet     │
                                    │                 │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   Application   │
                                    │ Load Balancer   │
                                    └────────┬────────┘
                                             │
                         ┌───────────────────┴───────────────────┐
                         │                                       │
                    ┌────┴────┐                            ┌─────┴────┐
                    │ Subnet  │                            │ Subnet   │
                    │   AZ1   │                            │   AZ2    │
                    └────┬────┘                            └─────┬────┘
                         │                                       │
                    ┌────┴────┐                            ┌─────┴────┐
                    │  ECS    │                            │   ECS    │
                    │ Fargate │                            │ Fargate  │
                    └─────────┘                            └──────────┘
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed (version >= 1.0)
- Docker installed locally

## Configuration Files

- `main.tf`: Main infrastructure configuration
- `terraform.tfvars`: AWS credentials and region configuration
- `push_image.ps1`: PowerShell script for building and pushing Docker image

## Usage

1. Initialize Terraform:
```bash
terraform init
```

2. Review the planned changes:
```bash
terraform plan
```

3. Apply the configuration:
```bash
terraform apply
```

4. To destroy the infrastructure:
```bash
terraform destroy
```

## Security Notes

- The VPC is configured with public subnets for simplicity
- Security groups are configured to allow inbound traffic on ports 80 and 5000
- IAM roles follow the principle of least privilege
- Sensitive variables should be managed through a secure secrets management system

## Resource Specifications

- ECS Task: 256 CPU units, 512MB memory
- Load Balancer: Application type (ALB)
- Container Port: 5000
- Health Check Path: `/health`

## Outputs

- `ecr_repository_uri`: The URI of the created ECR repository

## Important Notes

1. Remember to update `terraform.tfvars` with your AWS credentials
2. The infrastructure is set up in the us-west-1 region by default
3. The Docker image is automatically built and pushed to ECR during deployment
4. The service uses the latest tag for the Docker image

## Costs

This infrastructure uses several AWS services that may incur costs:
- ECS Fargate
- Application Load Balancer
- ECR Repository
- VPC and associated networking components

## Maintenance

- Regularly update the provider versions
- Monitor ECS service logs
- Check ALB health check status
- Review security group rules periodically 