# ARNs we build by hand. We only have the IDs, and both IAM policies below need
# full ARNs to scope permissions down to these two resources and nothing else.

locals {
  account_id = data.aws_caller_identity.current.account_id

  # Where the instance ID comes from depends on who created the instance:
  #   create_instance = true  -> the one Terraform just launched
  #   create_instance = false -> the ID you pasted into terraform.tfvars
  # Everything downstream (the IAM policy, the Lambda's INSTANCE_ID) reads this
  # single value, so the two modes cannot drift apart.
  instance_id = var.create_instance ? one(aws_instance.isaac_sim[*].id) : var.instance_id

  instance_arn       = "arn:aws:ec2:${var.aws_region}:${local.account_id}:instance/${local.instance_id}"
  security_group_arn = "arn:aws:ec2:${var.aws_region}:${local.account_id}:security-group/${var.security_group_id}"

  # One prefix for every resource name, so everything sorts together in the console.
  name_prefix = var.project_name
}
