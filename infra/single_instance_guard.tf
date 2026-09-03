# ---------------------------------------------------------------------------
# Single-instance guard
#
# Operators can launch the Isaac Sim instance themselves (iam_operators.tf).
# IAM can restrict *what* they launch but not *how many*. This Lambda closes
# that gap:
#
#   EventBridge rule (any instance enters "pending")
#     -> Lambda function (lambda/single_instance_guard.py)
#          -> lists every live instance with the Purpose tag
#          -> if more than one: keeps the oldest, terminates the rest
#
# "pending" is the first state after both launch and start, so a second
# launch is caught within seconds, before it has finished booting. The hourly
# auto-shutdown schedule also invokes the guard as a safety net.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "single_instance_guard" {
  name               = "${local.name_prefix}-single-instance-guard-role"
  description        = "Role assumed by the Isaac Sim single-instance guard Lambda."
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "single_instance_guard" {
  statement {
    sid    = "WriteOwnLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["${aws_cloudwatch_log_group.single_instance_guard.arn}:*"]
  }

  statement {
    sid    = "ReadInstanceState"
    effect = "Allow"

    actions   = ["ec2:DescribeInstances"]
    resources = ["*"]
  }

  statement {
    sid    = "TerminateTaggedIsaacSimInstances"
    effect = "Allow"

    # Terminate only, and only instances carrying the Purpose tag. An untagged
    # instance - anything else in the account - is out of reach.
    actions   = ["ec2:TerminateInstances"]
    resources = [local.any_instance_arn]

    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/${local.instance_tag_key}"
      values   = [local.instance_tag_value]
    }
  }
}

resource "aws_iam_role_policy" "single_instance_guard" {
  name   = "${local.name_prefix}-single-instance-guard-policy"
  role   = aws_iam_role.single_instance_guard.id
  policy = data.aws_iam_policy_document.single_instance_guard.json
}

resource "aws_cloudwatch_log_group" "single_instance_guard" {
  name              = "/aws/lambda/${local.name_prefix}-single-instance-guard"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "single_instance_guard" {
  function_name = "${local.name_prefix}-single-instance-guard"
  description   = "Terminates any Isaac Sim instance beyond the first one."
  role          = aws_iam_role.single_instance_guard.arn

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  handler = "single_instance_guard.handler"
  runtime = "python3.12"

  timeout     = 30
  memory_size = 128

  environment {
    variables = {
      TAG_KEY   = local.instance_tag_key
      TAG_VALUE = local.instance_tag_value
      DRY_RUN   = var.single_instance_guard_dry_run ? "true" : "false"
    }
  }

  depends_on = [
    aws_iam_role_policy.single_instance_guard,
    aws_cloudwatch_log_group.single_instance_guard,
  ]
}

# ---------------------------------------------------------------------------
# Trigger 1: any instance in the account enters "pending"
#
# The rule cannot filter on tags, so it fires for every instance launch or
# start in the region. The Lambda does the tag filtering. At this account's
# volume that is a handful of free invocations a day.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "instance_pending" {
  name        = "${local.name_prefix}-instance-pending"
  description = "Fires whenever an EC2 instance starts booting, so the guard can count Isaac Sim instances."

  event_pattern = jsonencode({
    source        = ["aws.ec2"]
    "detail-type" = ["EC2 Instance State-change Notification"]
    detail = {
      state = ["pending"]
    }
  })
}

resource "aws_cloudwatch_event_target" "guard_on_pending" {
  rule      = aws_cloudwatch_event_rule.instance_pending.name
  target_id = "${local.name_prefix}-single-instance-guard-lambda"
  arn       = aws_lambda_function.single_instance_guard.arn
}

resource "aws_lambda_permission" "guard_allow_pending_rule" {
  statement_id  = "AllowExecutionFromPendingRule"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.single_instance_guard.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.instance_pending.arn
}

# ---------------------------------------------------------------------------
# Trigger 2: the hourly schedule (safety net)
#
# Reuses the auto-shutdown schedule rule. If an event is ever missed, or the
# guard was in dry-run when a second instance appeared, the next hourly sweep
# catches it. Note this trigger pauses together with auto_shutdown_enabled.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_event_target" "guard_on_schedule" {
  rule      = aws_cloudwatch_event_rule.auto_shutdown.name
  target_id = "${local.name_prefix}-single-instance-guard-sweep"
  arn       = aws_lambda_function.single_instance_guard.arn
}

resource "aws_lambda_permission" "guard_allow_schedule_rule" {
  statement_id  = "AllowExecutionFromScheduleRule"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.single_instance_guard.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.auto_shutdown.arn
}
