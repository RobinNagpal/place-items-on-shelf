#!/usr/bin/env python3
"""Randomise object poses + save the camera frames as PNGs + YOLO labels.

This is the **second** of the six domain-randomisation axes from
``docs/synthetic-data/features/01-detection-images-and-masks.md``.
``move_camera.py`` already implements axis #1 (camera pose). This
script implements axis #2 (object pose): the camera sits still, but
every labelled object on the bench (the solvent bottle + the three
beakers) is teleported to a new (x, y, yaw) every frame.

What this does, end to end:

  1. Subscribes to /overhead_camera/image_raw via the gz-transport
     Python bindings (same plumbing as ``move_camera.py``).
  2. Picks the overhead "top" camera viewpoint and **leaves the camera
     there for the whole run** — no camera jitter.
  3. For each of N (default 5) frames:
       a. Draws a fresh random (dx, dy, dyaw) for every entry in
          ``RANDOMISED_OBJECTS`` using a seeded RNG so the run is
          reproducible.
       b. Calls `gz service /world/.../set_pose` once per object to
          teleport it. z is held fixed so the objects stay on the
          bench (they would just fall through the floor otherwise).
       c. Waits ``--dwell`` seconds for the next sensor frame.
       d. Saves the latest frame as captured_frames/frame_NN.png
          plus a sibling frame_NN.txt YOLO label computed by
          projecting each object's rotated world-space AABB onto
          the image.
  4. Writes captured_frames/classes.txt once at startup.
  5. Also writes captured_frames/poses.jsonl — one JSON line per
     frame recording the exact pose every object was teleported to.
     That makes the dataset fully reproducible from disk alone.
  6. Prints the absolute output path on every save.

NO ROS. NO ros_gz_bridge. Only gz-transport + numpy + Pillow + the
stdlib ``random`` module.

Prerequisites (one-time install) — same as ``move_camera.py``:

  Ubuntu 24.04 + Jazzy + Harmonic:
      sudo apt install python3-gz-transport13 python3-gz-msgs10 \
                       python3-numpy python3-pil

  Ubuntu 22.04 + Humble + Garden:
      sudo apt install python3-gz-transport12 python3-gz-msgs9 \
                       python3-numpy python3-pil

Run order — two terminals, same as ``move_camera.py``:

  Terminal 1:  gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
  Terminal 2:  python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_objects.py

Common flags:

  --frames N     number of randomised frames to capture (default 5)
  --dwell S      seconds to wait at each pose so the sensor publishes
                 a fresh image (default 2.0)
  --seed K       RNG seed (default 0) — same seed -> same dataset
  --out PATH     output folder (default ./captured_frames)
  --no-overlay   skip the bbox-annotated debug PNGs
                 (default: also save them under <out>/overlays/)
"""

from __future__ import annotations

import argparse
import json
import math
import random
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
# gz-transport / gz-msgs Python bindings (identical to move_camera.py).
# Kept duplicated rather than imported so each script is self-contained
# and can be copied to a fresh project without dragging the other along.
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
    )


def _import_image_libs():
    try:
        import numpy as np  # type: ignore
        from PIL import Image as PILImage  # type: ignore
        from PIL import ImageDraw as PILImageDraw  # type: ignore
        return np, PILImage, PILImageDraw
    except ImportError as e:
        sys.exit(
            "ERROR: numpy and Pillow are required to write PNGs.\n"
            f"  last import error: {e}\n"
            "  fix:  sudo apt install python3-numpy python3-pil\n"
        )


GzNode, GzImage, GZ_LABEL = _import_gz_bindings()
np, PILImage, PILImageDraw = _import_image_libs()


# ---------------------------------------------------------------------------
# Fixed camera viewpoint for the whole run.
#
# We deliberately do NOT vary the camera — that is what ``move_camera.py``
# already does. Picking the straight-down "top" view keeps the math
# simple (the object x/y jitter shows up cleanly as image-plane motion)
# and matches axis #2 of the DR doc: "every object's translation and
# yaw randomised per frame, camera fixed".
# ---------------------------------------------------------------------------
CAMERA_POSITION: Tuple[float, float, float] = (0.05, 0.00, 1.50)
LOOK_AT_TARGET: Tuple[float, float, float] = (0.05, 0.0, 0.94)


# ---------------------------------------------------------------------------
# Camera intrinsics — must mirror the <camera> block in ketchup_extraction.sdf
# (overhead_cam sensor). Identical to move_camera.py.
# ---------------------------------------------------------------------------
IMG_W = 640
IMG_H = 480
HFOV_RAD = 1.0472
FX = (IMG_W / 2.0) / math.tan(HFOV_RAD / 2.0)
FY = FX  # square pixels => same focal length on both axes
CX = IMG_W / 2.0
CY = IMG_H / 2.0


# ---------------------------------------------------------------------------
# Objects to randomise + label.
#
# Each entry is (class_id, class_name, model_name, base_pose, half_extents).
#   - ``base_pose``    = (x, y, z, yaw) read straight off the SDF default.
#   - ``half_extents`` = local-frame AABB half-sizes for the object's
#                       union of body+cap (used for the projected bbox).
#
# For *cylindrical* objects yaw doesn't actually change the world-space
# AABB (a cylinder is rotationally symmetric about z). We still apply
# the rotation in ``object_aabb_corners()`` so the same code path works
# for non-cylindrical models we may add later.
#
# Translation jitter (TRANS_JITTER_M) and yaw jitter (YAW_JITTER_RAD)
# follow the rule-of-thumb numbers from the DR doc: ~5 cm and ~20 deg.
# ---------------------------------------------------------------------------
RandomisedObject = Tuple[int, str, str, Tuple[float, float, float, float], Tuple[float, float, float]]
RANDOMISED_OBJECTS: List[RandomisedObject] = [
    # (class_id, class_name, model_name, (x, y, z, yaw), (hx, hy, hz))
    # solvent_bottle: body Ø85x150 + cap Ø50x25 at link z=+0.0875
    #   tight world AABB centred at z = 0.9875, half-z = 0.0875
    #   The model's <pose> is (0.10, 0.25, 0.975, yaw=0), so the AABB
    #   centre sits 0.0125 m ABOVE the model origin in z.
    (0, "solvent_bottle", "solvent_bottle", (0.10,  0.25, 0.975, 0.0),
     (0.0425, 0.0425, 0.0875)),
    # beakers: glass cylinder r=0.025, length=0.070
    #   model <pose> z = 0.935 -> bottom at 0.900, top at 0.970
    #   AABB centred at the model pose z, half-z = 0.035
    (1, "beaker", "beaker_1", (0.05, -0.30, 0.935, 0.0),
     (0.025, 0.025, 0.035)),
    (1, "beaker", "beaker_2", (0.05, -0.18, 0.935, 0.0),
     (0.025, 0.025, 0.035)),
    (1, "beaker", "beaker_3", (0.05, -0.06, 0.935, 0.0),
     (0.025, 0.025, 0.035)),
]
TRANS_JITTER_M = 0.05   # +/- 5 cm in x and y (z held fixed so things stay on the bench)
YAW_JITTER_RAD = math.radians(20.0)  # +/- 20 deg about world z


# ---------------------------------------------------------------------------
# Math helpers — identical to move_camera.py.
# ---------------------------------------------------------------------------
def look_at(
    cam_pos: Tuple[float, float, float],
    target: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Return (roll, pitch, yaw) so a camera at ``cam_pos`` points at ``target``."""
    dx = target[0] - cam_pos[0]
    dy = target[1] - cam_pos[1]
    dz = target[2] - cam_pos[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(-dz, horiz)
    return (0.0, pitch, yaw)


def rpy_to_quat(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    cr, cp, cy = math.cos(roll / 2.0), math.cos(pitch / 2.0), math.cos(yaw / 2.0)
    sr, sp, sy = math.sin(roll / 2.0), math.sin(pitch / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,  # qx
        cr * sp * cy + sr * cp * sy,  # qy
        cr * cp * sy - sr * sp * cy,  # qz
        cr * cp * cy + sr * sp * sy,  # qw
    )


def rotmat_from_rpy(roll: float, pitch: float, yaw: float):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )


# ---------------------------------------------------------------------------
# Pinhole projection — identical to move_camera.py.
# ---------------------------------------------------------------------------
def world_to_pixel(
    p_world: Tuple[float, float, float],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> Optional[Tuple[float, float]]:
    R = rotmat_from_rpy(*cam_rpy)
    dx = p_world[0] - cam_pos[0]
    dy = p_world[1] - cam_pos[1]
    dz = p_world[2] - cam_pos[2]
    bx = R[0][0] * dx + R[1][0] * dy + R[2][0] * dz
    by = R[0][1] * dx + R[1][1] * dy + R[2][1] * dz
    bz = R[0][2] * dx + R[1][2] * dy + R[2][2] * dz
    ox, oy, oz = -by, -bz, bx
    if oz <= 1e-6:
        return None
    return (FX * ox / oz + CX, FY * oy / oz + CY)


def object_aabb_corners(
    obj_xyz: Tuple[float, float, float],
    obj_yaw: float,
    half_extents: Tuple[float, float, float],
) -> List[Tuple[float, float, float]]:
    """Return the 8 world-frame corners of an object's local AABB.

    The object is at world position ``obj_xyz`` rotated by ``obj_yaw``
    about world z (no roll/pitch — the bench is flat). The local AABB
    has half-sizes ``half_extents`` in the object's own frame and is
    centred on the object's origin. The 8 corners are returned in
    world frame so the projection code can treat them as plain points.
    """
    hx, hy, hz = half_extents
    cy_, sy_ = math.cos(obj_yaw), math.sin(obj_yaw)
    corners: List[Tuple[float, float, float]] = []
    for sx in (-1, 1):
        for s_y in (-1, 1):
            for sz in (-1, 1):
                lx, ly, lz = sx * hx, s_y * hy, sz * hz
                wx = cy_ * lx - sy_ * ly + obj_xyz[0]
                wy = sy_ * lx + cy_ * ly + obj_xyz[1]
                wz = lz + obj_xyz[2]
                corners.append((wx, wy, wz))
    return corners


def pixel_bbox_for_object(
    obj_xyz: Tuple[float, float, float],
    obj_yaw: float,
    half_extents: Tuple[float, float, float],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    """Project a yawed object AABB to a clamped pixel-space rectangle."""
    pixels = []
    for corner in object_aabb_corners(obj_xyz, obj_yaw, half_extents):
        p = world_to_pixel(corner, cam_pos, cam_rpy)
        if p is not None:
            pixels.append(p)
    if not pixels:
        return None
    us = [p[0] for p in pixels]
    vs = [p[1] for p in pixels]
    u_min = max(0.0, min(us))
    u_max = min(float(IMG_W), max(us))
    v_min = max(0.0, min(vs))
    v_max = min(float(IMG_H), max(vs))
    if u_max <= u_min or v_max <= v_min:
        return None
    return (u_min, v_min, u_max, v_max)


def yolo_bbox_for_object(
    obj_xyz: Tuple[float, float, float],
    obj_yaw: float,
    half_extents: Tuple[float, float, float],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    rect = pixel_bbox_for_object(obj_xyz, obj_yaw, half_extents, cam_pos, cam_rpy)
    if rect is None:
        return None
    u_min, v_min, u_max, v_max = rect
    cu = (u_min + u_max) / 2.0 / IMG_W
    cv = (v_min + v_max) / 2.0 / IMG_H
    cw = (u_max - u_min) / IMG_W
    ch = (v_max - v_min) / IMG_H
    return (cu, cv, cw, ch)


# ---------------------------------------------------------------------------
# Per-frame randomisation
# ---------------------------------------------------------------------------
def jittered_poses(rng: random.Random) -> List[Tuple[RandomisedObject, Tuple[float, float, float, float]]]:
    """Return ``(entry, (x, y, z, yaw))`` for every randomised object.

    z is held fixed at the base value because we want the objects to
    stay on the bench top; jittering z would either levitate them
    above the surface or push them into the table. x/y get uniform
    noise of +/- TRANS_JITTER_M, yaw +/- YAW_JITTER_RAD.
    """
    out = []
    for entry in RANDOMISED_OBJECTS:
        _cid, _name, _model, (bx, by, bz, byaw), _hex = entry
        x = bx + rng.uniform(-TRANS_JITTER_M, TRANS_JITTER_M)
        y = by + rng.uniform(-TRANS_JITTER_M, TRANS_JITTER_M)
        yaw = byaw + rng.uniform(-YAW_JITTER_RAD, YAW_JITTER_RAD)
        out.append((entry, (x, y, bz, yaw)))
    return out


# ---------------------------------------------------------------------------
# YOLO label writing
# ---------------------------------------------------------------------------
def write_yolo_labels(
    out_path: Path,
    poses: List[Tuple[RandomisedObject, Tuple[float, float, float, float]]],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> int:
    lines = []
    for entry, (x, y, z, yaw) in poses:
        class_id, _name, _model, _base, half_extents = entry
        bbox = yolo_bbox_for_object((x, y, z), yaw, half_extents, cam_pos, cam_rpy)
        if bbox is None:
            continue
        cu, cv, cw, ch = bbox
        lines.append(f"{class_id} {cu:.6f} {cv:.6f} {cw:.6f} {ch:.6f}")
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return len(lines)


def write_classes_file(out_dir: Path) -> Path:
    path = out_dir / "classes.txt"
    by_id = {}
    for class_id, name, _model, _base, _hex in RANDOMISED_OBJECTS:
        by_id.setdefault(class_id, name)
    ordered = [by_id[k] for k in sorted(by_id)]
    path.write_text("\n".join(ordered) + "\n")
    return path


# ---------------------------------------------------------------------------
# Overlay (visual sanity check — NOT for training)
# ---------------------------------------------------------------------------
def save_overlay(
    msg,
    out_path: Path,
    poses: List[Tuple[RandomisedObject, Tuple[float, float, float, float]]],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> int:
    arr = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
    im = PILImage.fromarray(arr, mode="RGB")
    draw = PILImageDraw.Draw(im)
    drew = 0
    for entry, (x, y, z, yaw) in poses:
        class_id, name, _model, _base, half_extents = entry
        rect = pixel_bbox_for_object((x, y, z), yaw, half_extents, cam_pos, cam_rpy)
        if rect is None:
            continue
        u0, v0, u1, v1 = rect
        draw.rectangle([u0, v0, u1, v1], outline=(0, 255, 0), width=2)
        draw.text((u0 + 3, v0 + 3), f"{name} ({class_id})", fill=(0, 255, 0))
        drew += 1
    im.save(out_path)
    return drew


# ---------------------------------------------------------------------------
# Pose teleport via `gz service` (identical to move_camera.py).
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
# Image conversion + frame cache (identical to move_camera.py).
# ---------------------------------------------------------------------------
def msg_to_png(msg, out_path: Path) -> None:
    arr = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
    PILImage.fromarray(arr, mode="RGB").save(out_path)


class FrameCache:
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
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if cache.latest is not None:
            return True
        time.sleep(0.1)
    return False


# ---------------------------------------------------------------------------
# Main capture loop
# ---------------------------------------------------------------------------
def teleport_objects(
    poses: List[Tuple[RandomisedObject, Tuple[float, float, float, float]]],
) -> bool:
    """Apply every (x, y, z, yaw) via `set_pose`. Returns True if all calls OK."""
    all_ok = True
    for entry, (x, y, z, yaw) in poses:
        _cid, name, model_name, _base, _hex = entry
        qx, qy, qz, qw = rpy_to_quat(0.0, 0.0, yaw)
        ok = set_pose(model_name, x, y, z, qx, qy, qz, qw)
        if not ok:
            all_ok = False
            print(f"  set_pose {model_name}: FAIL (is gz sim running?)")
        else:
            print(
                f"  set_pose {model_name:>16s}: pos=({x:+.3f}, {y:+.3f}, {z:+.3f})  "
                f"yaw={math.degrees(yaw):+.1f}deg  OK"
            )
    return all_ok


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames", type=int, default=5,
                   help="number of randomised frames to capture (default: 5)")
    p.add_argument("--dwell", type=float, default=2.0,
                   help="seconds to wait at each pose (default: 2)")
    p.add_argument("--seed", type=int, default=0,
                   help="RNG seed — same seed reproduces the same dataset (default: 0)")
    p.add_argument("--out", type=Path, default=DEFAULT_SAVE_DIR,
                   help="output folder for PNGs (default: ./captured_frames)")
    p.add_argument(
        "--no-overlay",
        dest="overlay",
        action="store_false",
        help="skip the bbox-annotated overlay PNGs "
             "(default: also save them under <out>/overlays/)",
    )
    p.set_defaults(overlay=True)
    args = p.parse_args()

    save_dir = args.out.resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    classes_path = write_classes_file(save_dir)
    overlay_dir: Optional[Path] = None
    if args.overlay:
        overlay_dir = save_dir / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)
    poses_log = save_dir / "poses.jsonl"
    poses_log.write_text("")  # reset for this run

    cam_rpy = look_at(CAMERA_POSITION, LOOK_AT_TARGET)

    print(f"gz-transport Python: {GZ_LABEL}")
    print(f"subscribing to       {CAMERA_TOPIC}")
    print(f"saving PNGs to       {save_dir}/")
    print(f"YOLO classes file    {classes_path}  "
          f"({len(set(e[0] for e in RANDOMISED_OBJECTS))} class(es), "
          f"{len(RANDOMISED_OBJECTS)} object(s))")
    print(f"image intrinsics     {IMG_W}x{IMG_H}  "
          f"hfov={math.degrees(HFOV_RAD):.0f}deg  fx={FX:.1f}")
    print(f"camera (fixed)       pos={CAMERA_POSITION}  aim={LOOK_AT_TARGET}  "
          f"pitch={math.degrees(cam_rpy[1]):+.0f}deg yaw={math.degrees(cam_rpy[2]):+.0f}deg")
    print(f"random seed          {args.seed}  "
          f"(jitter: +/-{TRANS_JITTER_M*100:.0f} cm x/y, "
          f"+/-{math.degrees(YAW_JITTER_RAD):.0f} deg yaw)")
    if overlay_dir is not None:
        print(f"bbox overlays to     {overlay_dir}/  (disable with --no-overlay)")
    else:
        print("bbox overlays        OFF (--no-overlay was passed)")
    print()

    node = GzNode()
    cache = FrameCache()
    if not node.subscribe(GzImage, CAMERA_TOPIC, cache.on_image):
        sys.exit(
            f"ERROR: subscribe({CAMERA_TOPIC}) returned False.\n"
            "  Is gz sim actually running? Check `gz topic -l` for the topic."
        )

    # Park the camera at the fixed viewpoint ONCE, then leave it there.
    cqx, cqy, cqz, cqw = rpy_to_quat(*cam_rpy)
    if not set_pose(CAMERA_MODEL, *CAMERA_POSITION, cqx, cqy, cqz, cqw):
        print("WARNING: failed to set the camera pose — using whatever pose")
        print("         the SDF default is. Labels still match the FIXED")
        print("         (CAMERA_POSITION, LOOK_AT_TARGET) defined in this script,")
        print("         so if those disagree your bboxes will be wrong.")

    print("waiting for the first frame ...")
    sub_started_at = time.time()
    if not wait_for_first_frame(cache, timeout_s=5.0):
        print("WARNING: no frame in 5 s. Common causes: gz sim paused, wrong")
        print("         topic, gz-transport version mismatch.")
    else:
        elapsed = (cache.first_seen_at or sub_started_at) - sub_started_at
        print(f"first frame received after {elapsed:.1f} s "
              f"(got {cache.count} frames so far).")

    rng = random.Random(args.seed)
    saved = 0
    for frame_idx in range(args.frames):
        print(f"\n[frame {frame_idx:02d}]")
        poses = jittered_poses(rng)
        if not teleport_objects(poses):
            print("  one or more set_pose calls failed — skipping this frame.")
            continue
        time.sleep(args.dwell)
        if cache.latest is None:
            print("  no image received — is the topic publishing?")
            continue

        img_path = save_dir / f"frame_{frame_idx:02d}.png"
        txt_path = img_path.with_suffix(".txt")
        msg_to_png(cache.latest, img_path)
        n_boxes = write_yolo_labels(txt_path, poses, CAMERA_POSITION, cam_rpy)
        extra = ""
        if overlay_dir is not None:
            ov_path = overlay_dir / f"{img_path.stem}_bbox.png"
            drew = save_overlay(cache.latest, ov_path, poses, CAMERA_POSITION, cam_rpy)
            extra = f"  overlay={drew} -> overlays/{ov_path.name}"

        # Reproducibility log: one line per frame with every object's pose.
        log_entry = {
            "frame": frame_idx,
            "image": img_path.name,
            "objects": [
                {
                    "class_id": e[0],
                    "class_name": e[1],
                    "model": e[2],
                    "x": x, "y": y, "z": z, "yaw": yaw,
                }
                for e, (x, y, z, yaw) in poses
            ],
        }
        with poses_log.open("a") as fh:
            fh.write(json.dumps(log_entry) + "\n")

        saved += 1
        print(f"  -> {img_path.resolve()}  ({cache.latest.width}x{cache.latest.height})  "
              f"labels={n_boxes} -> {txt_path.name}{extra}")

    print()
    print(f"done. saved {saved} PNGs -> {save_dir}/")
    print(f"      per-frame poses -> {poses_log}")


if __name__ == "__main__":
    main()
