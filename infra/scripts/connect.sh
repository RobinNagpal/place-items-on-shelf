#!/usr/bin/env bash
# Open a terminal on the Isaac Sim instance, or tunnel the DCV port to your own
# machine, using AWS Session Manager.
#
# Usage:
#   ./connect.sh              # a shell on the instance
#   ./connect.sh --forward    # tunnel DCV to https://localhost:8443
#
# There is no SSH key and no open port involved. The instance's SSM Agent makes
# an OUTBOUND connection to AWS, your CLI makes one too, and AWS joins them. So
# this works even when the security group has no inbound rules at all.
#
# What each mode is for:
#
#   (no flag)   A text terminal. You need it exactly once on a brand new
#               machine, to give the ubuntu user a password so you can log in
#               to the DCV desktop. After that it is just a handy shell.
#
#   --forward   Tunnels the instance's port 8443 to your laptop, so the DCV
#               client can connect to localhost and port 8443 never has to be
#               opened to the internet. Safer, but slower: the tunnel is TCP
#               only, so DCV cannot use its faster UDP transport, and the
#               traffic makes an extra hop through the SSM service. For a 3D
#               viewport that is noticeable. Prefer ./allow-my-ip.sh and a
#               direct DCV connection for day-to-day work, and keep this for
#               networks where you cannot pin a stable IP.

cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

forward="no"
if [ "${1:-}" = "--forward" ]; then
  forward="yes"
elif [ -n "${1:-}" ]; then
  die "Unknown option '$1'. Usage: ./connect.sh [--forward]"
fi

require_aws
require_session_manager_plugin

instance_id="$(require_single_instance)"

state="$(aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$instance_id" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text)"

# A stopped instance runs no agent, so there is nothing to connect to.
if [ "$state" != "running" ]; then
  echo "${instance_id} is ${state}, not running."
  die "Power it on first with ./start.sh"
fi

# Only wait and print if it is not already reachable, so the common case stays
# quiet and instant.
if ! ssm_is_online "$instance_id"; then
  echo "Waiting for the SSM Agent on ${instance_id} to check in..."
  if ! wait_for_ssm "$instance_id"; then
    explain_ssm_timeout "$instance_id"
    exit 1
  fi
fi

if [ "$forward" = "yes" ]; then
  echo "Tunnelling ${instance_id}:${DCV_PORT} to localhost:${DCV_PORT}."
  echo "Leave this running, then point the DCV client at:"
  echo
  echo "  https://localhost:${DCV_PORT}"
  echo
  echo "Press Ctrl-C here to close the tunnel."
  echo

  exec aws ssm start-session \
    --region "$REGION" \
    --target "$instance_id" \
    --document-name AWS-StartPortForwardingSession \
    --parameters "{\"portNumber\":[\"${DCV_PORT}\"],\"localPortNumber\":[\"${DCV_PORT}\"]}"
fi

echo "Opening a shell on ${instance_id}."
echo
echo "You land as the ssm-user, not ubuntu. To become ubuntu:"
echo "    sudo su - ubuntu"
echo
echo "On a BRAND NEW machine, set the DCV login password once:"
echo "    sudo passwd ubuntu"
echo "DCV authenticates against the Linux user, so without this the desktop"
echo "login is rejected no matter what the security group says."
echo
echo "Type 'exit' to leave (twice if you switched to ubuntu)."
echo

# exec replaces this script with the session, so Ctrl-C and the exit code
# behave exactly as if you had run the aws command yourself.
exec aws ssm start-session \
  --region "$REGION" \
  --target "$instance_id"
