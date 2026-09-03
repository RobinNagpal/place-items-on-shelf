# ---------------------------------------------------------------------------
# Bootstrap: the things the main Terraform needs before it can run
#
#   1. An encrypted, versioned S3 bucket for Terraform state.
#   2. A DynamoDB table so two applies cannot run at the same time.
#   3. An IAM role GitHub Actions can assume (via OIDC, no long-lived keys)
#      to apply the main Terraform from the `main` branch.
#
# Run once, by the account owner, from this folder. The bucket cannot hold
# this state before it exists, so the first apply uses local state:
#
#   mv backend.tf backend.tf.off      # first time only
#   terraform init && terraform apply
#   mv backend.tf.off backend.tf
#   terraform init -migrate-state     # park the state in the new bucket
#
# After that, nothing here changes often.
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }

}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "isaac-sim"
}

variable "github_repo" {
  description = "owner/name of the GitHub repo allowed to assume the deploy role."
  type        = string
  default     = "RobinNagpal/place-items-on-shelf"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform-bootstrap"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  bucket_name = "${var.project_name}-tfstate-${data.aws_caller_identity.current.account_id}"
  table_name  = "${var.project_name}-tfstate-lock"
}

# ---------------------------------------------------------------------------
# State bucket
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "tfstate" {
  bucket = local.bucket_name

  # State holds passwords and keys. Refuse to delete the bucket by accident.
  lifecycle {
    prevent_destroy = true
  }
}

# Every write keeps the previous version, so a bad apply can be rolled back.
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt everything at rest with an AWS-managed key.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# No public access, ever, regardless of any bucket policy or ACL.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Old state versions are useful for a while, not forever.
resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# ---------------------------------------------------------------------------
# Lock table
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "lock" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

# ---------------------------------------------------------------------------
# GitHub Actions deploy role
#
# GitHub signs a short-lived token for every workflow run. AWS trusts those
# tokens through the OIDC provider below, but only when the token says it came
# from this repo's `main` branch. No access keys are stored in GitHub.
# ---------------------------------------------------------------------------

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]

  # AWS validates GitHub's certificate chain itself these days, but the
  # argument is still required. These are GitHub's published thumbprints.
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Only workflows running on the main branch. A pull request branch gets
    # a different "sub" claim and is refused.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name               = "${var.project_name}-github-deploy"
  description        = "Assumed by GitHub Actions on the main branch to apply the Isaac Sim Terraform."
  assume_role_policy = data.aws_iam_policy_document.github_trust.json
}

# The main Terraform creates IAM users, EC2 templates, Lambdas, log groups and
# EventBridge rules, so the role needs write access to those five services.
resource "aws_iam_role_policy_attachment" "github_deploy" {
  for_each = toset([
    "arn:aws:iam::aws:policy/IAMFullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    "arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess",
  ])

  role       = aws_iam_role.github_deploy.name
  policy_arn = each.value
}

# Plus read/write on the state bucket and the lock table.
data "aws_iam_policy_document" "github_state" {
  statement {
    sid       = "ListStateBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.tfstate.arn]
  }

  statement {
    sid       = "ReadWriteState"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.tfstate.arn}/*"]
  }

  statement {
    sid       = "UseLockTable"
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = [aws_dynamodb_table.lock.arn]
  }
}

resource "aws_iam_role_policy" "github_state" {
  name   = "${var.project_name}-github-state"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_state.json
}

output "state_bucket" {
  value = aws_s3_bucket.tfstate.bucket
}

output "lock_table" {
  value = aws_dynamodb_table.lock.name
}

output "github_deploy_role_arn" {
  value = aws_iam_role.github_deploy.arn
}
