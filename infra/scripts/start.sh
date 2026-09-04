#!/usr/bin/env bash
# Power on the Isaac Sim instance you already have. This is the one you run at
# the start of every working day.
#
# Usage:
#   ./start.sh
#
# This does NOT create a machine. It powers on the existing one, with all your
# files, installed packages and settings exactly as you left them.
#
#   ./launch.sh   create a brand new machine (once, or after terminating)
#   ./start.sh    power on the machine you already have   <-- daily
#   ./stop.sh     power it off, keep the disk             <-- daily
#
# The public IP changes every time an instance starts, so this script prints
# the new one and reminds you if the security group needs updating.

cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

require_aws

instance_id="$(require_single_instance)"

state="$(aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$instance_id" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text)"

case "$state" in
running)
  echo "${instance_id} is already running."
  ;;
stopping)
  # You cannot start an instance that is still shutting down. Wait it out.
  echo "${instance_id} is still stopping. Waiting for that to finish first..."
  aws ec2 wait instance-stopped --region "$REGION" --instance-ids "$instance_id"
  echo "Starting ${instance_id}..."
  aws ec2 start-instances --region "$REGION" --instance-ids "$instance_id" --output text >/dev/null
  aws ec2 wait instance-running --region "$REGION" --instance-ids "$instance_id"
  ;;
*)
  echo "Starting ${instance_id} (currently ${state})..."
  aws ec2 start-instances --region "$REGION" --instance-ids "$instance_id" --output text >/dev/null
  aws ec2 wait instance-running --region "$REGION" --instance-ids "$instance_id"
  ;;
esac

public_ip="$(aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$instance_id" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)"

echo
echo "Running: ${instance_id}   public IP: ${public_ip}"
echo
echo "  Shell:  ./connect.sh"
echo "  DCV:    ${public_ip}:${DCV_PORT}   (log in as 'ubuntu')"
echo

# The instance gets a new public IP on every start, and your own home IP can
# change too. Either one breaks the security group rule, so check both.
#
# Only DCV is affected. ./connect.sh goes through Session Manager and does not
# care about the security group at all, which is why it is worth saying so
# here - otherwise a stale rule looks like the whole machine is unreachable.
my_ip="$(curl -s --max-time 5 https://checkip.amazonaws.com || true)"
if [ -n "$my_ip" ]; then
  if ! aws ec2 describe-security-groups \
    --region "$REGION" \
    --filters "Name=group-name,Values=${PROJECT}-sg" \
    --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp' \
    --output text | grep -q "${my_ip}/32"; then

    echo "WARNING: your current IP (${my_ip}) is not allowed in ${PROJECT}-sg,"
    echo "so the DCV desktop will time out. Add it with:"
    echo
    echo "  ./allow-my-ip.sh"
    echo
    echo "(./connect.sh still works - it does not use the security group.)"
    echo
  fi
fi

echo "The auto-shutdown Lambda stops this instance after 2 hours of uptime, or"
echo "once it is past 3 PM US Eastern. Run ./stop.sh when you finish."
