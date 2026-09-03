# ---------------------------------------------------------------------------
# Auto-shutdown for the Isaac Sim instance
#
# Pieces, in the order they fire:
#
#   EventBridge rule (every hour)
#     -> Lambda function (lambda/auto_shutdown.py)
#          -> reads the instance state and uptime
#          -> calls ec2:StopInstances if a limit is crossed
#
# Two limits are enforced: a max uptime (2 hours) and a daily curfew (3 PM
# Eastern). A g6e.xlarge costs about $1.86/hour, so a forgotten instance is
# roughly $45 a day. This is the guard rail.
# ---------------------------------------------------------------------------

# Zip the Python file at plan time. Terraform re-zips automatically whenever
# the source changes, which makes the Lambda redeploy on the next apply.
data "archive_file" "auto_shutdown" {
  type        = "zip"
  source_file = "${path.module}/lambda/auto_shutdown.py"
  output_path = "${path.module}/build/auto_shutdown.zip"
}

# ---------------------------------------------------------------------------
# Execution role: what the Lambda itself is allowed to do
# ---------------------------------------------------------------------------

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

resource "aws_iam_role" "auto_shutdown" {
  name               = "${local.name_prefix}-auto-shutdown-role"
  description        = "Role assumed by the Isaac Sim auto-shutdown Lambda."
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "auto_shutdown" {
  statement {
    sid    = "WriteOwnLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["${aws_cloudwatch_log_group.auto_shutdown.arn}:*"]
  }

  statement {
    sid    = "ReadInstanceState"
    effect = "Allow"

    # DescribeInstances cannot be scoped to a single instance - AWS does not
    # support resource-level permissions on EC2 Describe* calls.
    actions   = ["ec2:DescribeInstances"]
    resources = ["*"]
  }

  statement {
    sid    = "StopIsaacSimInstance"
    effect = "Allow"

    # Stop only. The Lambda has no way to start, reboot or terminate anything.
    actions   = ["ec2:StopInstances"]
    resources = [local.instance_arn]
  }
}

resource "aws_iam_role_policy" "auto_shutdown" {
  name   = "${local.name_prefix}-auto-shutdown-policy"
  role   = aws_iam_role.auto_shutdown.id
  policy = data.aws_iam_policy_document.auto_shutdown.json
}

# ---------------------------------------------------------------------------
# Log group
#
# Created explicitly (instead of letting Lambda create it) so we control the
# retention. Without this, logs are kept forever and slowly cost money.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "auto_shutdown" {
  name              = "/aws/lambda/${local.name_prefix}-auto-shutdown"
  retention_in_days = var.log_retention_days
}

# ---------------------------------------------------------------------------
# The Lambda function
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "auto_shutdown" {
  function_name = "${local.name_prefix}-auto-shutdown"
  description   = "Stops the Isaac Sim instance after a max uptime or past the daily curfew."
  role          = aws_iam_role.auto_shutdown.arn

  filename         = data.archive_file.auto_shutdown.output_path
  source_code_hash = data.archive_file.auto_shutdown.output_base64sha256

  # "file.function" - lambda/auto_shutdown.py, function handler().
  handler = "auto_shutdown.handler"
  runtime = "python3.12"

  # boto3 is already in the runtime, so nothing to install. Two EC2 API calls
  # finish in well under 30 seconds.
  timeout     = 30
  memory_size = 128

  environment {
    variables = {
      INSTANCE_ID       = local.instance_id
      MAX_RUNTIME_HOURS = tostring(var.max_runtime_hours)
      CURFEW_HOUR       = tostring(var.curfew_hour)
      TIMEZONE          = var.curfew_timezone
      DRY_RUN           = var.auto_shutdown_dry_run ? "true" : "false"
    }
  }

  lifecycle {
    precondition {
      condition     = var.create_instance || var.instance_id != ""
      error_message = "Set create_instance = true, or paste a real instance_id into terraform.tfvars. With create_instance = false and an empty instance_id the auto-shutdown would watch nothing."
    }
  }

  # Make sure the log group exists before the function writes to it.
  depends_on = [
    aws_iam_role_policy.auto_shutdown,
    aws_cloudwatch_log_group.auto_shutdown,
  ]
}

# ---------------------------------------------------------------------------
# The schedule
#
# cron(0 * * * ? *) runs the checker at the top of every hour, 24 times a day.
# Because it is a periodic check and not a timer, a shutdown lands somewhere
# inside the hour after a limit is crossed - an instance started at 09:10 is
# stopped at the 12:00 run, not exactly at 11:10. Shorten
# check_schedule_expression if that matters. Use cron() rather than rate():
# rate() counts from when the rule was created, so it drifts off the clock.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "auto_shutdown" {
  name                = "${local.name_prefix}-auto-shutdown-schedule"
  description         = "Runs the Isaac Sim auto-shutdown check on a fixed interval."
  schedule_expression = var.check_schedule_expression
  state               = var.auto_shutdown_enabled ? "ENABLED" : "DISABLED"
}

resource "aws_cloudwatch_event_target" "auto_shutdown" {
  rule      = aws_cloudwatch_event_rule.auto_shutdown.name
  target_id = "${local.name_prefix}-auto-shutdown-lambda"
  arn       = aws_lambda_function.auto_shutdown.arn
}

# EventBridge is a separate service, so it needs explicit permission to invoke
# the function. Without this the rule fires and silently does nothing.
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_shutdown.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.auto_shutdown.arn
}
