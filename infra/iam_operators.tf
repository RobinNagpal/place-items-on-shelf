# ---------------------------------------------------------------------------
# The operators group
#
# Everyone who is allowed to run the Isaac Sim instance - the developer users
# created in iam_user.tf and any existing admin users listed in
# var.admin_user_names - is a member of this group. Permissions live on the
# group, not on the users, so both get exactly the same rights.
#
# What a member can do:
#   - see EC2 (read-only)
#   - create the Isaac Sim instance, but only from the launch template
#   - start / stop / reboot / terminate instances that carry the Purpose tag
#   - edit inbound rules on the Isaac Sim security group
#
# What a member cannot do: launch anything else, touch untagged instances,
# change the launch template, or see or change anything outside EC2.
#
# "At most one instance" is NOT enforced here. IAM cannot count. The
# single-instance guard Lambda (single_instance_guard.tf) does that.
# ---------------------------------------------------------------------------

resource "aws_iam_group" "operators" {
  name = "${local.name_prefix}-operators"
}

# One membership per developer user. for_each over the same set that
# iam_user.tf creates the users from, so the two always line up.
resource "aws_iam_user_group_membership" "developers" {
  for_each = aws_iam_user.developers

  user   = each.value.name
  groups = [aws_iam_group.operators.name]
}

# Existing users (e.g. the manager's own admin user). for_each builds one
# membership per name in the list. Nothing else about those users is managed.
resource "aws_iam_user_group_membership" "admins" {
  for_each = toset(var.admin_user_names)

  user   = each.value
  groups = [aws_iam_group.operators.name]
}

# ---------------------------------------------------------------------------
# Policy 1: read-only view of EC2
#
# AWS's own managed policy. Needed so the console can list instances, show
# status checks, display the public IP, and show the launch template.
# ---------------------------------------------------------------------------

resource "aws_iam_group_policy_attachment" "ec2_read_only" {
  group      = aws_iam_group.operators.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

# ---------------------------------------------------------------------------
# Policy 2: create and operate the Isaac Sim instance
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "operate_instance" {
  # RunInstances is unusual: one API call is checked against several
  # resources at once (the template, the instance, its disk, its network
  # card, the AMI, the key pair, ...). Every one of them needs an Allow, so
  # the permission is split into the three statements below.

  statement {
    sid    = "LaunchOnlyFromTheIsaacSimTemplate"
    effect = "Allow"

    actions   = ["ec2:RunInstances"]
    resources = [aws_launch_template.isaac_sim.arn]
  }

  statement {
    sid    = "LaunchOnlyAnIsaacSimShapedInstance"
    effect = "Allow"

    actions   = ["ec2:RunInstances"]
    resources = [local.any_instance_arn]

    # The instance must come from our template ...
    condition {
      test     = "ArnLike"
      variable = "ec2:LaunchTemplate"
      values   = [aws_launch_template.isaac_sim.arn]
    }

    # ... be the approved size (a template launch can override the type) ...
    condition {
      test     = "StringEquals"
      variable = "ec2:InstanceType"
      values   = [var.instance_type]
    }

    # ... and nobody may swap the Purpose tag for a different value on the
    # way in, which would hide the instance from the two Lambdas.
    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:RequestTag/${local.instance_tag_key}"
      values   = [local.instance_tag_value]
    }
  }

  statement {
    sid    = "LaunchSupportingResources"
    effect = "Allow"

    actions = ["ec2:RunInstances"]

    # The AMI, key pair and security group are pinned to the exact ones the
    # template uses, so a launch cannot override them. Volumes, network cards
    # and subnets have no useful identity before launch, so they stay open.
    resources = [
      local.ami_arn,
      local.key_pair_arn,
      local.security_group_arn,
      local.any_volume_arn,
      local.any_eni_arn,
      local.any_subnet_arn,
    ]
  }

  statement {
    sid    = "TagTheInstanceAtLaunch"
    effect = "Allow"

    # The template stamps tags on the new instance and disk. That is a
    # CreateTags call under the hood, allowed only as part of RunInstances.
    actions = ["ec2:CreateTags"]

    resources = [
      local.any_instance_arn,
      local.any_volume_arn,
      local.any_eni_arn,
    ]

    condition {
      test     = "StringEquals"
      variable = "ec2:CreateAction"
      values   = ["RunInstances"]
    }
  }

  statement {
    sid    = "OperateTaggedIsaacSimInstances"
    effect = "Allow"

    actions = [
      "ec2:StartInstances",
      "ec2:StopInstances",
      "ec2:RebootInstances",
      "ec2:TerminateInstances",
    ]

    resources = [local.any_instance_arn]

    # Only instances carrying the Purpose tag. Any other instance is denied.
    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/${local.instance_tag_key}"
      values   = [local.instance_tag_value]
    }
  }
}

resource "aws_iam_policy" "operate_instance" {
  name        = "${local.name_prefix}-operate-instance"
  description = "Launch the Isaac Sim workstation from its template; start, stop, reboot and terminate only tagged Isaac Sim instances."
  policy      = data.aws_iam_policy_document.operate_instance.json
}

resource "aws_iam_group_policy_attachment" "operate_instance" {
  group      = aws_iam_group.operators.name
  policy_arn = aws_iam_policy.operate_instance.arn
}

# ---------------------------------------------------------------------------
# Policy 3: edit the Isaac Sim security group
#
# SSH (22) and NICE DCV (8443) are locked to the operator's home IP. Home IPs
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
  description = "Edit inbound rules on the Isaac Sim security group so operators can refresh their home IP."
  policy      = data.aws_iam_policy_document.manage_security_group.json
}

resource "aws_iam_group_policy_attachment" "manage_security_group" {
  group      = aws_iam_group.operators.name
  policy_arn = aws_iam_policy.manage_security_group.arn
}
