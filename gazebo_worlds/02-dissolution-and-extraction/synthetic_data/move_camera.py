#!/usr/bin/env python3
"""Teleport the overhead camera + save its frames as PNGs + YOLO labels.

What this does, end to end:

  1. Subscribes to /overhead_camera/image_raw via the gz-transport
     Python bindings (NOT ROS, NOT ros_gz_bridge). The subscription
     also forces the sensor to actually render — some gz-sim builds
     skip rendering when no client is connected.
  2. Calls `gz service /world/.../set_pose` to teleport the
     `overhead_camera` model through a list of preset viewpoints.
  3. After waiting `--dwell` seconds at each pose, saves the latest
     received frame as captured_frames/<label>_<N>.png AND a sibling
     <label>_<N>.txt with YOLO labels (one line per labelled object)
     computed by projecting the object's known world-space bounding
     box onto the image with a pinhole camera model.
  4. Writes captured_frames/classes.txt once at startup so the labels
     are self-describing (Ultralytics YOLO expects this file too).
  5. Prints the absolute output path on every save so there is no
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

  --dwell 4      spend 4 s at each view (default 2)
  --loop         cycle forever (Ctrl+C to stop)
  --out PATH     output folder (default ./captured_frames)
  --shots N      PNGs to save per view (default 1)
  --no-overlay   skip the bbox-annotated debug PNGs
                 (default: also save them in <out>/overlays/)
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
# Camera intrinsics — must mirror the <camera> block in ketchup_extraction.sdf
# (overhead_cam sensor). If you change the SDF, update these or the labels
# will not match the pixels.
#
#   horizontal_fov = 1.0472 rad (= 60 deg)
#   image:  640 x 480, format R8G8B8 (square pixels)
# ---------------------------------------------------------------------------
IMG_W = 640
IMG_H = 480
HFOV_RAD = 1.0472
FX = (IMG_W / 2.0) / math.tan(HFOV_RAD / 2.0)
FY = FX  # square pixels => same focal length on both axes
CX = IMG_W / 2.0
CY = IMG_H / 2.0


# ---------------------------------------------------------------------------
# Objects to label.
#
# Each entry is (class_id, class_name, bbox_center_world, bbox_half_extents).
# The bounding box is an axis-aligned box in world frame that wraps the
# object — derived ONCE from the SDF, not measured per frame, because the
# objects are static for now (Step 2 will move them and we'll recompute
# from their reported pose).
#
# Right now we only label the solvent bottle — single-class detection
# is the simplest possible YOLO problem and matches what the user asked
# for. Add more entries here to extend to multi-class.
#
# How we got the solvent bottle bbox from ketchup_extraction.sdf:
#   - <model name="solvent_bottle"> pose: 0.10 0.25 0.975 0 0 0
#   - body cylinder:  r=0.0425, l=0.150  -> z in [0.900, 1.050]
#   - cap cylinder:   r=0.025,  l=0.025, link-local z=+0.0875
#                                         -> z in [1.050, 1.075]
#   - tight AABB:  x = 0.10 +/- 0.0425
#                  y = 0.25 +/- 0.0425
#                  z = 0.900 .. 1.075  (center 0.9875, half-extent 0.0875)
# ---------------------------------------------------------------------------
LabeledObject = Tuple[int, str, Tuple[float, float, float], Tuple[float, float, float]]
LABELED_OBJECTS: List[LabeledObject] = [
    (0, "solvent_bottle", (0.10, 0.25, 0.9875), (0.0425, 0.0425, 0.0875)),
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


def rotmat_from_rpy(roll: float, pitch: float, yaw: float):
    """Z-Y-X intrinsic rotation matrix R = Rz(yaw) * Ry(pitch) * Rx(roll).

    R maps body-frame vectors to world-frame vectors:
        v_world = R * v_body

    For projecting a world point INTO the camera, we want the inverse
    R^T (since R is orthonormal): v_body = R^T * (v_world - cam_pos).
    """
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )


# ---------------------------------------------------------------------------
# Pinhole projection
# ---------------------------------------------------------------------------
def world_to_pixel(
    p_world: Tuple[float, float, float],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> Optional[Tuple[float, float]]:
    """Project a world-frame point to pixel coords (u, v).

    Returns None if the point is behind the camera (so the caller can
    skip the corner without producing a garbage projection).

    Coordinate frames at play here:
      * Camera BODY frame (Gazebo / SDF convention):
            +X = look direction (forward)
            +Y = left
            +Z = up
      * Standard OPTICAL frame (pinhole / OpenCV / image coords):
            +X = right
            +Y = down
            +Z = forward
        So the body -> optical remap is: ox = -by, oy = -bz, oz = bx.

      * Image pixel coords:
            u = focal_x * X_optical / Z_optical + cx
            v = focal_y * Y_optical / Z_optical + cy
        with (cx, cy) = image center, (focal_x, focal_y) derived from
        horizontal FOV. u grows to the right, v grows downward.
    """
    R = rotmat_from_rpy(*cam_rpy)
    dx = p_world[0] - cam_pos[0]
    dy = p_world[1] - cam_pos[1]
    dz = p_world[2] - cam_pos[2]
    # body = R^T * d. We multiply by the columns of R because (R^T)[i][j] = R[j][i].
    bx = R[0][0] * dx + R[1][0] * dy + R[2][0] * dz
    by = R[0][1] * dx + R[1][1] * dy + R[2][1] * dz
    bz = R[0][2] * dx + R[1][2] * dy + R[2][2] * dz
    # body -> optical
    ox, oy, oz = -by, -bz, bx
    if oz <= 1e-6:
        return None  # at or behind the image plane
    u = FX * ox / oz + CX
    v = FY * oy / oz + CY
    return (u, v)


def pixel_bbox_for_aabb(
    center: Tuple[float, float, float],
    half_extents: Tuple[float, float, float],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    """Project a world-frame AABB to a pixel-space rectangle.

    Returns (u_min, v_min, u_max, v_max) clamped to image bounds, or
    None if the box is entirely behind the camera / off-screen.

    Approach: project all 8 corners, take the min/max of the projected
    pixels, clamp to [0, W] x [0, H]. This is the standard "axis-aligned
    bounding box of the projected oriented bounding box" trick — it
    over-estimates by a few pixels at oblique angles but is fine for a
    640x480 dataset and matches what most Replicator / BlenderProc
    pipelines emit out of the box.
    """
    cx_w, cy_w, cz_w = center
    hx, hy, hz = half_extents
    pixels = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corner = (cx_w + sx * hx, cy_w + sy * hy, cz_w + sz * hz)
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
        return None  # the box is fully off-screen after clamping
    return (u_min, v_min, u_max, v_max)


def yolo_bbox_for_aabb(
    center: Tuple[float, float, float],
    half_extents: Tuple[float, float, float],
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    """Project a world-frame AABB to a YOLO-format bbox.

    Returns (cx, cy, w, h) normalised to [0, 1] for use in a YOLO label
    file, or None if the box is entirely behind the camera / off-screen.

    Thin wrapper over ``pixel_bbox_for_aabb()``: same projection, just
    normalised so the same number works at any image resolution. Both
    functions are kept because the overlay drawer needs the raw pixel
    rect and the YOLO writer needs the normalised one.
    """
    rect = pixel_bbox_for_aabb(center, half_extents, cam_pos, cam_rpy)
    if rect is None:
        return None
    u_min, v_min, u_max, v_max = rect
    cu = (u_min + u_max) / 2.0 / IMG_W
    cv = (v_min + v_max) / 2.0 / IMG_H
    cw = (u_max - u_min) / IMG_W
    ch = (v_max - v_min) / IMG_H
    return (cu, cv, cw, ch)


def write_yolo_labels(
    out_path: Path,
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> int:
    """Emit a YOLO .txt sibling for one image. Returns the number of boxes written.

    YOLO format: one line per detection.
        <class_id> <cx_norm> <cy_norm> <w_norm> <h_norm>
    Empty file == no detections in this frame (still a valid YOLO label).
    """
    lines = []
    for class_id, _name, center, half_extents in LABELED_OBJECTS:
        bbox = yolo_bbox_for_aabb(center, half_extents, cam_pos, cam_rpy)
        if bbox is None:
            continue
        cu, cv, cw, ch = bbox
        lines.append(f"{class_id} {cu:.6f} {cv:.6f} {cw:.6f} {ch:.6f}")
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return len(lines)


def write_classes_file(out_dir: Path) -> Path:
    """Write classes.txt — one class name per line, matching class_id order.

    Ultralytics + most labelling tools expect this file. We re-write
    it on every run so it can never go stale relative to LABELED_OBJECTS.
    """
    path = out_dir / "classes.txt"
    by_id = sorted(LABELED_OBJECTS, key=lambda e: e[0])
    path.write_text("\n".join(name for _id, name, _c, _h in by_id) + "\n")
    return path


# ---------------------------------------------------------------------------
# Bbox overlay (visual sanity check — NOT for training)
# ---------------------------------------------------------------------------
def save_overlay(
    msg,
    out_path: Path,
    cam_pos: Tuple[float, float, float],
    cam_rpy: Tuple[float, float, float],
) -> int:
    """Render the same image with one green rectangle per labelled object.

    Lives in an ``overlays/`` subfolder so it never pollutes the YOLO
    training dir — Ultralytics walks the image folder and would
    otherwise pick these up as extra (mislabelled) training images.

    Returns the number of boxes drawn so the caller can print a sanity
    count. If a box is off-screen or behind the camera it is silently
    skipped (the .txt label already records "no detection" for that
    object in this frame).
    """
    arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(
        (msg.height, msg.width, 3)
    )
    im = PILImage.fromarray(arr, mode="RGB")
    draw = PILImageDraw.Draw(im)
    drew = 0
    for class_id, name, center, half_extents in LABELED_OBJECTS:
        rect = pixel_bbox_for_aabb(center, half_extents, cam_pos, cam_rpy)
        if rect is None:
            continue
        u0, v0, u1, v1 = rect
        # Bright green is the standard "ground-truth bbox" colour (red
        # is reserved for model predictions in most viz tools).
        draw.rectangle([u0, v0, u1, v1], outline=(0, 255, 0), width=2)
        # Label text just inside the top-left corner. PIL's default
        # bitmap font is tiny but readable at 640x480 and avoids the
        # need to ship a .ttf file.
        draw.text((u0 + 3, v0 + 3), f"{name} ({class_id})", fill=(0, 255, 0))
        drew += 1
    im.save(out_path)
    return drew


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
               cycle_idx: int, overlay_dir: Optional[Path]) -> int:
    saved = 0
    for label, x, y, z in CAMERA_POSITIONS:
        cam_pos = (x, y, z)
        r, p, yw = look_at(cam_pos, LOOK_AT_TARGET)
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

        # The labels depend only on (cam_pos, cam_rpy) + static world geometry,
        # so all shots from the same viewpoint share the same .txt content.
        # We still emit one .txt per .png so the YOLO trainer sees them paired.
        cam_rpy = (r, p, yw)
        for shot in range(shots):
            img_path = save_dir / f"cycle{cycle_idx:02d}_{label}_{shot}.png"
            txt_path = img_path.with_suffix(".txt")
            msg_to_png(cache.latest, img_path)
            n_boxes = write_yolo_labels(txt_path, cam_pos, cam_rpy)
            extra = ""
            if overlay_dir is not None:
                ov_path = overlay_dir / f"{img_path.stem}_bbox.png"
                drew = save_overlay(cache.latest, ov_path, cam_pos, cam_rpy)
                extra = f"  overlay={drew} -> overlays/{ov_path.name}"
            saved += 1
            print(f"[{label}]  -> {img_path.resolve()}  "
                  f"({cache.latest.width}x{cache.latest.height})  "
                  f"labels={n_boxes} -> {txt_path.name}{extra}")
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

    print(f"gz-transport Python: {GZ_LABEL}")
    print(f"subscribing to       {CAMERA_TOPIC}")
    print(f"saving PNGs to       {save_dir}/")
    print(f"YOLO classes file    {classes_path}  "
          f"({len(LABELED_OBJECTS)} class(es))")
    print(f"image intrinsics     {IMG_W}x{IMG_H}  "
          f"hfov={math.degrees(HFOV_RAD):.0f}deg  fx={FX:.1f}")
    if overlay_dir is not None:
        print(f"bbox overlays to     {overlay_dir}/  "
              f"(disable with --no-overlay)")
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
                total += cycle_once(cache, args.dwell, args.shots, save_dir,
                                    cycle_idx, overlay_dir)
                cycle_idx += 1
        except KeyboardInterrupt:
            print()
            print(f"stopped by user. saved {total} PNGs -> {save_dir}/")
    else:
        total = cycle_once(cache, args.dwell, args.shots, save_dir,
                           cycle_idx, overlay_dir)
        print()
        print(f"done. saved {total} PNGs -> {save_dir}/")


if __name__ == "__main__":
    main()
