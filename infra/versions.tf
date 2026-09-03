# Pins the Terraform CLI and the providers we use. Pinning keeps a `terraform
# apply` on your machine identical to one on your manager's machine.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }

    # Used to zip the Lambda source at plan time. No build step, no CI needed.
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }

    # Generates the SSH key pair.
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}
