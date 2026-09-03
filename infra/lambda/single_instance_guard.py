"""
Single-instance guard for Isaac Sim.

Operators are allowed to launch the Isaac Sim instance themselves. IAM can say
"only from this template" and "only this size", but it cannot say "only one".
This function does that.

EventBridge calls it whenever any instance enters the "pending" state (the
first state after launch or start), and again on the hourly schedule as a
safety net. Each run:

  1. lists every live instance that carries the Isaac Sim tag,
  2. if there is more than one, keeps the oldest and terminates the rest.

"Oldest" means "created first", not "started first". See _created_at below.
"""

import logging

from common import ec2, find_tagged_instances, is_dry_run

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _created_at(instance):
    """When was this instance created?

    LaunchTime is the wrong clock: EC2 resets it on every stop/start, so a
    fresh launch and a just-restarted old instance look the same. The primary
    network card (device index 0) is attached once, at creation, and stays
    attached across stop/start, so its AttachTime is a stable creation time.
    """
    for eni in instance.get("NetworkInterfaces", []):
        attachment = eni.get("Attachment", {})
        if attachment.get("DeviceIndex") == 0 and "AttachTime" in attachment:
            return attachment["AttachTime"]
    # Should not happen, but never crash the guard over a missing field.
    return instance["LaunchTime"]


def handler(event, context):  # noqa: ARG001 - the event only tells us "something changed"
    instances = find_tagged_instances()
    ids = [i["InstanceId"] for i in instances]

    if len(instances) <= 1:
        logger.info("%d Isaac Sim instance(s) found (%s) - within the limit", len(instances), ids)
        return {"action": "none", "instances": ids}

    # Keep the one that was created first. Everything newer is an extra.
    instances.sort(key=_created_at)
    keep = instances[0]["InstanceId"]
    extras = [i["InstanceId"] for i in instances[1:]]

    if is_dry_run():
        logger.warning("DRY RUN - %d instances found, would keep %s and terminate %s", len(instances), keep, extras)
        return {"action": "dry-run", "keep": keep, "would_terminate": extras}

    logger.warning("%d instances found, keeping %s and terminating %s", len(instances), keep, extras)
    ec2.terminate_instances(InstanceIds=extras)
    return {"action": "terminated", "keep": keep, "terminated": extras}
