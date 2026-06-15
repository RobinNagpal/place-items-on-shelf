#!/usr/bin/env python3
"""Teleport the overhead camera + save its frames as PNGs.

What this does, end to end:

  1. Subscribes to /overhead_camera/image_raw via the gz-transport
     Python bindings (NOT ROS, NOT ros_gz_bridge). The subscription
     also forces the sensor to actually render — some gz-sim builds
     skip rendering when no client is connected.
  2. Calls `gz service /world/.../set_pose` to teleport the
     `overhead_camera` model through a list of preset viewpoints.
  3. After waiting `--dwell` seconds at each pose, saves the latest
     received frame as captured_frames/<label>_<N>.png.
  4. Prints the absolute output path on every save so there is no
     guessing about where the PNGs landed.

NO ROS. NO ros_gz_bridge. Only gz-transport + numpy + Pillow.

Why the rewrite from the previous version:
The SDF <save> element parses cleanly but does not actually write
PNGs on the user's WSL gz-sim build (the sensor's render-on-render
loop never fires when nothing is subscribed to the topic). Doing
the subscribe ourselves in Python both fixes the capture and makes
it impossible to get zero PNGs without a clear error message.

Prerequisites (one-time install):

  Ubuntu 24.04 + Jazzy + Harmonic:
      sudo apt install python3-gz-transport13 python3-gz-msgs10 \
                       python3-numpy python3-pil

  Ubuntu 22.04 + Humble + Garden:
      sudo apt install python3-gz-transport12 python3-gz-msgs9 \
                       python3-numpy python3-pil

Run order:

  Terminal 1:  gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
  Terminal 2:  python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/move_camera.py

Common flags:

  --dwell 4     spend 4 s at each view (default 2)
  --loop        cycle forever (Ctrl+C to stop)
  --out PATH    output folder (default ./captured_frames)
  --shots N     PNGs to save per view (default 1)
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

WORLD = "ketchup_extraction_cell"
CAMERA_MODEL = "overhead_camera"
CAMERA_TOPIC = "/overhead_camera/image_raw"
DEFAULT_SAVE_DIR = Path("captured_frames")


# ---------------------------------------------------------------------------
# gz-transport / gz-msgs Python bindings.
# Harmonic ships v13/v10; Garden ships v12/v9. Try newest first.
# ---------------------------------------------------------------------------
def _import_gz_bindings():
    last_err = None
    for transport_mod, msgs_mod, label in (
        ("gz.transport13", "gz.msgs10.image_pb2", "Harmonic (transport13 + msgs10)"),
        ("gz.transport12", "gz.msgs9.image_pb2",  "Garden   (transport12 + msgs9)"),
    ):
        try:
            transport = __import__(transport_mod, fromlist=["Node"])
            msgs = __import__(msgs_mod, fromlist=["Image"])
            return transport.Node, msgs.Image, label
        except ImportError as e:
            last_err = e
    sys.exit(
        "ERROR: gz-transport Python bindings not found.\n"
        f"  last import error: {last_err}\n"
        "\n"
        "Install (Ubuntu 24.04 + Harmonic):\n"
        "    sudo apt install python3-gz-transport13 python3-gz-msgs10\n"
        "Install (Ubuntu 22.04 + Garden):\n"
        "    sudo apt install python3-gz-transport12 python3-gz-msgs9\n"
        "\n"
        "If apt cannot find the package, you are likely on the other gz\n"
        "track — `gz sim --version` tells you Garden (v7) vs Harmonic (v8).\n"
    )


def _import_image_libs():
    try:
        import numpy as np  # type: ignore
        from PIL import Image as PILImage  # type: ignore
        return np, PILImage
    except ImportError as e:
        sys.exit(
            "ERROR: numpy and Pillow are required to write PNGs.\n"
            f"  last import error: {e}\n"
            "  fix:  sudo apt install python3-numpy python3-pil\n"
        )


GzNode, GzImage, GZ_LABEL = _import_gz_bindings()
np, PILImage = _import_image_libs()


# ---------------------------------------------------------------------------
# Where the camera always points to.
#
# All bench objects are clustered around this point (solvent bottle near
# (0.10, 0.25, 0.97), three beakers along x ~ 0.05, y in [-0.30, -0.06],
# bench top at z = 0.90). Aiming every view at this single point keeps
# the scene centred no matter where the camera sits.
#
# If you add new objects somewhere else in the world, either move this
# target or add per-view targets.
# ---------------------------------------------------------------------------
LOOK_AT_TARGET: Tuple[float, float, float] = (0.05, 0.0, 0.94)


# ---------------------------------------------------------------------------
# Camera positions only. Orientation (pitch + yaw) is computed at runtime
# by look_at(), so we never hand-write rotations and never face the wrong
# way again.
#
# Each entry is (label, x, y, z) in world frame, with units in metres.
# ---------------------------------------------------------------------------
CameraPos = Tuple[str, float, float, float]
CAMERA_POSITIONS: List[CameraPos] = [
    # Straight down, ~0.6 m above the bench top.
    ("top",        0.05,  0.00, 1.50),
    # In front of the bench (+X side), high enough to tilt down ~40 deg.
    ("front_+x",   0.60,  0.00, 1.40),
    # Behind the bench (-X side, near the arm marker), looking forward.
    ("back_-x",   -0.50,  0.00, 1.40),
    # Operator's left (+Y side), looking right.
    ("left_+y",    0.05,  0.55, 1.40),
    # Operator's right (-Y side), looking left.
    ("right_-y",   0.05, -0.55, 1.40),
]


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------
def look_at(
    cam_pos: Tuple[float, float, float],
    target: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Return (roll, pitch, yaw) so a camera at ``cam_pos`` points at ``target``.

    Convention used by gz-sim cameras:
      - The camera body's +X axis is the looking direction.
      - +Z is up.
      - The SDF pose RPY is Z-Y-X intrinsic: rotation = Rz(yaw) * Ry(pitch) * Rx(roll).

    With that order, the body +X direction in world frame after rotation is
        ( cos(yaw) * cos(pitch),
          sin(yaw) * cos(pitch),
         -sin(pitch) )
    so for the camera to look at the target we need:
        yaw   = atan2(dy, dx)
        pitch = atan2(-dz, sqrt(dx^2 + dy^2))
    where (dx, dy, dz) = target - cam_pos.

    Roll is set to 0 (no rotation about the look axis -> image stays upright).
    """
    dx = target[0] - cam_pos[0]
    dy = target[1] - cam_pos[1]
    dz = target[2] - cam_pos[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(-dz, horiz)
    return (0.0, pitch, yaw)


def rpy_to_quat(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    """Roll-pitch-yaw (Z-Y-X intrinsic) -> (qx, qy, qz, qw).

    Matches the convention used by SDF <pose> and by look_at() above.
    """
    cr, cp, cy = math.cos(roll / 2.0), math.cos(pitch / 2.0), math.cos(yaw / 2.0)
    sr, sp, sy = math.sin(roll / 2.0), math.sin(pitch / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,  # qx
        cr * sp * cy + sr * cp * sy,  # qy
        cr * cp * sy - sr * sp * cy,  # qz
        cr * cp * cy + sr * sp * sy,  # qw
    )


# ---------------------------------------------------------------------------
# Pose teleport via `gz service` (subprocess, no Python binding needed).
# ---------------------------------------------------------------------------
def set_pose(name: str, x: float, y: float, z: float,
             qx: float, qy: float, qz: float, qw: float) -> bool:
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


# ---------------------------------------------------------------------------
# Image conversion + frame cache
# ---------------------------------------------------------------------------
def msg_to_png(msg, out_path: Path) -> None:
    """gz.msgs.Image (RGB_INT8) -> PNG on disk.

    The SDF declares <format>R8G8B8</format>, so msg.data is a
    flat (height * width * 3) uint8 buffer in RGB order.
    """
    arr = np.frombuffer(msg.data, dtype=np.uint8)
    arr = arr.reshape((msg.height, msg.width, 3))
    PILImage.fromarray(arr, mode="RGB").save(out_path)


class FrameCache:
    """Holds the most recent image received on the topic."""
    def __init__(self) -> None:
        self.latest = None
        self.count = 0
        self.first_seen_at: Optional[float] = None

    def on_image(self, msg) -> None:
        if self.latest is None:
            self.first_seen_at = time.time()
        self.latest = msg
        self.count += 1


def wait_for_first_frame(cache: FrameCache, timeout_s: float = 5.0) -> bool:
    """Return True once we have received at least one image."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if cache.latest is not None:
            return True
        time.sleep(0.1)
    return False


# ---------------------------------------------------------------------------
# Cycle: teleport, dwell, save
# ---------------------------------------------------------------------------
def cycle_once(cache: FrameCache, dwell_s: float, shots: int, save_dir: Path,
               cycle_idx: int) -> int:
    saved = 0
    for label, x, y, z in CAMERA_POSITIONS:
        r, p, yw = look_at((x, y, z), LOOK_AT_TARGET)
        qx, qy, qz, qw = rpy_to_quat(r, p, yw)
        ok = set_pose(CAMERA_MODEL, x, y, z, qx, qy, qz, qw)
        status = "OK" if ok else "FAIL (is gz sim running?)"
        print(
            f"[{label}]  pos=({x:+.2f}, {y:+.2f}, {z:+.2f})  "
            f"-> aim at {LOOK_AT_TARGET}  pitch={math.degrees(p):+.0f}deg "
            f"yaw={math.degrees(yw):+.0f}deg  set_pose={status}"
        )
        if not ok:
            continue
        time.sleep(dwell_s)  # let physics + render + topic catch up

        if cache.latest is None:
            print(f"[{label}]  no image received — is the topic publishing?")
            continue

        for shot in range(shots):
            out = save_dir / f"cycle{cycle_idx:02d}_{label}_{shot}.png"
            msg_to_png(cache.latest, out)
            saved += 1
            print(f"[{label}]  -> {out.resolve()}  "
                  f"({cache.latest.width}x{cache.latest.height})")
            if shots > 1:
                time.sleep(max(0.2, dwell_s / shots))
    return saved


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dwell", type=float, default=2.0,
                   help="seconds to wait at each pose (default: 2)")
    p.add_argument("--loop", action="store_true",
                   help="cycle through views forever (Ctrl+C to stop)")
    p.add_argument("--out", type=Path, default=DEFAULT_SAVE_DIR,
                   help="output folder for PNGs (default: ./captured_frames)")
    p.add_argument("--shots", type=int, default=1,
                   help="PNGs to save per view (default: 1)")
    args = p.parse_args()

    save_dir = args.out.resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"gz-transport Python: {GZ_LABEL}")
    print(f"subscribing to       {CAMERA_TOPIC}")
    print(f"saving PNGs to       {save_dir}/")
    print()

    node = GzNode()
    cache = FrameCache()
    if not node.subscribe(GzImage, CAMERA_TOPIC, cache.on_image):
        sys.exit(
            f"ERROR: subscribe({CAMERA_TOPIC}) returned False.\n"
            "  Is gz sim actually running? Check `gz topic -l` for the topic."
        )

    print("waiting for the first frame ...")
    sub_started_at = time.time()
    if not wait_for_first_frame(cache, timeout_s=5.0):
        print("WARNING: no frame in 5 s. The script will still try, but if")
        print("         nothing saves, common causes are:")
        print("           - gz sim is paused (click ▶ or use -r)")
        print(f"           - topic name differs from {CAMERA_TOPIC}")
        print("             (run `gz topic -l` and grep for image_raw)")
        print("           - gz-transport version mismatch (Harmonic vs Garden)")
    else:
        elapsed = (cache.first_seen_at or sub_started_at) - sub_started_at
        print(f"first frame received after {elapsed:.1f} s "
              f"(got {cache.count} frames so far).")

    total = 0
    cycle_idx = 0
    if args.loop:
        try:
            while True:
                total += cycle_once(cache, args.dwell, args.shots, save_dir, cycle_idx)
                cycle_idx += 1
        except KeyboardInterrupt:
            print()
            print(f"stopped by user. saved {total} PNGs -> {save_dir}/")
    else:
        total = cycle_once(cache, args.dwell, args.shots, save_dir, cycle_idx)
        print()
        print(f"done. saved {total} PNGs -> {save_dir}/")


if __name__ == "__main__":
    main()
