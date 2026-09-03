"""
Auto-shutdown checker for the Isaac Sim EC2 instance.

EventBridge calls this function on a fixed schedule (hourly by default).
On every run it asks two questions about the instance:

  1. Has it been running longer than MAX_RUNTIME_HOURS?
  2. Is the local wall-clock time at or past CURFEW_HOUR?

If the answer to either one is yes, the instance is stopped. Otherwise the
function does nothing and exits. Stopping an EC2 instance ends GPU billing
immediately; only the EBS disk keeps costing money.

All settings arrive as environment variables, which Terraform fills in.
"""

import datetime
import logging
import os

import boto3

# Lambda already configures a root logger, so we just grab it and set a level.
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client("ec2")


def _local_now(timezone_name):
    """Return the current time in the given IANA timezone (e.g. America/New_York).

    Lambda's Python runtime ships the system timezone database, so zoneinfo
    normally works. If it ever doesn't, we fall back to a fixed UTC-5 offset
    (plain EST, no daylight saving) so the curfew still runs instead of the
    whole function crashing.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    try:
        from zoneinfo import ZoneInfo

        return now_utc.astimezone(ZoneInfo(timezone_name))
    except Exception:  # noqa: BLE001 - any tz lookup failure should degrade, not fail
        logger.warning("Timezone %s unavailable, falling back to fixed UTC-5", timezone_name)
        return now_utc.astimezone(datetime.timezone(datetime.timedelta(hours=-5)))


def _describe(instance_id):
    """Fetch the one instance we care about. Returns None if it no longer exists."""
    response = ec2.describe_instances(InstanceIds=[instance_id])
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            return instance
    return None


def handler(event, context):  # noqa: ARG001 - Lambda passes both, we need neither
    instance_id = os.environ["INSTANCE_ID"]
    max_runtime_hours = float(os.environ["MAX_RUNTIME_HOURS"])
    curfew_hour = int(os.environ["CURFEW_HOUR"])
    timezone_name = os.environ["TIMEZONE"]
    # Dry run lets you watch the logs and confirm the logic before it can
    # actually stop anything.
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    instance = _describe(instance_id)
    if instance is None:
        logger.warning("Instance %s not found - nothing to do", instance_id)
        return {"action": "none", "reason": "instance-not-found"}

    state = instance["State"]["Name"]
    if state != "running":
        logger.info("Instance %s is %s - nothing to do", instance_id, state)
        return {"action": "none", "reason": f"state-{state}"}

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    local_now = _local_now(timezone_name)

    # EC2 updates LaunchTime every time an instance is started, so for a
    # stop/start machine like this one it is the current uptime clock.
    launch_time = instance["LaunchTime"]
    uptime_hours = (now_utc - launch_time).total_seconds() / 3600.0

    # Collect every rule that wants the instance off. One is enough to stop it,
    # but logging all of them makes the CloudWatch logs easier to read.
    reasons = []
    if uptime_hours >= max_runtime_hours:
        reasons.append(f"uptime {uptime_hours:.2f}h >= limit {max_runtime_hours}h")
    if local_now.hour >= curfew_hour:
        reasons.append(f"local time {local_now:%H:%M} {timezone_name} is past curfew {curfew_hour}:00")

    if not reasons:
        logger.info(
            "Instance %s running %.2fh, local time %s - under both limits, leaving it up",
            instance_id,
            uptime_hours,
            local_now.strftime("%H:%M"),
        )
        return {"action": "none", "reason": "within-limits", "uptime_hours": round(uptime_hours, 2)}

    if dry_run:
        logger.info("DRY RUN - would stop %s because: %s", instance_id, "; ".join(reasons))
        return {"action": "dry-run", "reasons": reasons}

    logger.info("Stopping %s because: %s", instance_id, "; ".join(reasons))
    ec2.stop_instances(InstanceIds=[instance_id])
    return {"action": "stopped", "reasons": reasons, "uptime_hours": round(uptime_hours, 2)}
