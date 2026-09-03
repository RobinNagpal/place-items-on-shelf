# Pins the Terraform CLI and the providers we use. Pinning keeps a `terraform
# apply` on your machine identical to one on your manager's machine.

terraform {
  required_version = ">= 1.5.0"

  # State lives in an encrypted, versioned S3 bucket made by ./bootstrap, so
  # the GitHub Actions apply and a local apply see the same state. The
  # DynamoDB table stops two applies from running at once.
  backend "s3" {
    bucket         = "isaac-sim-tfstate-729763663166"
    key            = "isaac-sim/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "isaac-sim-tfstate-lock"
    encrypt        = true
  }

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
