# The AWS provider. Credentials are NOT written here - Terraform picks them up
# from the usual places (AWS_PROFILE, AWS_ACCESS_KEY_ID, or ~/.aws/credentials).
# Whoever runs this needs admin-ish rights, because it creates IAM users.

provider "aws" {
  region = var.aws_region

  # Every resource below gets these tags automatically. Handy for finding the
  # Isaac Sim spend in Cost Explorer later.
  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

# Small read-only lookups. We need the account ID to build ARNs by hand and to
# print the console sign-in URL at the end.
data "aws_caller_identity" "current" {}
