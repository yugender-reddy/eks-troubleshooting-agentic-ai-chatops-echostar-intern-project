variable "name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "eks-agentic-troubleshooting"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for Prometheus AlertManager notifications"
  type        = string
  default     = ""
}

variable "slack_channel_name" {
  description = "Slack channel name for Prometheus AlertManager notifications"
  type        = string
  default     = ""
}

# Agentic deployment variables
variable "agentic_image_repository" {
  description = "ECR repository for the Agentic AI troubleshooting agent image"
  type        = string
  default     = ""
}

variable "agentic_image_tag" {
  description = "Tag for the Agentic AI troubleshooting agent image"
  type        = string
  default     = "latest"
}

# Google Chat credentials (replace Slack)
variable "gchat_service_account_key" {
  description = "Base64-encoded Google Cloud service account JSON key for Google Chat bot"
  type        = string
  default     = ""
  sensitive   = true
}

variable "gchat_project_id" {
  description = "Google Cloud Project ID for the Chat app"
  type        = string
  default     = ""
}

variable "gchat_project_number" {
  description = "Google Cloud Project Number (for JWT audience verification)"
  type        = string
  default     = ""
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID for AI agent"
  type        = string
  default     = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
}

variable "vector_bucket_name" {
  description = "S3 bucket name for vector storage (must be created manually before deployment)"
  type        = string
  default     = ""
}

variable "vector_index_name" {
  description = "S3 Vectors index name for troubleshooting knowledge base"
  type        = string
  default     = "k8s-troubleshooting"
}

variable "chat_platform" {
  description = "Chat platform to deploy: 'slack' (Socket Mode, no NLB needed) or 'gchat' (HTTP webhook, NLB required)"
  type        = string
  default     = "slack"
  validation {
    condition     = contains(["slack", "gchat"], var.chat_platform)
    error_message = "chat_platform must be either 'slack' or 'gchat'."
  }
}
