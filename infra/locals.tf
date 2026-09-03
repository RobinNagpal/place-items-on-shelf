# ARNs we build by hand. We only have the IDs, and both IAM policies below need
# full ARNs to scope permissions down to these two resources and nothing else.

locals {
  account_id = data.aws_caller_identity.current.account_id

  instance_arn       = "arn:aws:ec2:${var.aws_region}:${local.account_id}:instance/${var.instance_id}"
  security_group_arn = "arn:aws:ec2:${var.aws_region}:${local.account_id}:security-group/${var.security_group_id}"

  # One prefix for every resource name, so everything sorts together in the console.
  name_prefix = var.project_name
}
