#!/usr/bin/env bash
# Open SSH (22) and NICE DCV (8443) to the IP you are connecting from right now.
#
# Usage:
#   ./allow-my-ip.sh            # detect my IP and allow it
#   ./allow-my-ip.sh --replace  # remove every old rule first, then allow it
#
# Why this exists: the security group starts with NO inbound rules, so nothing
# can reach the instance. Home IPs also change whenever your ISP feels like it,
# or when you move to a cafe. Operators are allowed to edit this one security
# group themselves so they are not blocked waiting on an admin.
#
# --replace keeps the rule list from filling up with dead IPs over time. Use it
# on your own machine; skip it if a teammate's IP is also in the list.

cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

require_aws

replace="no"
if [ "${1:-}" = "--replace" ]; then
  replace="yes"
fi

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

# Already allowed? Then there is nothing to do, and re-adding would just error.
if aws ec2 describe-security-groups \
  --region "$REGION" \
  --group-ids "$group_id" \
  --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp' \
  --output text | grep -q "${my_ip}/32"; then

  echo "${my_ip}/32 is already allowed. Nothing to do."
  exit 0
fi

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

echo "Allowing SSH (22) and DCV (8443) from ${my_ip}/32..."
aws ec2 authorize-security-group-ingress \
  --region "$REGION" \
  --group-id "$group_id" \
  --ip-permissions \
  "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=${my_ip}/32,Description=SSH}]" \
  "IpProtocol=tcp,FromPort=8443,ToPort=8443,IpRanges=[{CidrIp=${my_ip}/32,Description=NICE DCV}]" \
  --output text >/dev/null

echo "Done. Current inbound rules:"
aws ec2 describe-security-groups \
  --region "$REGION" \
  --group-ids "$group_id" \
  --query 'SecurityGroups[0].IpPermissions[].[FromPort,IpRanges[0].CidrIp,IpRanges[0].Description]' \
  --output table
