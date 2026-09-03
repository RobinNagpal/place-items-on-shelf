# ---------------------------------------------------------------------------
# The Isaac Sim EC2 instance
#
# Only created when create_instance = true. Terraform launches it from the same
# AWS Marketplace AMI you would pick by hand in the console, so you get the same
# machine with Isaac Sim already installed.
#
# ONE MANUAL STEP FIRST: someone with account-owner rights must subscribe to the
# AMI once (AWS Marketplace -> "NVIDIA Isaac Sim Development Workstation
# (Linux)" -> Accept Terms). Accepting a Marketplace agreement is a legal and
# billing action, so AWS does not expose it to Terraform. Skip it and the launch
# below fails with OptInRequired.
#
# After that one click, everything here is code: apply creates the instance and
# feeds its real ID straight into the IAM policy and the auto-shutdown Lambda,
# so there are no IDs to copy by hand.
# ---------------------------------------------------------------------------

# Find the newest Marketplace AMI whose name matches the filter. Used only when
# ami_id is left empty. Pin ami_id instead if you want apply to be repeatable -
# "most_recent" means a new AMI release can change what this resolves to.
#
# Known-good AMI in us-east-1 as of 2026-07-13:
#   ami-04c0e6d2f07bbddc7
#   OV-Template-aws-ubuntu-isaac_sim-20260624T103823-ceabb999-prod-l4r5drddssotm
# AMI IDs are region-specific - that one is us-east-1 only.
data "aws_ami" "isaac_sim" {
  count = var.create_instance && var.ami_id == "" ? 1 : 0

  owners      = ["aws-marketplace"]
  most_recent = true

  filter {
    name   = "name"
    values = [var.ami_name_filter]
  }

  filter {
    name   = "state"
    values = ["available"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ---------------------------------------------------------------------------
# Which network to launch into
#
# An instance and its security group MUST live in the same VPC, or the launch
# fails with "Security group ... and subnet ... belong to different networks".
# Rather than assume the default VPC, we read the VPC off the security group
# itself and launch there. That is always the right answer by construction.
# ---------------------------------------------------------------------------

data "aws_security_group" "isaac_sim" {
  count = var.create_instance ? 1 : 0
  id    = var.security_group_id
}

# Public subnets in that VPC. "Public" here means the subnet hands out a public
# IP on launch - without one there is no way to SSH or reach NICE DCV.
data "aws_subnets" "public" {
  count = var.create_instance && var.subnet_id == "" ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [data.aws_security_group.isaac_sim[0].vpc_id]
  }

  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

locals {
  # sort() makes the pick deterministic, so re-running plan does not propose
  # moving the instance to a different subnet.
  auto_subnet_id = try(sort(data.aws_subnets.public[0].ids)[0], "")
  chosen_subnet  = var.subnet_id != "" ? var.subnet_id : local.auto_subnet_id
}

resource "aws_instance" "isaac_sim" {
  count = var.create_instance ? 1 : 0

  # coalesce picks the first non-empty value. one() returns null when the data
  # source was not created, which keeps this valid in both modes - indexing
  # with [0] would blow up when the count is 0.
  ami           = coalesce(var.ami_id, one(data.aws_ami.isaac_sim[*].id))
  instance_type = var.instance_type

  # Empty means "launch with no SSH key". Terraform wants null, not "".
  key_name = var.key_pair_name != "" ? var.key_pair_name : null

  subnet_id              = local.chosen_subnet
  vpc_security_group_ids = [var.security_group_id]

  # Belt and braces: some subnets do not auto-assign, and without a public IP
  # the box is unreachable.
  associate_public_ip_address = true

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = "gp3"
    encrypted   = var.root_volume_encrypted

    # Keep the disk when the instance is terminated? No - it is a 512 GiB
    # volume costing ~$40/month, and leaving orphans behind is how surprise
    # bills happen.
    delete_on_termination = true
  }

  # Require IMDSv2. Blocks the SSRF-style attacks that can read instance
  # credentials through the metadata endpoint.
  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tags = {
    Name = "${local.name_prefix}-dev"
  }

  lifecycle {
    # Stopping and starting the instance is normal daily use, and a new AMI
    # release should not silently replace the machine (and wipe its disk) on
    # the next apply. Change ami_id deliberately when you want to rebuild.
    ignore_changes = [ami]

    precondition {
      condition     = local.chosen_subnet != ""
      error_message = "No public subnet found in the VPC that ${var.security_group_id} belongs to. Set subnet_id in terraform.tfvars to a subnet that assigns public IPs."
    }
  }
}
