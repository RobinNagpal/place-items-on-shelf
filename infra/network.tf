# ---------------------------------------------------------------------------
# Security group and SSH key pair for the Isaac Sim instance
#
# Both used to be made by hand. Terraform makes them now so a fresh account
# needs no clicking before `terraform apply`.
# ---------------------------------------------------------------------------

# The VPC the instance lives in. The default VPC unless a subnet was given.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnet" "chosen" {
  count = var.subnet_id == null ? 0 : 1
  id    = var.subnet_id
}

resource "aws_security_group" "isaac_sim" {
  name        = "${local.name_prefix}-sg"
  description = "SSH and NICE DCV into the Isaac Sim workstation. Operators edit the sources to match their home IP."
  vpc_id      = var.subnet_id == null ? data.aws_vpc.default.id : data.aws_subnet.chosen[0].vpc_id

  # Ports 22 (SSH) and 8443 (NICE DCV) from each allowed CIDR. With an empty
  # list, no inbound rule is created and operators add their own IP.
  dynamic "ingress" {
    for_each = { for pair in setproduct([22, 8443], var.ssh_dcv_allowed_cidrs) : "${pair[0]}-${pair[1]}" => pair }

    content {
      description = ingress.value[0] == 22 ? "SSH" : "NICE DCV"
      from_port   = ingress.value[0]
      to_port     = ingress.value[0]
      protocol    = "tcp"
      cidr_blocks = [ingress.value[1]]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Operators change the inbound rules by hand whenever their IP changes.
  # Ignoring ingress here stops the next `terraform apply` from undoing that.
  lifecycle {
    ignore_changes = [ingress]
  }

  tags = {
    Name = "${local.name_prefix}-sg"
  }
}

# A fresh RSA key. The private half is written to Terraform state and printed
# by `terraform output -raw ssh_private_key_pem`. State already holds the
# developers' passwords, so this does not change how sensitive it is.
resource "tls_private_key" "isaac_sim" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "isaac_sim" {
  key_name   = var.key_pair_name
  public_key = tls_private_key.isaac_sim.public_key_openssh
}
