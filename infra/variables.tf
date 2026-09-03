# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "Region the Isaac Sim instance lives in. Keep this the same as the instance."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used as a prefix for every resource this project creates."
  type        = string
  default     = "isaac-sim"
}

# ---------------------------------------------------------------------------
# The Isaac Sim instance
#
# Terraform can create the instance for you (create_instance = true, the
# default), or point at one you launched by hand (create_instance = false plus
# an instance_id). Either way the security group is NOT created here - make
# isaac-sim-sg in the console first and paste its ID below.
#
# Creating the instance still needs ONE manual step beforehand: accepting the
# Marketplace subscription for the Isaac Sim AMI. See instance.tf.
# ---------------------------------------------------------------------------

variable "create_instance" {
  description = <<-EOT
    Let Terraform create the Isaac Sim EC2 instance (recommended).

    true  - Terraform launches the instance from the Marketplace AMI and wires
            its real ID into the IAM policy and the auto-shutdown Lambda by
            itself. You must accept the Marketplace subscription first (one
            click, once per account) or the launch fails with OptInRequired.
    false - You launched the instance by hand; paste its ID into instance_id
            below.
  EOT
  type        = bool
  default     = true
}

variable "instance_id" {
  description = "Only used when create_instance = false. EC2 instance ID of the hand-launched Isaac Sim workstation, e.g. i-0abc123def4567890."
  type        = string
  default     = ""

  validation {
    # Empty is allowed because create_instance = true supplies the ID instead.
    condition     = var.instance_id == "" || can(regex("^i-[0-9a-f]{8,17}$", var.instance_id))
    error_message = "instance_id must be empty (when create_instance = true) or look like i-0abc123def4567890."
  }
}

variable "security_group_id" {
  description = "Security group ID of isaac-sim-sg. The developer is allowed to edit its inbound rules so they can refresh their home IP."
  type        = string

  validation {
    condition     = can(regex("^sg-[0-9a-f]{8,17}$", var.security_group_id))
    error_message = "security_group_id must look like sg-0abc123def4567890."
  }
}

# ---------------------------------------------------------------------------
# The developer IAM user
# ---------------------------------------------------------------------------

variable "developer_user_name" {
  description = "Name of the IAM user created for the developer who uses Isaac Sim."
  type        = string
  default     = "isaac-sim-dev"
}

variable "create_console_access" {
  description = "Create a console password for the user. They are forced to change it on first sign-in."
  type        = bool
  default     = true
}

variable "create_access_key" {
  description = "Create an access key ID + secret for the AWS CLI. Turn off if the user only needs the console."
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------
# Auto-shutdown rules
# ---------------------------------------------------------------------------

variable "auto_shutdown_enabled" {
  description = "Master switch. Set to false to pause the scheduled check without destroying anything."
  type        = bool
  default     = true
}

variable "auto_shutdown_dry_run" {
  description = "When true the checker only logs what it would stop. Use this for the first day, then flip it off."
  type        = bool
  default     = false
}

variable "max_runtime_hours" {
  description = "Stop the instance once it has been running this many hours."
  type        = number
  default     = 2
}

variable "curfew_hour" {
  description = "Local hour (24h clock) at or after which the instance must not be running. 15 means 3 PM."
  type        = number
  default     = 15

  validation {
    condition     = var.curfew_hour >= 0 && var.curfew_hour <= 23
    error_message = "curfew_hour must be between 0 and 23."
  }
}

variable "curfew_timezone" {
  description = "IANA timezone the curfew is measured in. America/New_York is US Eastern and handles daylight saving on its own."
  type        = string
  default     = "America/New_York"
}

variable "check_schedule_expression" {
  description = "How often the checker runs. Hourly (aligned to the top of the hour) by default, so a shutdown lands within one hour of a limit being crossed. Use cron(*/15 * * * ? *) if you want it tighter. Note: cron() is UTC and is wall-clock aligned; rate() is NOT wall-clock aligned - it fires every N minutes from whenever the rule was created."
  type        = string
  default     = "cron(0 * * * ? *)"
}

variable "log_retention_days" {
  description = "How long to keep the checker's CloudWatch logs. Short is fine and cheap."
  type        = number
  default     = 14
}

# ---------------------------------------------------------------------------
# The instance Terraform creates (only when create_instance = true)
# ---------------------------------------------------------------------------

variable "ami_id" {
  description = "Pin an exact AMI ID. Leave empty to auto-find the newest Marketplace AMI matching ami_name_filter."
  type        = string
  default     = ""
}

variable "ami_name_filter" {
  description = <<-EOT
    Name pattern used to find the Isaac Sim Marketplace AMI when ami_id is empty.

    NVIDIA publishes these as "OV-Template" (OV = Omniverse) images, e.g.
      OV-Template-aws-ubuntu-isaac_sim-20260624T103823-...-prod-l4r5drddssotm

    The "ubuntu" in the pattern matters: there is a matching windows- image and
    we do not want it. Re-check the current name with:
      aws ec2 describe-images --owners aws-marketplace \
        --filters "Name=name,Values=*isaac_sim*" \
        --query 'reverse(sort_by(Images,&CreationDate))[:5].[ImageId,Name]' \
        --output table
  EOT
  type        = string
  default     = "OV-Template-aws-ubuntu-isaac_sim-*"
}

variable "instance_type" {
  description = "GPU instance type. g6e.xlarge is the cheapest the Isaac Sim AMI accepts (L40S 48 GB, ~$1.86/hour)."
  type        = string
  default     = "g6e.xlarge"
}

variable "root_volume_size" {
  description = "Root disk in GiB. 512 is the Isaac Sim AMI minimum."
  type        = number
  default     = 512
}

variable "root_volume_encrypted" {
  description = "Encrypt the root disk. Set false only if the Marketplace AMI refuses to launch encrypted."
  type        = bool
  default     = true
}

variable "subnet_id" {
  description = "Subnet to launch into. Leave empty to auto-pick a public subnet in whatever VPC the security group belongs to. Set it explicitly if that VPC has several public subnets and you care which one."
  type        = string
  default     = ""
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH. Create it in the console first (EC2 -> Key Pairs)."
  type        = string
  default     = "isaac-sim-key"
}
