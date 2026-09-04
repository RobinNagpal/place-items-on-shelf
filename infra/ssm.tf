# ---------------------------------------------------------------------------
# Session Manager access
#
# Session Manager gives an operator a shell on the instance with no SSH key and
# no inbound port. The instance's SSM Agent dials OUT to AWS over HTTPS, the
# operator's CLI dials out too, and AWS joins the two ends together.
#
# Why we want it: the SSH private key only exists in Terraform state, and
# developers cannot read that bucket. Before this file, a developer could
# launch the instance but never log in without the account owner mailing them
# a .pem. Now they need nothing from anyone.
#
# It takes TWO halves, and both are required:
#
#   1. The INSTANCE needs an IAM role, so its agent may register itself as a
#      managed node. Without it the instance never appears in SSM and
#      start-session fails with TargetNotConnected.
#   2. The OPERATOR needs ssm:StartSession, or the call is denied long before
#      it reaches the instance.
#
# Note for whoever reviews the CI run: Session Manager creates no SSM
# resources, only IAM ones. That is why this applies through GitHub Actions.
# The deploy role has IAMFullAccess and AmazonEC2FullAccess but no ssm:* write
# permissions, so anything that created, say, an SSM parameter would fail here.
# ---------------------------------------------------------------------------

# --- Half 1: the role the instance itself wears ----------------------------

data "aws_iam_policy_document" "instance_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance" {
  name               = "${local.name_prefix}-instance"
  description        = "Worn by the Isaac Sim instance. Lets its SSM Agent register as a managed node so operators can open a session."
  assume_role_policy = data.aws_iam_policy_document.instance_assume_role.json
}

# AWS's own policy. It is the minimum an SSM Agent needs to check in, and it
# grants nothing else - no S3, no EC2, no ability to act on the account.
resource "aws_iam_role_policy_attachment" "instance_ssm_core" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# EC2 attaches roles through an instance profile, never directly. This is the
# wrapper the launch template points at.
resource "aws_iam_instance_profile" "instance" {
  name = "${local.name_prefix}-instance"
  role = aws_iam_role.instance.name
}

# --- Half 2: what an operator is allowed to do with sessions ---------------

data "aws_iam_policy_document" "session_manager" {
  statement {
    sid       = "StartSessionOnIsaacSimInstancesOnly"
    effect    = "Allow"
    actions   = ["ssm:StartSession"]
    resources = [local.any_instance_arn]

    # Same tag gate as every other policy here, so a session can only ever be
    # opened on the Isaac Sim machine and never on someone else's instance.
    condition {
      test     = "StringEquals"
      variable = "ssm:resourceTag/${local.instance_tag_key}"
      values   = [local.instance_tag_value]
    }
  }

  statement {
    sid     = "UseTheTwoSessionDocuments"
    effect  = "Allow"
    actions = ["ssm:StartSession"]

    # StartSession is checked against the instance AND the document that shapes
    # the session. RunShell is the plain terminal and is what you get when
    # --document-name is omitted; PortForwarding is what tunnels DCV's 8443 to
    # the operator's laptop. RunShell is listed twice because the document is
    # AWS-owned until someone edits the account's session preferences, at which
    # point it becomes an account-owned copy with a different ARN.
    resources = [
      "arn:aws:ssm:${var.aws_region}::document/SSM-SessionManagerRunShell",
      "arn:aws:ssm:${var.aws_region}:${local.account_id}:document/SSM-SessionManagerRunShell",
      "arn:aws:ssm:${var.aws_region}::document/AWS-StartPortForwardingSession",
    ]
  }

  statement {
    sid     = "EndOnlyYourOwnSessions"
    effect  = "Allow"
    actions = ["ssm:TerminateSession", "ssm:ResumeSession"]

    # Session IDs are "<iam-user-name>-<random>", so this wildcard lets you
    # close your own session and nobody else's.
    resources = ["arn:aws:ssm:${var.aws_region}:${local.account_id}:session/$${aws:username}-*"]
  }

  statement {
    sid    = "SeeWhetherSsmCanReachTheInstance"
    effect = "Allow"

    # These Describe calls do not support resource-level permissions, so they
    # have to be "*". Read-only, so the blast radius is just visibility. The
    # scripts use DescribeInstanceInformation to wait for the agent to come up
    # after a launch.
    actions = [
      "ssm:DescribeSessions",
      "ssm:DescribeInstanceInformation",
      "ssm:GetConnectionStatus",
    ]

    resources = ["*"]
  }

  statement {
    sid       = "PassTheInstanceRoleAtLaunch"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.instance.arn]

    # Easy to miss: attaching a role to an instance counts as "passing" that
    # role, and IAM checks it against the CALLER of RunInstances. It is checked
    # even though the profile is baked into the launch template rather than
    # given on the command line. Without this statement every launch fails with
    # "not authorized to perform: iam:PassRole".
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "session_manager" {
  name        = "${local.name_prefix}-session-manager"
  description = "Open a Session Manager shell or port-forward on the tagged Isaac Sim instance, and pass the instance role at launch."
  policy      = data.aws_iam_policy_document.session_manager.json
}

resource "aws_iam_group_policy_attachment" "session_manager" {
  group      = aws_iam_group.operators.name
  policy_arn = aws_iam_policy.session_manager.arn
}
