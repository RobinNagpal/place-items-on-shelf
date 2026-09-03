#!/usr/bin/env bash
# Delete the Isaac Sim instance for good.
#
# Usage:
#   ./terminate.sh            # asks you to type the instance ID to confirm
#   ./terminate.sh --force    # no question asked (for scripts, not for people)
#
# THIS IS NOT THE SAME AS ./stop.sh.
#
#   stop.sh       pauses the machine. GPU billing ends. Your disk and all your
#                 work are kept. This is what you want at the end of a day.
#
#   terminate.sh  deletes the machine AND its 512 GiB disk, because the launch
#                 template sets delete_on_termination = true. Everything you
#                 installed or saved on that disk is gone and cannot be
#                 recovered. Only do this when you are finished with Isaac Sim
#                 for a long time, or you want a clean rebuild.
#
# You can always launch a fresh instance afterwards with ./launch.sh - the
# launch template is not affected.

cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

require_aws

force="no"
if [ "${1:-}" = "--force" ]; then
  force="yes"
fi

instance_id="$(require_single_instance)"

echo "About to TERMINATE this instance and delete its disk:"
echo
describe_instance "$instance_id"
echo

# List the volumes that go with it, so the size of the loss is on screen
# before anyone confirms.
echo "Volumes that will be deleted with it:"
aws ec2 describe-volumes \
  --region "$REGION" \
  --filters "Name=attachment.instance-id,Values=${instance_id}" \
  --query 'Volumes[].[VolumeId,Size,VolumeType]' \
  --output text
echo

if [ "$force" != "yes" ]; then
  echo "This cannot be undone. Everything on the disk will be lost."
  echo "If you only want to pause the machine and keep your work, press Ctrl-C"
  echo "now and run ./stop.sh instead."
  echo
  # Asking for the full instance ID, not just "y", makes it hard to delete the
  # wrong thing on autopilot.
  printf 'Type the instance ID to confirm: '
  read -r typed

  [ "$typed" = "$instance_id" ] || die "Typed '${typed}', expected '${instance_id}'. Nothing was terminated."
fi

echo "Terminating ${instance_id}..."
aws ec2 terminate-instances \
  --region "$REGION" \
  --instance-ids "$instance_id" \
  --output text >/dev/null

# Block until it is really gone, so a follow-up ./launch.sh does not trip over
# the single-instance guard while the old one is still shutting down.
aws ec2 wait instance-terminated --region "$REGION" --instance-ids "$instance_id"

echo "${instance_id} is terminated and its disk is deleted."
echo "Launch a fresh one any time with ./launch.sh"
