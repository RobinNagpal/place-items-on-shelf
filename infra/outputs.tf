# What to hand to the developer after `terraform apply`.
#
# Values marked `sensitive` are hidden in the normal output. Read them with:
#   terraform output -raw developer_console_password
# Send them over a secure channel, never plain email.

output "developer_user_name" {
  description = "IAM user name created for the developer."
  value       = aws_iam_user.developer.name
}

output "developer_console_signin_url" {
  description = "AWS Console sign-in URL for this account."
  value       = "https://${data.aws_caller_identity.current.account_id}.signin.aws.amazon.com/console"
}

output "developer_console_password" {
  description = "One-time console password. The user must change it on first sign-in."
  value       = var.create_console_access ? aws_iam_user_login_profile.developer[0].password : null
  sensitive   = true
}

output "developer_access_key_id" {
  description = "Access key ID for the AWS CLI."
  value       = var.create_access_key ? aws_iam_access_key.developer[0].id : null
}

output "developer_secret_access_key" {
  description = "Secret access key for the AWS CLI."
  value       = var.create_access_key ? aws_iam_access_key.developer[0].secret : null
  sensitive   = true
}

output "auto_shutdown_function_name" {
  description = "Lambda that stops the instance. Invoke it manually to test."
  value       = aws_lambda_function.auto_shutdown.function_name
}

output "auto_shutdown_log_group" {
  description = "CloudWatch log group where every check writes its decision."
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

# ---------------------------------------------------------------------------
# The instance
# ---------------------------------------------------------------------------

output "instance_id" {
  description = "The Isaac Sim instance being managed - created by Terraform or pasted in, depending on create_instance."
  value       = local.instance_id
}

output "instance_public_ip" {
  description = "Public IP for SSH and NICE DCV. Null while the instance is stopped; it changes on every start unless you attach an Elastic IP."
  value       = one(aws_instance.isaac_sim[*].public_ip)
}

# A stopped instance has no public IP, and interpolating null into a string is
# a hard error - so fall back to a placeholder rather than breaking `output`.
output "connect_hint" {
  description = "How to get on the box once it is running."
  value = var.create_instance ? join(" ", [
    "SSH: ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${coalesce(one(aws_instance.isaac_sim[*].public_ip), "<start the instance to get an IP>")}",
    "| NICE DCV: port 8443 on that IP (set a Linux password first with 'sudo passwd ubuntu').",
  ]) : "Instance was launched by hand - look up its public IP in the EC2 console."
}
