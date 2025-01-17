variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-1"
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "app_port" {
  description = "Port exposed by the docker image"
  type        = number
  default     = 5000
}

variable "tensorboard_port" {
  description = "Port for TensorBoard"
  type        = number
  default     = 6006
}

variable "app_count" {
  description = "Number of docker containers to run"
  type        = number
  default     = 2
}

variable "health_check_path" {
  description = "Health check path for the application"
  type        = string
  default     = "/health"
} 