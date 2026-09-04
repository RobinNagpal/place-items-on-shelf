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
