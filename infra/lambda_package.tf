# ---------------------------------------------------------------------------
# One zip for both Lambdas
#
# The two functions share lambda/common.py, so they ship in the same zip and
# just point at different handlers. Terraform re-zips whenever any of the three
# files changes, which makes both functions redeploy on the next apply.
#
# Listing the files one by one (instead of zipping the whole folder) keeps
# stray __pycache__ folders from a local syntax check out of the package.
# ---------------------------------------------------------------------------

data "archive_file" "lambda" {
  type        = "zip"
  output_path = "${path.module}/build/lambda.zip"

  source {
    filename = "common.py"
    content  = file("${path.module}/lambda/common.py")
  }

  source {
    filename = "auto_shutdown.py"
    content  = file("${path.module}/lambda/auto_shutdown.py")
  }

  source {
    filename = "single_instance_guard.py"
    content  = file("${path.module}/lambda/single_instance_guard.py")
  }
}

# Both Lambdas run as a Lambda service role. Same trust policy for each.
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}
