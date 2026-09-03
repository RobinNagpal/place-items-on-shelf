# ---------------------------------------------------------------------------
# The developers' IAM users
#
# One user per name in var.developer_user_names (up to four). Each gets a
# console password, a CLI access key, and one policy that lets it look after
# its own credentials. Everything to do with EC2 comes from the operators
# group in iam_operators.tf.
#
# `for_each` builds one copy of each resource per name. An empty list builds
# nothing. Removing a name from the list deletes that user on the next apply.
# ---------------------------------------------------------------------------

resource "aws_iam_user" "developers" {
  for_each = toset(var.developer_user_names)

  name = each.value

  # Refuse to delete the user while it still has keys or policies attached.
  # Prevents a surprise `terraform destroy` from silently wiping credentials.
  force_destroy = false
}

# Console password. Built only when the flag is on. password_reset_required
# means AWS makes them pick their own password the first time they sign in.
resource "aws_iam_user_login_profile" "developers" {
  for_each = var.create_console_access ? aws_iam_user.developers : {}

  user                    = each.value.name
  password_length         = 20
  password_reset_required = true

  # After the first apply the password lives in state, not in AWS. Ignoring
  # changes stops Terraform from resetting it every time they change it.
  lifecycle {
    ignore_changes = [password_length, password_reset_required]
  }
}

# Access key for the AWS CLI (aws ec2 run-instances, start-instances, etc.).
resource "aws_iam_access_key" "developers" {
  for_each = var.create_access_key ? aws_iam_user.developers : {}

  user = each.value.name
}

# ---------------------------------------------------------------------------
# Let each user look after their own credentials
#
# Without this they cannot change the temporary password AWS hands them, or set
# up MFA on their own account. The policy uses ${aws:username}, so one policy
# serves every developer and each can only touch their own user.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "self_service_credentials" {
  statement {
    sid    = "ViewOwnUser"
    effect = "Allow"

    actions = [
      "iam:GetUser",
      "iam:ListMFADevices",
      "iam:ListAccessKeys",
    ]

    resources = ["arn:aws:iam::${local.account_id}:user/$${aws:username}"]
  }

  statement {
    sid       = "ChangeOwnPassword"
    effect    = "Allow"
    actions   = ["iam:ChangePassword"]
    resources = ["arn:aws:iam::${local.account_id}:user/$${aws:username}"]
  }

  statement {
    sid       = "ReadAccountPasswordPolicy"
    effect    = "Allow"
    actions   = ["iam:GetAccountPasswordPolicy"]
    resources = ["*"]
  }

  statement {
    sid    = "ManageOwnMFADevice"
    effect = "Allow"

    actions = [
      "iam:CreateVirtualMFADevice",
      "iam:EnableMFADevice",
      "iam:ResyncMFADevice",
      "iam:DeleteVirtualMFADevice",
    ]

    resources = [
      "arn:aws:iam::${local.account_id}:mfa/$${aws:username}",
      "arn:aws:iam::${local.account_id}:user/$${aws:username}",
    ]
  }
}

resource "aws_iam_policy" "self_service_credentials" {
  name        = "${local.name_prefix}-self-service-credentials"
  description = "Let a developer change their own password and manage their own MFA device."
  policy      = data.aws_iam_policy_document.self_service_credentials.json
}

resource "aws_iam_user_policy_attachment" "self_service_credentials" {
  for_each = aws_iam_user.developers

  user       = each.value.name
  policy_arn = aws_iam_policy.self_service_credentials.arn
}
