#!/usr/bin/env bash
# Helpers shared by launch.sh, stop.sh and terminate.sh.
#
# This file is sourced, not run. It never touches AWS by itself.
#
# There is no fixed instance ID anywhere. Operators terminate the instance and
# launch a new one, so the ID changes. What stays the same is the tag the
# launch template stamps on every instance: Purpose = isaac-sim. Every script
# here finds the instance by that tag, exactly like the two Lambdas do.

# -e  stop on the first failing command
# -u  treat an unset variable as an error
# -o pipefail  a failure anywhere in a pipe fails the whole pipe
set -euo pipefail

# All three can be overridden from the environment, e.g. AWS_REGION=us-west-2.
REGION="${AWS_REGION:-us-east-1}"
PROJECT="${ISAAC_SIM_PROJECT:-isaac-sim}"

TAG_KEY="Purpose"
TAG_VALUE="$PROJECT"
LAUNCH_TEMPLATE_NAME="${PROJECT}-workstation"

# Every state except shutting-down and terminated. An instance in one of these
# still exists and still costs something (at minimum, its disk).
LIVE_STATES="pending,running,stopping,stopped"

# Print an error and exit. "$*" is every argument joined with spaces.
die() {
  echo "ERROR: $*" >&2
  exit 1
}

# Fail early with a clear message instead of a confusing one later.
require_aws() {
  command -v aws >/dev/null 2>&1 || die "The AWS CLI is not installed. See https://aws.amazon.com/cli/"

  aws sts get-caller-identity >/dev/null 2>&1 ||
    die "AWS CLI is not logged in, or the credentials are wrong. Try: aws sts get-caller-identity"
}

# Print the ID of every live Isaac Sim instance, one per line.
# Prints nothing (and still exits 0) when there are none.
find_instances() {
  aws ec2 describe-instances \
    --region "$REGION" \
    --filters "Name=tag:${TAG_KEY},Values=${TAG_VALUE}" \
    "Name=instance-state-name,Values=${LIVE_STATES}" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text | tr '\t' '\n' | sed '/^$/d'
}

# Print "<id> <state> <type> <public-ip>" for one instance.
describe_instance() {
  aws ec2 describe-instances \
    --region "$REGION" \
    --instance-ids "$1" \
    --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,PublicIpAddress]' \
    --output text
}

# Exactly one instance must exist for stop / terminate to make sense.
# Prints the single ID, or exits with a message explaining what it found.
require_single_instance() {
  local ids
  ids="$(find_instances)"

  [ -n "$ids" ] || die "No Isaac Sim instance found in ${REGION}. Nothing to do."

  if [ "$(echo "$ids" | wc -l | tr -d ' ')" -gt 1 ]; then
    echo "Found more than one Isaac Sim instance:" >&2
    echo "$ids" >&2
    die "The single-instance guard Lambda should have cleaned this up. Check its CloudWatch logs before acting by hand."
  fi

  echo "$ids"
}

# --- Session Manager helpers ----------------------------------------------
#
# Connecting no longer needs the SSH private key or an open port. The instance
# runs an SSM Agent that dials out to AWS; `aws ssm start-session` dials out
# too, and AWS joins the two. The agent only registers once the instance has
# booted, so a freshly launched machine takes a minute or two to become
# reachable even after EC2 reports it as "running".

# How long to keep waiting for the agent to check in, in seconds.
SSM_WAIT_SECONDS="${ISAAC_SIM_SSM_WAIT:-180}"

# The port NICE DCV listens on, on the instance.
DCV_PORT=8443

# Fail early if the Session Manager plugin is missing. The AWS CLI can make the
# StartSession API call without it, but cannot then run the session, and the
# error it prints is not obvious.
require_session_manager_plugin() {
  command -v session-manager-plugin >/dev/null 2>&1 && return 0

  echo "ERROR: the Session Manager plugin is not installed." >&2
  echo >&2
  echo "On macOS:" >&2
  echo "  brew install --cask session-manager-plugin" >&2
  echo >&2
  echo "Or follow the official installer for your OS:" >&2
  echo "  https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html" >&2
  exit 1
}

# True when SSM can currently reach the instance. Returns non-zero rather than
# printing, so it reads well inside an `if`.
ssm_is_online() {
  [ "$(aws ssm describe-instance-information \
    --region "$REGION" \
    --filters "Key=InstanceIds,Values=$1" \
    --query 'InstanceInformationList[0].PingStatus' \
    --output text 2>/dev/null)" = "Online" ]
}

# Block until the agent checks in. Returns non-zero on timeout so the caller can
# print advice that fits whatever it was doing.
wait_for_ssm() {
  local id="$1" waited=0

  # Written as a full `if` rather than `ssm_is_online "$id" && return 0`. With
  # `set -e` that shorter form aborts the whole script the first time the probe
  # says "not yet", which is the normal case on a machine that is still booting.
  while [ "$waited" -lt "$SSM_WAIT_SECONDS" ]; do
    if ssm_is_online "$id"; then
      return 0
    fi
    sleep 10
    waited=$((waited + 10))
  done

  return 1
}

# The advice to print when the agent never checked in. Almost always one of
# these three, in this order of likelihood.
explain_ssm_timeout() {
  echo "The SSM Agent has not checked in after ${SSM_WAIT_SECONDS}s. Usually one of:" >&2
  echo "  1. The instance is still booting. Wait a minute and run ./connect.sh again." >&2
  echo "  2. The instance profile is missing. Check with:" >&2
  echo "       aws ec2 describe-instances --region ${REGION} --instance-ids $1 \\" >&2
  echo "         --query 'Reservations[].Instances[].IamInstanceProfile'" >&2
  echo "     Empty means it was launched before the SSM change was applied." >&2
  echo "     Terminate it and run ./launch.sh again." >&2
  echo "  3. The AMI has no SSM Agent installed. Then SSH is the only way in." >&2
}
