# What to hand to the developers after `terraform apply`.
#
# Values marked `sensitive` are hidden in the normal output. Read them with
# `terraform output -json <name>`.
# Send them over a secure channel, never plain email.

output "developer_user_names" {
  description = "IAM user names created for the developers."
  value       = keys(aws_iam_user.developers)
}

output "operators_group_name" {
  description = "IAM group that holds the launch / start / stop permissions. Every developer and every admin_user_names entry is a member."
  value       = aws_iam_group.operators.name
}

output "console_signin_url" {
  description = "AWS Console sign-in URL for this account."
  value       = "https://${data.aws_caller_identity.current.account_id}.signin.aws.amazon.com/console"
}

# The three outputs below are maps keyed by user name. Read one entry with:
#   terraform output -json developer_console_passwords | jq -r '."robin-robotics"'

output "developer_console_passwords" {
  description = "One-time console password per developer. Each must change it on first sign-in."
  value       = { for name, profile in aws_iam_user_login_profile.developers : name => profile.password }
  sensitive   = true
}

output "developer_access_key_ids" {
  description = "Access key ID per developer, for the AWS CLI."
  value       = { for name, key in aws_iam_access_key.developers : name => key.id }
}

output "developer_secret_access_keys" {
  description = "Secret access key per developer, for the AWS CLI."
  value       = { for name, key in aws_iam_access_key.developers : name => key.secret }
  sensitive   = true
}

output "security_group_id" {
  description = "Security group on the Isaac Sim instance. Operators edit its inbound rules to match their IP."
  value       = aws_security_group.isaac_sim.id
}

output "ssh_private_key_pem" {
  description = "Private key for the launch template's key pair. Save as ~/.ssh/isaac-sim-key.pem, chmod 400."
  value       = tls_private_key.isaac_sim.private_key_pem
  sensitive   = true
}

output "launch_template_id" {
  description = "Launch template operators must use to create the Isaac Sim instance."
  value       = aws_launch_template.isaac_sim.id
}

output "launch_command" {
  description = "The one CLI command that creates the Isaac Sim instance."
  value       = "aws ec2 run-instances --region ${var.aws_region} --launch-template LaunchTemplateId=${aws_launch_template.isaac_sim.id}"
}

output "auto_shutdown_function_name" {
  description = "Lambda that stops the instance. Invoke it manually to test."
  value       = aws_lambda_function.auto_shutdown.function_name
}

output "single_instance_guard_function_name" {
  description = "Lambda that terminates any second Isaac Sim instance. Invoke it manually to test."
  value       = aws_lambda_function.single_instance_guard.function_name
}

output "auto_shutdown_log_group" {
  description = "CloudWatch log group where every shutdown check writes its decision."
  value       = aws_cloudwatch_log_group.auto_shutdown.name
}

output "auto_shutdown_rules_summary" {
  description = "Plain-English summary of the rules currently in effect."
  value = join(" ", [
    "Checked ${var.check_schedule_expression}.",
    "Stops after ${var.max_runtime_hours}h of uptime",
    "or at/after ${var.curfew_hour}:00 ${var.curfew_timezone}.",
    var.auto_shutdown_dry_run ? "DRY RUN - nothing is actually stopped." : "Live.",
    var.auto_shutdown_enabled ? "" : "SCHEDULE DISABLED.",
  ])
}
