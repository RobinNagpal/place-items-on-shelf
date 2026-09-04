# ---------------------------------------------------------------------------
# The launch template
#
# This is the one recipe for creating the Isaac Sim instance. It pins the AMI,
# the instance type, the key pair, the security group, the disk size, and the
# Purpose tag. Operators can only call RunInstances *through* this template
# (see iam_operators.tf), and they cannot edit the template, so every instance
# they create comes out looking the same.
# ---------------------------------------------------------------------------

# Look the AMI up so we know its root device name. Different AMIs mount the root
# disk at different names (/dev/sda1 vs /dev/xvda). If we guessed wrong, the
# block_device_mappings below would add a second disk instead of resizing the
# root one. This lookup also fails the plan early if the AMI ID is a typo.
data "aws_ami" "isaac_sim" {
  filter {
    name   = "image-id"
    values = [var.ami_id]
  }
}

resource "aws_launch_template" "isaac_sim" {
  name        = "${local.name_prefix}-workstation"
  description = "Isaac Sim workstation. Operators may only launch instances from this template."

  image_id      = var.ami_id
  instance_type = var.instance_type
  key_name      = aws_key_pair.isaac_sim.key_name

  # Lets the instance's SSM Agent register itself, which is what makes
  # `aws ssm start-session` work and removes the need to hand out the SSH
  # private key. Operators need iam:PassRole on the role behind this profile
  # or RunInstances is denied outright - see ssm.tf.
  iam_instance_profile {
    name = aws_iam_instance_profile.instance.name
  }

  # Stopping from inside the OS (sudo shutdown) stops the instance instead of
  # terminating it, so a careless shutdown does not delete the disk.
  instance_initiated_shutdown_behavior = "stop"

  # Security group goes here when no subnet is given (default VPC), or inside
  # network_interfaces when one is. AWS refuses both at once.
  vpc_security_group_ids = var.subnet_id == null ? [aws_security_group.isaac_sim.id] : null

  dynamic "network_interfaces" {
    for_each = var.subnet_id == null ? [] : [var.subnet_id]

    content {
      device_index                = 0
      subnet_id                   = network_interfaces.value
      security_groups             = [aws_security_group.isaac_sim.id]
      associate_public_ip_address = true
    }
  }

  block_device_mappings {
    device_name = data.aws_ami.isaac_sim.root_device_name

    ebs {
      volume_size           = var.root_volume_size_gb
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  # Require IMDSv2. Blocks the SSRF-style attacks that can read instance
  # credentials through the metadata endpoint.
  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  # The Purpose tag is what makes an instance "the Isaac Sim instance". The IAM
  # policies, the auto-shutdown and the single-instance guard all key off it.
  tag_specifications {
    resource_type = "instance"

    tags = {
      Name                     = var.instance_name
      (local.instance_tag_key) = local.instance_tag_value
    }
  }

  tag_specifications {
    resource_type = "volume"

    tags = {
      Name                     = var.instance_name
      (local.instance_tag_key) = local.instance_tag_value
    }
  }

  # Launch from "$Latest" by default, so re-applying with a new instance type
  # or disk size takes effect on the next launch without any extra flag.
  update_default_version = true
}
