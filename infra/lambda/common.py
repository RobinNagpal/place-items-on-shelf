"""
Helpers shared by both Lambdas: find the Isaac Sim instance(s) by tag.

There is no fixed instance ID any more. Operators can terminate the instance
and launch a new one from the launch template, so the ID changes. What stays
the same is the tag the template stamps on every instance (Purpose = isaac-sim
by default). Both Lambdas ask EC2 for "every instance with that tag".
"""

import os

import boto3

ec2 = boto3.client("ec2")

# Every state except "shutting-down" and "terminated". An instance in one of
# these still exists and still counts as "an Isaac Sim instance".
LIVE_STATES = ["pending", "running", "stopping", "stopped"]


def find_tagged_instances():
    """Return every live instance that carries the Isaac Sim tag."""
    tag_key = os.environ["TAG_KEY"]
    tag_value = os.environ["TAG_VALUE"]

    paginator = ec2.get_paginator("describe_instances")
    pages = paginator.paginate(
        Filters=[
            {"Name": f"tag:{tag_key}", "Values": [tag_value]},
            {"Name": "instance-state-name", "Values": LIVE_STATES},
        ]
    )

    instances = []
    for page in pages:
        for reservation in page.get("Reservations", []):
            instances.extend(reservation.get("Instances", []))
    return instances


def is_dry_run():
    """Dry run lets you watch the logs before the function can touch anything."""
    return os.environ.get("DRY_RUN", "false").lower() == "true"
