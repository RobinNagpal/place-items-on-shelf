# Values shared by more than one file.
#
# The Isaac Sim instance is no longer identified by a hard-coded instance ID.
# Operators can terminate it and launch a fresh one, so the ID changes over
# time. Instead, every Isaac Sim instance carries one tag (Purpose = isaac-sim)
# and every permission and every Lambda is scoped to that tag.

locals {
  account_id = data.aws_caller_identity.current.account_id

  # The marker tag. Stamped on the instance by the launch template, required by
  # the IAM policies, and searched for by both Lambdas.
  instance_tag_key   = "Purpose"
  instance_tag_value = var.project_name

  # "Any instance in this account and region". The policies pair this with a
  # tag condition so it really means "any Isaac Sim instance".
  any_instance_arn = "arn:aws:ec2:${var.aws_region}:${local.account_id}:instance/*"
  any_volume_arn   = "arn:aws:ec2:${var.aws_region}:${local.account_id}:volume/*"
  any_eni_arn      = "arn:aws:ec2:${var.aws_region}:${local.account_id}:network-interface/*"
  any_subnet_arn   = "arn:aws:ec2:${var.aws_region}:${local.account_id}:subnet/*"

  # The exact resources the launch template points at. The IAM policy pins
  # RunInstances to these three so a launch cannot swap any of them.
  security_group_arn = aws_security_group.isaac_sim.arn
  key_pair_arn       = aws_key_pair.isaac_sim.arn
  ami_arn            = "arn:aws:ec2:${var.aws_region}::image/${var.ami_id}"

  # One prefix for every resource name, so everything sorts together in the console.
  name_prefix = var.project_name
}
