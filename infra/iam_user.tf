# ---------------------------------------------------------------------------
# The developer's IAM user
#
# The idea: they can see EC2, and they can start/stop/reboot exactly one
# instance and edit exactly one security group. They cannot touch anything else
# in the account.
# ---------------------------------------------------------------------------

resource "aws_iam_user" "developer" {
  name = var.developer_user_name

  # Refuse to delete the user while it still has keys or policies attached.
  # Prevents a surprise `terraform destroy` from silently wiping credentials.
  force_destroy = false
}

# Console password. `count` is Terraform's way of saying "only build this if the
# flag is on". password_reset_required means AWS makes them pick their own
# password the first time they sign in.
resource "aws_iam_user_login_profile" "developer" {
  count = var.create_console_access ? 1 : 0

  user                    = aws_iam_user.developer.name
  password_length         = 20
  password_reset_required = true

  # After the first apply the password lives in state, not in AWS. Ignoring
  # changes stops Terraform from resetting it every time they change it.
  lifecycle {
    ignore_changes = [password_length, password_reset_required]
  }
}

# Access key for the AWS CLI (aws ec2 start-instances, etc.).
resource "aws_iam_access_key" "developer" {
  count = var.create_access_key ? 1 : 0

  user = aws_iam_user.developer.name
}

# ---------------------------------------------------------------------------
# Policy 1: read-only view of EC2
#
# AWS's own managed policy. Needed so the console can list instances, show
# status checks, and display the public IP.
# ---------------------------------------------------------------------------

resource "aws_iam_user_policy_attachment" "ec2_read_only" {
  user       = aws_iam_user.developer.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

# ---------------------------------------------------------------------------
# Policy 2: operate the one Isaac Sim instance
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "operate_instance" {
  statement {
    sid    = "StartStopRebootIsaacSimInstance"
    effect = "Allow"

    actions = [
      "ec2:StartInstances",
      "ec2:StopInstances",
      "ec2:RebootInstances",
    ]

    # Scoped to a single instance ARN. Any other instance ID is denied.
    resources = [local.instance_arn]
  }
}

resource "aws_iam_policy" "operate_instance" {
  name        = "${local.name_prefix}-operate-instance"
  description = "Start, stop and reboot only the Isaac Sim workstation."
  policy      = data.aws_iam_policy_document.operate_instance.json
}

resource "aws_iam_user_policy_attachment" "operate_instance" {
  user       = aws_iam_user.developer.name
  policy_arn = aws_iam_policy.operate_instance.arn
}

# ---------------------------------------------------------------------------
# Policy 3: edit the Isaac Sim security group
#
# SSH (22) and NICE DCV (8443) are locked to the developer's home IP. Home IPs
# change, so they need to be able to fix the rules themselves instead of
# messaging the manager every time.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "manage_security_group" {
  statement {
    sid    = "EditIsaacSimSecurityGroupRules"
    effect = "Allow"

    actions = [
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:ModifySecurityGroupRules",
      "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
    ]

    resources = [local.security_group_arn]
  }

  statement {
    sid    = "ReadSecurityGroupRules"
    effect = "Allow"

    # Describe* calls do not support resource-level permissions, so this has to
    # be "*". It is read-only, so the blast radius is just visibility.
    actions = [
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSecurityGroupRules",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "manage_security_group" {
  name        = "${local.name_prefix}-manage-security-group"
  description = "Edit inbound rules on the Isaac Sim security group so the developer can refresh their home IP."
  policy      = data.aws_iam_policy_document.manage_security_group.json
}

resource "aws_iam_user_policy_attachment" "manage_security_group" {
  user       = aws_iam_user.developer.name
  policy_arn = aws_iam_policy.manage_security_group.arn
}

# ---------------------------------------------------------------------------
# Policy 4: let the user look after their own credentials
#
# Without this they cannot change the temporary password AWS hands them, or set
# up MFA on their own account.
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
  description = "Let the developer change their own password and manage their own MFA device."
  policy      = data.aws_iam_policy_document.self_service_credentials.json
}

resource "aws_iam_user_policy_attachment" "self_service_credentials" {
  user       = aws_iam_user.developer.name
  policy_arn = aws_iam_policy.self_service_credentials.arn
}
