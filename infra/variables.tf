# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "Region the Isaac Sim instance lives in. Keep this the same as the security group and key pair."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used as a prefix for every resource this project creates. Also the value of the Purpose tag that marks the Isaac Sim instance."
  type        = string
  default     = "isaac-sim"
}

# ---------------------------------------------------------------------------
# The AMI, network and key pair
#
# The Isaac Sim AMI comes from the AWS Marketplace and needs a manual
# "Subscribe / Accept Terms" click that Terraform cannot perform. Everything
# else (security group, key pair) is created here.
# ---------------------------------------------------------------------------

variable "ami_id" {
  description = "AMI ID of the NVIDIA Isaac Sim Marketplace image, e.g. ami-0abc123def4567890. Subscribe to it in the Marketplace first, then copy the ID from the AMI Catalog."
  type        = string

  validation {
    condition     = can(regex("^ami-[0-9a-f]{8,17}$", var.ami_id))
    error_message = "ami_id must look like ami-0abc123def4567890."
  }
}

variable "ssh_dcv_allowed_cidrs" {
  description = "CIDRs allowed to reach SSH (22) and NICE DCV (8443) when the security group is first created, e.g. [\"203.0.113.7/32\"]. Operators edit the rules by hand afterwards, so this only seeds the first rule set."
  type        = list(string)
  default     = []
}

variable "key_pair_name" {
  description = "Name of the EC2 key pair Terraform creates and bakes into the launch template. Operators SSH in with the private key from `terraform output -raw ssh_private_key_pem`."
  type        = string
  default     = "isaac-sim-key"
}

variable "subnet_id" {
  description = "Subnet to launch into. Leave null to use the default VPC's default subnet, which is where the hand-made security group normally lives."
  type        = string
  default     = null
}

# ---------------------------------------------------------------------------
# The launch template - the only way operators can create the instance
# ---------------------------------------------------------------------------

variable "instance_type" {
  description = "Instance type the launch template uses. It is also the only type the IAM policy allows, so a bigger box means changing this and re-applying. Must be on the Marketplace product's supported list - g6e.xlarge is the smallest one it allows."
  type        = string
  default     = "g6e.xlarge"
}

variable "root_volume_size_gb" {
  description = "Root disk size in GiB. The Isaac Sim AMI refuses anything under 512."
  type        = number
  default     = 512
}

variable "instance_name" {
  description = "Value of the Name tag on the instance, so it is easy to spot in the console."
  type        = string
  default     = "isaac-sim-dev"
}

# ---------------------------------------------------------------------------
# Who can operate the instance
# ---------------------------------------------------------------------------

variable "developer_user_names" {
  description = "IAM user names to create for the developers who use Isaac Sim. One user per name, up to four. Leave empty to create none."
  type        = list(string)
  default     = ["robin-robotics", "hassaan-robotics"]

  validation {
    condition     = length(var.developer_user_names) <= 4
    error_message = "developer_user_names holds at most four names."
  }

  validation {
    condition     = length(var.developer_user_names) == length(distinct(var.developer_user_names))
    error_message = "developer_user_names must not contain duplicates."
  }
}

variable "admin_user_names" {
  description = "Names of EXISTING IAM users (for example your own admin user) that should get the same launch / start / stop rights as the developer. They are added to the operators group; nothing else about them is touched."
  type        = list(string)
  default     = []
}

variable "create_console_access" {
  description = "Create a console password for every developer user. They are forced to change it on first sign-in."
  type        = bool
  default     = true
}

variable "create_access_key" {
  description = "Create an access key ID + secret for the AWS CLI. Turn off if the developers only need the console."
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------
# Single-instance guard
# ---------------------------------------------------------------------------

variable "single_instance_guard_dry_run" {
  description = "When true the guard only logs which extra instance it would terminate. Use this for the first day, then flip it off."
  type        = bool
  default     = false
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
  description = "How long to keep the Lambdas' CloudWatch logs. Short is fine and cheap."
  type        = number
  default     = 14
}
