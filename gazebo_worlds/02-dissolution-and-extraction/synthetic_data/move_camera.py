#!/usr/bin/env python3
"""Teleport the overhead camera through a list of preset poses.

What this does, in plain English:

  1. The camera in `ketchup_extraction.sdf` is set to AUTO-SAVE every
     rendered frame to `./captured_frames/` (see the <save> element on
     the overhead_cam sensor). So just running gz sim already produces
     a dataset of identical top-down frames.
  2. This script adds variety by moving the camera between captures.
     It calls `gz service /world/.../set_pose` to teleport the
     `overhead_camera` model to each pose in VIEWS, sleeping at each
     pose so Gazebo writes several PNGs at that angle before we move on.

No ROS. No bridge. No Python image library. Only `gz service`.

Run it AFTER starting Gazebo with:

    gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf

Usage:

    python3 move_camera.py            # cycle through views once, then exit
    python3 move_camera.py --loop     # cycle forever until Ctrl+C
    python3 move_camera.py --dwell 4  # spend 4 s at each view (default 2)
"""

from __future__ import annotations

import argparse
import math
import subprocess
import time
from typing import List, Tuple

WORLD = "ketchup_extraction_cell"
CAMERA_MODEL = "overhead_camera"

# Each view is (label, x, y, z, roll, pitch, yaw) in world coords.
# Camera optical axis is +X of its own frame. pitch = +pi/2 means the
# axis points down (toward -Z in world). For oblique side shots we
# reduce pitch toward ~pi/3 and add a yaw so the camera faces the
# bench centre.
View = Tuple[str, float, float, float, float, float, float]
VIEWS: List[View] = [
    # Straight down — same as the SDF default pose.
    ("top",          0.00,  0.00, 1.50, 0.0, math.pi / 2,         0.0),
    # Oblique from in front of the bench (+X), tilted to look at the centre.
    ("oblique_+x",   0.45,  0.00, 1.25, 0.0, math.pi / 3,         0.0),
    # Oblique from behind the bench (-X). Yaw 180 deg to still face centre.
    ("oblique_-x",  -0.45,  0.00, 1.25, 0.0, math.pi / 3,    math.pi),
    # Oblique from the left side (+Y).
    ("oblique_+y",   0.00,  0.45, 1.25, 0.0, math.pi / 3,    math.pi / 2),
    # Oblique from the right side (-Y).
    ("oblique_-y",   0.00, -0.45, 1.25, 0.0, math.pi / 3,   -math.pi / 2),
]


def rpy_to_quat(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    """Roll-pitch-yaw (ZYX intrinsic) -> (qx, qy, qz, qw)."""
    cr, cp, cy = math.cos(roll / 2.0), math.cos(pitch / 2.0), math.cos(yaw / 2.0)
    sr, sp, sy = math.sin(roll / 2.0), math.sin(pitch / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,  # qx
        cr * sp * cy + sr * cp * sy,  # qy
        cr * cp * sy - sr * sp * cy,  # qz
        cr * cp * cy + sr * sp * sy,  # qw
    )


def set_pose(name: str, x: float, y: float, z: float,
             qx: float, qy: float, qz: float, qw: float) -> bool:
    """Teleport ``name`` via `gz service /world/<WORLD>/set_pose`."""
    req = (
        f'name: "{name}" '
        f'position {{ x: {x} y: {y} z: {z} }} '
        f'orientation {{ x: {qx} y: {qy} z: {qz} w: {qw} }}'
    )
    result = subprocess.run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD}/set_pose",
            "--reqtype", "gz.msgs.Pose",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "1000",
            "--req", req,
        ],
        capture_output=True, text=True,
    )
    return "data: true" in (result.stdout or "")


def cycle_once(dwell_s: float) -> None:
    for label, x, y, z, r, p, yw in VIEWS:
        qx, qy, qz, qw = rpy_to_quat(r, p, yw)
        ok = set_pose(CAMERA_MODEL, x, y, z, qx, qy, qz, qw)
        status = "OK" if ok else "FAIL (is gz sim running?)"
        print(
            f"[{label}]  pos=({x:+.2f}, {y:+.2f}, {z:+.2f})  "
            f"rpy=({r:+.2f}, {p:+.2f}, {yw:+.2f})  set_pose={status}"
        )
        if ok:
            time.sleep(dwell_s)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dwell", type=float, default=2.0,
                        help="seconds to wait at each pose (default: 2)")
    parser.add_argument("--loop", action="store_true",
                        help="cycle through views forever (Ctrl+C to stop)")
    args = parser.parse_args()

    if args.loop:
        try:
            while True:
                cycle_once(args.dwell)
        except KeyboardInterrupt:
            print("\nstopped by user.")
    else:
        cycle_once(args.dwell)


if __name__ == "__main__":
    main()
