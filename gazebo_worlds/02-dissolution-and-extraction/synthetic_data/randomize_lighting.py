#!/usr/bin/env python3
"""Randomise the world lighting + save the camera frames as PNGs + YOLO labels.

This is the **third** of the six domain-randomisation axes from
``docs/synthetic-data/features/01-detection-images-and-masks.md``.
``move_camera.py`` covers axis #1 (camera pose); ``randomize_objects.py``
covers axis #2 (object pose). This script implements axis #3
(lighting): the camera AND every object stay in fixed positions, but
the sun light's direction, colour and intensity change every frame.

What this does, end to end:

  1. Subscribes to /overhead_camera/image_raw via the gz-transport
     Python bindings.
  2. Parks the camera at the fixed overhead pose and parks every
     labelled object back at its SDF default pose. This way the only
     thing varying between frames is the lighting — exactly what
     axis #3 is supposed to demonstrate.
  3. For each of N (default 5) frames:
       a. Picks a random (elevation_deg, azimuth_deg, warmth, intensity)
          for the sun using a seeded RNG.
       b. Builds a gz.msgs.Light request with:
            type        = DIRECTIONAL
            direction   = unit vector pointing FROM sun TO scene
            diffuse     = warmth-tinted colour scaled by intensity
            specular    = 0.2 * diffuse (matches the SDF default ratio)
            cast_shadows = true
            attenuation = SDF defaults (range=1000, c=0.9, l=0.01, q=0.001)
       c. Calls `gz service /world/.../light_config` (the same one the
          GUI's lighting panel uses).
       d. Waits ``--dwell`` seconds so the renderer publishes a frame
          with the new lighting.
       e. Saves frame_NN.png + YOLO labels + overlay (labels are
          static here because objects don't move, but we still emit
          them per-frame so the dataset format matches the other
          DR axes).
  4. Writes captured_frames/classes.txt once at startup.
  5. Also writes captured_frames/lights.jsonl — one JSON line per
     frame recording the exact (direction, diffuse, intensity) the
     sun was set to. Reproducible from disk alone.

Service we hit (see https://gazebosim.org/api/sim/9/light_config.html):

  /world/<world>/light_config  --reqtype gz.msgs.Light  --reptype gz.msgs.Boolean

The world's UserCommands plugin (already loaded in ketchup_extraction.sdf)
is what serves this endpoint — same plugin that serves /set_pose.

NO ROS. NO ros_gz_bridge. Only gz-transport + numpy + Pillow + the
stdlib ``random`` module.

Prerequisites (one-time install) — identical to the sibling scripts:

  Ubuntu 24.04 + Jazzy + Harmonic:
      sudo apt install python3-gz-transport13 python3-gz-msgs10 \
                       python3-numpy python3-pil

  Ubuntu 22.04 + Humble + Garden:
      sudo apt install python3-gz-transport12 python3-gz-msgs9 \
                       python3-numpy python3-pil

Run order — two terminals:

  Terminal 1:  gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
  Terminal 2:  python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_lighting.py

Common flags:

  --frames N     number of randomised frames to capture (default 5)
  --dwell S      seconds to wait at each pose (default 2.0)
  --seed K       RNG seed (default 0) — same seed -> same dataset
  --out PATH     output folder (default ./captured_frames)
  --no-overlay   skip the bbox-annotated overlay PNGs
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
LIGHT_NAME = "sun"  # matches <light name="sun"> in ketchup_extraction.sdf
DEFAULT_SAVE_DIR = Path("captured_frames")


# ---------------------------------------------------------------------------
# gz-transport / gz-msgs Python bindings (same fallback ladder as the
# sibling scripts). Duplicated rather than imported so each script is
# self-contained and copy-pasteable to a new project.
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
# Fixed camera viewpoint + fixed object poses (must match the SDF defaults
# so the labels stay correct without re-reading the SDF every run).
# ---------------------------------------------------------------------------
CAMERA_POSITION: Tuple[float, float, float] = (0.05, 0.00, 1.50)
LOOK_AT_TARGET: Tuple[float, float, float] = (0.05, 0.0, 0.94)

IMG_W = 640
IMG_H = 480
HFOV_RAD = 1.0472
FX = (IMG_W / 2.0) / math.tan(HFOV_RAD / 2.0)
FY = FX
CX = IMG_W / 2.0
CY = IMG_H / 2.0


# Same (class_id, name, model_name, base_pose, half_extents) tuples as
# randomize_objects.py, but the base pose is what we *enforce* every run
# rather than what we jitter away from.
LabelledObject = Tuple[int, str, str, Tuple[float, float, float, float], Tuple[float, float, float]]
LABELLED_OBJECTS: List[LabelledObject] = [
    (0, "solvent_bottle", "solvent_bottle", (0.10,  0.25, 0.975, 0.0),
     (0.0425, 0.0425, 0.0875)),
    (1, "beaker", "beaker_1", (0.05, -0.30, 0.935, 0.0),
     (0.025, 0.025, 0.035)),
    (1, "beaker", "beaker_2", (0.05, -0.18, 0.935, 0.0),
     (0.025, 0.025, 0.035)),
    (1, "beaker", "beaker_3", (0.05, -0.06, 0.935, 0.0),
     (0.025, 0.025, 0.035)),
]


# ---------------------------------------------------------------------------
# Lighting jitter ranges
#
# Elevation = angle above the horizon. We avoid going below ~25 deg so the
# scene isn't lit purely from the side (which looks weird on the overhead
# camera) or from below (which inverts highlights).
#
# Azimuth = compass direction the sun comes FROM. Full 0..360 so the long
# shadow side of every object rotates over the run.
#
# Warmth is a single scalar in [-1, +1] that biases the diffuse colour
# from "cool blue" (~daylight) to "warm orange" (~tungsten). Cheaper than
# implementing a real Kelvin-to-RGB lookup and the visual difference is
# what matters for DR; the absolute temperature doesn't.
#
# Intensity is a multiplicative scale on the diffuse colour. The renderer
# clips per-channel at 1.0, so cranking intensity above ~1.5 mostly
# saturates white rather than over-brightening. Keep the bounds tight.
# ---------------------------------------------------------------------------
ELEVATION_DEG_RANGE = (25.0, 80.0)
AZIMUTH_DEG_RANGE   = (0.0, 360.0)
WARMTH_RANGE        = (-1.0, 1.0)
INTENSITY_RANGE     = (0.45, 1.20)


# ---------------------------------------------------------------------------
# Math helpers (identical to the sibling scripts).
# ---------------------------------------------------------------------------
def look_at(cam_pos, target):
    dx = target[0] - cam_pos[0]
    dy = target[1] - cam_pos[1]
    dz = target[2] - cam_pos[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(-dz, horiz)
    return (0.0, pitch, yaw)


def rpy_to_quat(roll, pitch, yaw):
    cr, cp, cy = math.cos(roll / 2.0), math.cos(pitch / 2.0), math.cos(yaw / 2.0)
    sr, sp, sy = math.sin(roll / 2.0), math.sin(pitch / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def rotmat_from_rpy(roll, pitch, yaw):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )


def world_to_pixel(p_world, cam_pos, cam_rpy):
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


def object_aabb_corners(obj_xyz, obj_yaw, half_extents):
    hx, hy, hz = half_extents
    cy_, sy_ = math.cos(obj_yaw), math.sin(obj_yaw)
    corners = []
    for sx in (-1, 1):
        for s_y in (-1, 1):
            for sz in (-1, 1):
                lx, ly, lz = sx * hx, s_y * hy, sz * hz
                wx = cy_ * lx - sy_ * ly + obj_xyz[0]
                wy = sy_ * lx + cy_ * ly + obj_xyz[1]
                wz = lz + obj_xyz[2]
                corners.append((wx, wy, wz))
    return corners


def pixel_bbox_for_object(obj_xyz, obj_yaw, half_extents, cam_pos, cam_rpy):
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


def yolo_bbox_for_object(obj_xyz, obj_yaw, half_extents, cam_pos, cam_rpy):
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
# Lighting math
# ---------------------------------------------------------------------------
def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def warmth_to_rgb(warmth: float) -> Tuple[float, float, float]:
    """Map a single 'warmth' parameter in [-1, +1] to an (r, g, b) tint.

    -1.0 = cool (slight blue cast, like noon daylight)
    0.0  = neutral white
    +1.0 = warm (slight red/orange cast, like tungsten)

    A real Kelvin-to-RGB curve is non-linear; we use a small linear
    approximation instead because the difference shown in the
    rendered image is what matters for sim-to-real, not the absolute
    colour temperature.
    """
    r = 0.95 + 0.10 * warmth
    g = 0.95
    b = 0.95 - 0.20 * warmth
    return (clamp01(r), clamp01(g), clamp01(b))


def sun_direction(elevation_deg: float, azimuth_deg: float) -> Tuple[float, float, float]:
    """Return the unit vector the sun's rays travel ALONG (i.e. FROM sun TO scene).

    Elevation is angle above the horizontal plane (0 deg = sun on the
    horizon, 90 deg = sun directly overhead). Azimuth is the compass
    direction the sun is IN, measured CCW from world +X.

    The sun's *direction* field expects the direction the rays go,
    which is the negation of the unit vector pointing TOWARDS the
    sun. So for a sun above and to the east:
        towards_sun = ( cos(el)*cos(az), cos(el)*sin(az), sin(el))
        ray_dir     = (-cos(el)*cos(az),-cos(el)*sin(az),-sin(el))
    """
    el = math.radians(elevation_deg)
    az = math.radians(azimuth_deg)
    return (
        -math.cos(el) * math.cos(az),
        -math.cos(el) * math.sin(az),
        -math.sin(el),
    )


# ---------------------------------------------------------------------------
# Per-frame randomisation
# ---------------------------------------------------------------------------
LightSample = Tuple[float, float, float, float]  # (elev_deg, az_deg, warmth, intensity)


def random_light(rng: random.Random) -> LightSample:
    return (
        rng.uniform(*ELEVATION_DEG_RANGE),
        rng.uniform(*AZIMUTH_DEG_RANGE),
        rng.uniform(*WARMTH_RANGE),
        rng.uniform(*INTENSITY_RANGE),
    )


# ---------------------------------------------------------------------------
# YOLO label writing (objects are static here, but we still emit a .txt
# per image so the dataset format matches randomize_objects.py).
# ---------------------------------------------------------------------------
def write_yolo_labels(out_path: Path, cam_pos, cam_rpy) -> int:
    lines = []
    for entry in LABELLED_OBJECTS:
        class_id, _name, _model, (x, y, z, yaw), half_extents = entry
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
    for class_id, name, _model, _base, _hex in LABELLED_OBJECTS:
        by_id.setdefault(class_id, name)
    ordered = [by_id[k] for k in sorted(by_id)]
    path.write_text("\n".join(ordered) + "\n")
    return path


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------
def save_overlay(msg, out_path: Path, cam_pos, cam_rpy) -> int:
    arr = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
    im = PILImage.fromarray(arr, mode="RGB")
    draw = PILImageDraw.Draw(im)
    drew = 0
    for entry in LABELLED_OBJECTS:
        class_id, name, _model, (x, y, z, yaw), half_extents = entry
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
# gz service calls
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


def set_directional_light(
    name: str,
    direction: Tuple[float, float, float],
    diffuse_rgb: Tuple[float, float, float],
    intensity: float,
) -> Tuple[bool, str]:
    """Call /world/<world>/light_config to replace the named directional light.

    Returns (ok, raw_stdout) so the caller can show the error text if
    the request was rejected (very useful when debugging field names).

    We send the full Light message every call rather than a partial
    update — the service treats the request as a complete description
    of the light, so omitting fields can reset them to zero. Specular
    is kept at 0.2 of diffuse (matches the SDF default ratio), and
    attenuation uses the SDF defaults. Direction is the world-frame
    unit vector the rays travel along.
    """
    dr, dg, db = diffuse_rgb
    # Scale diffuse by intensity so it's visible in renderers that
    # ignore the separate 'intensity' field (some Gazebo versions
    # only honour diffuse). gz Harmonic also reads 'intensity' as a
    # multiplier; sending both keeps us forward-compatible.
    dr_i, dg_i, db_i = clamp01(dr * intensity), clamp01(dg * intensity), clamp01(db * intensity)
    sx, sy, sz = direction
    req = (
        f'name: "{name}" '
        f'type: DIRECTIONAL '
        f'diffuse {{ r: {dr_i:.4f} g: {dg_i:.4f} b: {db_i:.4f} a: 1.0 }} '
        f'specular {{ r: {0.2 * dr_i:.4f} g: {0.2 * dg_i:.4f} b: {0.2 * db_i:.4f} a: 1.0 }} '
        f'direction {{ x: {sx:.4f} y: {sy:.4f} z: {sz:.4f} }} '
        f'range: 1000 '
        f'attenuation_constant: 0.9 '
        f'attenuation_linear: 0.01 '
        f'attenuation_quadratic: 0.001 '
        f'cast_shadows: true '
        f'intensity: {intensity:.4f}'
    )
    result = subprocess.run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD}/light_config",
            "--reqtype", "gz.msgs.Light",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "1000",
            "--req", req,
        ],
        capture_output=True, text=True,
    )
    ok = "data: true" in (result.stdout or "")
    return ok, (result.stdout or result.stderr or "").strip()


# ---------------------------------------------------------------------------
# Image conversion + frame cache (same as the sibling scripts).
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
# Setup: pin camera + reset objects to SDF defaults
# ---------------------------------------------------------------------------
def park_scene_to_defaults(cam_rpy) -> None:
    """Park the camera and every labelled object at their SDF defaults.

    Run once before the capture loop so we don't inherit whatever pose
    the previous script left things in. Logs each call but doesn't
    abort on failure — the user can see which one failed and react.
    """
    cqx, cqy, cqz, cqw = rpy_to_quat(*cam_rpy)
    cx, cy, cz = CAMERA_POSITION
    ok = set_pose(CAMERA_MODEL, cx, cy, cz, cqx, cqy, cqz, cqw)
    print(f"  set_pose {CAMERA_MODEL:>16s}: ({cx:+.3f}, {cy:+.3f}, {cz:+.3f}) "
          f"-> {'OK' if ok else 'FAIL'}")
    for entry in LABELLED_OBJECTS:
        _cid, _name, model_name, (x, y, z, yaw), _hex = entry
        qx, qy, qz, qw = rpy_to_quat(0.0, 0.0, yaw)
        ok = set_pose(model_name, x, y, z, qx, qy, qz, qw)
        print(f"  set_pose {model_name:>16s}: ({x:+.3f}, {y:+.3f}, {z:+.3f}) "
              f"yaw={math.degrees(yaw):+.1f}deg -> {'OK' if ok else 'FAIL'}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames", type=int, default=5,
                   help="number of randomised frames to capture (default: 5)")
    p.add_argument("--dwell", type=float, default=2.0,
                   help="seconds to wait after setting the light (default: 2)")
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
    lights_log = save_dir / "lights.jsonl"
    lights_log.write_text("")  # reset for this run

    cam_rpy = look_at(CAMERA_POSITION, LOOK_AT_TARGET)

    print(f"gz-transport Python: {GZ_LABEL}")
    print(f"subscribing to       {CAMERA_TOPIC}")
    print(f"saving PNGs to       {save_dir}/")
    print(f"YOLO classes file    {classes_path}  "
          f"({len(set(e[0] for e in LABELLED_OBJECTS))} class(es), "
          f"{len(LABELLED_OBJECTS)} object(s))")
    print(f"image intrinsics     {IMG_W}x{IMG_H}  "
          f"hfov={math.degrees(HFOV_RAD):.0f}deg  fx={FX:.1f}")
    print(f"camera (fixed)       pos={CAMERA_POSITION}  aim={LOOK_AT_TARGET}  "
          f"pitch={math.degrees(cam_rpy[1]):+.0f}deg yaw={math.degrees(cam_rpy[2]):+.0f}deg")
    print(f"light service        /world/{WORLD}/light_config  (target: '{LIGHT_NAME}')")
    print(f"random seed          {args.seed}  "
          f"(elev={ELEVATION_DEG_RANGE} deg, az={AZIMUTH_DEG_RANGE} deg, "
          f"warmth={WARMTH_RANGE}, intensity={INTENSITY_RANGE})")
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

    print("parking camera + objects at SDF defaults ...")
    park_scene_to_defaults(cam_rpy)

    print("\nwaiting for the first frame ...")
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
        elev_deg, az_deg, warmth, intensity = random_light(rng)
        direction = sun_direction(elev_deg, az_deg)
        diffuse_rgb = warmth_to_rgb(warmth)
        print(f"\n[frame {frame_idx:02d}]")
        print(f"  light  elev={elev_deg:+5.1f}deg  az={az_deg:6.1f}deg  "
              f"warmth={warmth:+.2f}  intensity={intensity:.2f}  "
              f"diffuse=({diffuse_rgb[0]:.2f},{diffuse_rgb[1]:.2f},{diffuse_rgb[2]:.2f})")
        ok, stdout = set_directional_light(LIGHT_NAME, direction, diffuse_rgb, intensity)
        if not ok:
            # Print the raw service reply so the user can see if e.g. the
            # service path is wrong on their gz version. Then skip the
            # frame so we don't pollute the dataset with an old-lighting
            # image relabelled as new-lighting.
            print(f"  light_config FAILED. service stdout/stderr:")
            for line in stdout.splitlines():
                print(f"    {line}")
            continue
        time.sleep(args.dwell)
        if cache.latest is None:
            print("  no image received — is the topic publishing?")
            continue

        img_path = save_dir / f"frame_{frame_idx:02d}.png"
        txt_path = img_path.with_suffix(".txt")
        msg_to_png(cache.latest, img_path)
        n_boxes = write_yolo_labels(txt_path, CAMERA_POSITION, cam_rpy)
        extra = ""
        if overlay_dir is not None:
            ov_path = overlay_dir / f"{img_path.stem}_bbox.png"
            drew = save_overlay(cache.latest, ov_path, CAMERA_POSITION, cam_rpy)
            extra = f"  overlay={drew} -> overlays/{ov_path.name}"

        log_entry = {
            "frame": frame_idx,
            "image": img_path.name,
            "light": {
                "name": LIGHT_NAME,
                "type": "DIRECTIONAL",
                "elevation_deg": elev_deg,
                "azimuth_deg": az_deg,
                "direction": list(direction),
                "warmth": warmth,
                "intensity": intensity,
                "diffuse_rgb": list(diffuse_rgb),
            },
        }
        with lights_log.open("a") as fh:
            fh.write(json.dumps(log_entry) + "\n")

        saved += 1
        print(f"  -> {img_path.resolve()}  ({cache.latest.width}x{cache.latest.height})  "
              f"labels={n_boxes} -> {txt_path.name}{extra}")

    print()
    print(f"done. saved {saved} PNGs -> {save_dir}/")
    print(f"      per-frame lights -> {lights_log}")


if __name__ == "__main__":
    main()
