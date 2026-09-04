#!/usr/bin/env bash
# Open the NICE DCV port to the IP you are connecting from right now.
#
# Usage:
#   ./allow-my-ip.sh              # allow DCV from my current IP
#   ./allow-my-ip.sh --replace    # remove every old rule first, then allow it
#   ./allow-my-ip.sh --with-ssh   # also open port 22
#
# Why this exists: the security group starts with NO inbound rules, so nothing
# can reach the instance. Home IPs also change whenever your ISP feels like it,
# or when you move to a cafe. Operators are allowed to edit this one security
# group themselves so they are not blocked waiting on an admin.
#
# Two ports, not one:
#
#   TCP 8443   The DCV connection itself. Always needed.
#   UDP 8443   DCV's QUIC transport. Optional, but it is the single biggest
#              improvement on a long-distance link - it is what keeps the 3D
#              viewport responsive when the round trip is 200ms+. The server
#              side also has to be switched on; see the note at the bottom.
#
# Port 22 is NOT opened by default any more. ./connect.sh gets you a shell
# through Session Manager without it. Pass --with-ssh if you specifically need
# SSH, for example to use scp or an editor's remote mode.
#
# --replace keeps the rule list from filling up with dead IPs over time. Use it
# on your own machine; skip it if a teammate's IP is also in the list.

cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

require_aws

replace="no"
with_ssh="no"

for arg in "$@"; do
  case "$arg" in
  --replace) replace="yes" ;;
  --with-ssh) with_ssh="yes" ;;
  *) die "Unknown option '$arg'. Usage: ./allow-my-ip.sh [--replace] [--with-ssh]" ;;
  esac
done

# checkip.amazonaws.com just echoes back the IP it sees you from.
my_ip="$(curl -s --max-time 10 https://checkip.amazonaws.com | tr -d '[:space:]')"
[ -n "$my_ip" ] || die "Could not detect your public IP. Are you online?"

group_id="$(aws ec2 describe-security-groups \
  --region "$REGION" \
  --filters "Name=group-name,Values=${PROJECT}-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)"

[ "$group_id" != "None" ] && [ -n "$group_id" ] ||
  die "No security group named ${PROJECT}-sg in ${REGION}."

echo "Your IP: ${my_ip}"
echo "Security group: ${group_id}"

if [ "$replace" = "yes" ]; then
  echo "Removing existing inbound rules..."
  # Pull the whole permission set and hand it straight back to revoke. Prints
  # nothing and succeeds harmlessly when there are no rules yet.
  existing="$(aws ec2 describe-security-groups \
    --region "$REGION" \
    --group-ids "$group_id" \
    --query 'SecurityGroups[0].IpPermissions' \
    --output json)"

  if [ "$existing" != "[]" ] && [ -n "$existing" ]; then
    aws ec2 revoke-security-group-ingress \
      --region "$REGION" \
      --group-id "$group_id" \
      --ip-permissions "$existing" \
      --output text >/dev/null
  fi
fi

# Add one rule, and treat "it is already there" as success rather than an
# error. That makes the whole script safe to re-run any number of times.
allow_rule() {
  local proto="$1" port="$2" desc="$3" out

  if out="$(aws ec2 authorize-security-group-ingress \
    --region "$REGION" \
    --group-id "$group_id" \
    --ip-permissions "IpProtocol=${proto},FromPort=${port},ToPort=${port},IpRanges=[{CidrIp=${my_ip}/32,Description=${desc}}]" \
    --output text 2>&1)"; then
    echo "  added    ${proto}/${port}"
  elif echo "$out" | grep -q "InvalidPermission.Duplicate"; then
    echo "  already  ${proto}/${port}"
  else
    die "Could not add ${proto}/${port}: ${out}"
  fi
}

echo "Allowing DCV from ${my_ip}/32..."
allow_rule tcp "$DCV_PORT" DCV
allow_rule udp "$DCV_PORT" DCV-QUIC

if [ "$with_ssh" = "yes" ]; then
  allow_rule tcp 22 SSH
fi

echo "Done. Current inbound rules:"
aws ec2 describe-security-groups \
  --region "$REGION" \
  --group-ids "$group_id" \
  --query 'SecurityGroups[0].IpPermissions[].[IpProtocol,FromPort,IpRanges[0].CidrIp,IpRanges[0].Description]' \
  --output table

# The UDP rule alone does nothing until DCV is told to offer QUIC. This is a
# one-time change on the instance, and it survives stop/start.
echo
echo "The UDP rule only helps once DCV offers QUIC. To switch it on, open a"
echo "shell with ./connect.sh and run:"
echo
echo "  sudo sed -i 's/^#\\?enable-quic-frontend=.*/enable-quic-frontend=true/' /etc/dcv/dcv.conf"
echo "  grep enable-quic-frontend /etc/dcv/dcv.conf   # confirm it says true"
echo "  sudo systemctl restart dcvserver"
echo
echo "Then reconnect and check the DCV client shows a QUIC/UDP connection."
