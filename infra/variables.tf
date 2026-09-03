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
# Existing resources this project points at
#
# The instance and the security group are NOT created here. The Isaac Sim AMI
# comes from the AWS Marketplace and needs a manual subscription click, so the
# manager launches the instance by hand (see ../isaac-sim-aws-setup.md) and then
# pastes the two IDs below.
# ---------------------------------------------------------------------------

variable "instance_id" {
  description = "EC2 instance ID of the Isaac Sim workstation, e.g. i-0abc123def4567890."
  type        = string

  validation {
    condition     = can(regex("^i-[0-9a-f]{8,17}$", var.instance_id))
    error_message = "instance_id must look like i-0abc123def4567890."
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
