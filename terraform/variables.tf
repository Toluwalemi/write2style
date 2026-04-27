variable "project_id" {
  type    = string
  default = "write2style"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "backend_service_name" {
  type    = string
  default = "write2style-backend"
}

variable "frontend_service_name" {
  type    = string
  default = "write2style-frontend"
}

variable "github_repo" {
  type    = string
  default = "Toluwalemi/write2style"
}

variable "docker_image_tag" {
  type    = string
  default = "bootstrap"
}

variable "style_model" {
  type    = string
  default = "anthropic/claude-sonnet-4.5"
}

variable "draft_model" {
  type    = string
  default = "anthropic/claude-haiku-4.5"
}

variable "pinecone_index" {
  type    = string
  default = "write2style"
}

variable "pinecone_cloud" {
  type    = string
  default = "aws"
}

variable "pinecone_region" {
  type    = string
  default = "us-east-1"
}

variable "clerk_jwks_url" {
  type        = string
  description = "Clerk JWKS URL, e.g. https://your-instance.clerk.accounts.dev/.well-known/jwks.json"
}

variable "clerk_issuer" {
  type        = string
  description = "Clerk issuer URL, e.g. https://your-instance.clerk.accounts.dev"
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "openrouter_api_key" {
  type      = string
  sensitive = true
}

variable "pinecone_api_key" {
  type      = string
  sensitive = true
}
