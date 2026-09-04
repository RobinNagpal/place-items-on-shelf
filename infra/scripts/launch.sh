#!/usr/bin/env bash
# Create the Isaac Sim instance from the launch template, then wait until it is
# ready and print how to connect.
#
# Usage:
#   ./launch.sh
#
# The launch template decides everything about the machine: the AMI, the
# instance type, the disk size, the security group, the key pair and the
# Purpose tag. This script passes no overrides, because the IAM policy would
# reject most of them anyway.

# Find this script's own folder, so the script works from any directory.
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=common.sh
source ./common.sh

require_aws

# --- Refuse to launch a second instance -----------------------------------
#
# The guard Lambda terminates every extra instance, keeping only the oldest.
# So launching a second one does not give you a second machine - it gives you
# a machine that disappears a minute later. Better to stop here and explain.
existing="$(find_instances)"
if [ -n "$existing" ]; then
  echo "An Isaac Sim instance already exists:"
  while read -r id; do
    describe_instance "$id"
  done <<<"$existing"
  echo
  echo "Start it instead of launching a new one:"
  echo "  aws ec2 start-instances --region ${REGION} --instance-ids $(echo "$existing" | head -1)"
  echo
  die "Refusing to launch a second instance - the single-instance guard would terminate it."
fi

echo "Launching from launch template '${LAUNCH_TEMPLATE_NAME}' in ${REGION}..."

# Referring to the template by NAME, not ID. The name is stable; the ID changes
# if the template is ever destroyed and recreated by Terraform.
instance_id="$(aws ec2 run-instances \
  --region "$REGION" \
  --launch-template "LaunchTemplateName=${LAUNCH_TEMPLATE_NAME}" \
  --query 'Instances[0].InstanceId' \
  --output text)"

echo "Created ${instance_id}. Waiting for it to reach 'running'..."

# EC2 takes a couple of minutes. This blocks until the state changes.
aws ec2 wait instance-running --region "$REGION" --instance-ids "$instance_id"

public_ip="$(aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$instance_id" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)"

echo
echo "Running: ${instance_id}   public IP: ${public_ip}"
echo
echo "  SSH:  ssh -i ~/.ssh/${PROJECT}-key.pem ubuntu@${public_ip}"
echo "  DCV:  https://${public_ip}:8443"
echo

# --- Two things that commonly block the first connection -------------------

# The security group starts with no inbound rules at all, so nothing can reach
# the box until an operator adds their own IP.
rule_count="$(aws ec2 describe-security-groups \
  --region "$REGION" \
  --filters "Name=group-name,Values=${PROJECT}-sg" \
  --query 'length(SecurityGroups[0].IpPermissions)' \
  --output text 2>/dev/null || echo 0)"

if [ "$rule_count" = "0" ]; then
  echo "WARNING: the ${PROJECT}-sg security group has no inbound rules, so you cannot"
  echo "connect yet. Open SSH and DCV to your current IP with:"
  echo
  echo "  MYIP=\$(curl -s https://checkip.amazonaws.com)"
  echo "  aws ec2 authorize-security-group-ingress --region ${REGION} \\"
  echo "    --group-id \$(aws ec2 describe-security-groups --region ${REGION} \\"
  echo "        --filters Name=group-name,Values=${PROJECT}-sg \\"
  echo "        --query 'SecurityGroups[0].GroupId' --output text) \\"
  echo "    --ip-permissions \\"
  echo "      \"IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=\$MYIP/32,Description=SSH}]\" \\"
  echo "      \"IpProtocol=tcp,FromPort=8443,ToPort=8443,IpRanges=[{CidrIp=\$MYIP/32,Description=DCV}]\""
  echo
fi

echo "Remember: the auto-shutdown Lambda stops this instance after 2 hours of"
echo "uptime, or once it is past 3 PM US Eastern. Run ./stop.sh when you finish"
echo "so you are not relying on the guard rail."
