#!/usr/bin/env bash
# Stop the Isaac Sim instance. This is the one you run at the end of every
# working session.
#
# Usage:
#   ./stop.sh
#
# Stopping ends the GPU billing straight away. The disk stays, so everything
# you installed and every file you saved is still there next time. Only the
# 512 GiB disk keeps costing money (about $40 a month).
#
# The public IP is released on stop and a new one is assigned on the next
# start, so re-check it after starting.

cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

require_aws

instance_id="$(require_single_instance)"

# What state is it in right now? Stopping an already-stopped instance is
# harmless, but saying so is clearer than printing a confusing AWS response.
state="$(aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$instance_id" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text)"

if [ "$state" = "stopped" ]; then
  echo "${instance_id} is already stopped. Nothing to do."
  exit 0
fi

if [ "$state" = "stopping" ]; then
  echo "${instance_id} is already stopping. Waiting for it to finish..."
else
  echo "Stopping ${instance_id} (currently ${state})..."
  aws ec2 stop-instances \
    --region "$REGION" \
    --instance-ids "$instance_id" \
    --output text >/dev/null
fi

# Block until it is fully stopped, so the script only returns when the GPU
# billing has actually ended.
aws ec2 wait instance-stopped --region "$REGION" --instance-ids "$instance_id"

echo "${instance_id} is stopped. GPU billing has ended; the disk is kept."
echo "Start it again with:"
echo "  ./start.sh"
