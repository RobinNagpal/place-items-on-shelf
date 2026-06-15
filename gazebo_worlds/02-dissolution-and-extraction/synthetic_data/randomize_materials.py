#!/usr/bin/env python3
"""Randomise materials (object + bench colours) + save frames as PNGs + YOLO labels.

This is the **fourth** of the six domain-randomisation axes from
``docs/synthetic-data/features/01-detection-images-and-masks.md``. It
completes the set started by:

  - ``move_camera.py``         axis #1, camera pose
  - ``randomize_objects.py``   axis #2, object pose
  - ``randomize_lighting.py``  axis #3, lighting
  - ``randomize_distractors.py`` axis #5, distractors
  - ``randomize_background.py`` axis #6, background plane

Axis #4 is *materials / textures*: the camera, every object pose, the
lighting and the bench layout all stay fixed; what changes per frame
is the **colour every visible surface is painted in**. Specifically:

  1. The bench top gets re-painted by spawning a thin coloured plane
     on top of it (same trick ``randomize_background.py`` uses).
  2. Each labelled object — the solvent bottle and the three beakers
     — gets WRAPPED by a slightly larger, fully-opaque coloured
     cylinder spawned at the object's pose. From the overhead camera
     the wrap fully obscures the original glass / blue cap, so the
     viewer sees a coloured cylinder of the right *shape* but a
     random colour.

This is the "structured DR" trick: teach the detector that "a
cylindrical thing of these dimensions on the bench" is a beaker
regardless of its colour, by varying the colour every frame while
keeping the geometry constant. Same idea for the solvent bottle.

The YOLO labels are **identical** across every frame here — the
labelled objects don't move, and the wraps are concentric with them
and only ~1 mm larger, so the pixel-space bbox is essentially the
same. We re-emit the .txt sibling per frame anyway so the on-disk
format matches the other DR axes.

What this does, end to end:

  1. Subscribes to /overhead_camera/image_raw via gz-transport.
  2. Parks the camera + every labelled object at the SDF defaults.
  3. For each of N (default 5) frames:
       a. Picks a random ``(hue, saturation, value)`` per element
          using the seeded RNG, converts to RGB.
       b. Spawns:
            - one bench-top mat plane (``material_bench``)
            - one wrap cylinder per labelled object
              (``material_bottle``, ``material_beaker_1``, ...).
       c. Waits ``--dwell`` seconds for the renderer to catch up.
       d. Saves frame_NN.png + frame_NN.txt + overlay.
       e. Removes every spawned model so the next frame starts from
          a clean scene.
  4. Writes captured_frames/materials.jsonl recording the exact
     colours used per frame so the dataset is reproducible from
     disk alone.

NO ROS. NO ros_gz_bridge.

Why we don't use ``/world/<world>/material_color`` directly:
Gazebo Harmonic does ship a topic-based MaterialColor mechanism,
but it needs the ``gz::sim::systems::MaterialColor`` plugin loaded
in the world SDF AND its semantics around entity-name matching
differ between releases. Spawning a coloured overlay model uses
the same ``EntityFactory`` plumbing as the distractor / background
scripts, works on every Garden+ release with ``UserCommands``, and
needs zero SDF edits to the existing world.

Prerequisites — same as the sibling scripts.

Run order:

  Terminal 1:  gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
  Terminal 2:  python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_materials.py

Common flags:

  --frames N     number of randomised frames (default 5)
  --dwell S      seconds to wait after spawning (default 2)
  --seed K       RNG seed (default 0)
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
DEFAULT_SAVE_DIR = Path("captured_frames")


# ---------------------------------------------------------------------------
# gz-transport / gz-msgs bindings.
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
        "Install (Harmonic): sudo apt install python3-gz-transport13 python3-gz-msgs10\n"
        "Install (Garden):   sudo apt install python3-gz-transport12 python3-gz-msgs9\n"
    )


def _import_image_libs():
    try:
        import numpy as np  # type: ignore
        from PIL import Image as PILImage  # type: ignore
        from PIL import ImageDraw as PILImageDraw  # type: ignore
        return np, PILImage, PILImageDraw
    except ImportError as e:
        sys.exit(
            "ERROR: numpy + Pillow required.\n"
            f"  last import error: {e}\n"
            "  fix:  sudo apt install python3-numpy python3-pil\n"
        )


GzNode, GzImage, GZ_LABEL = _import_gz_bindings()
np, PILImage, PILImageDraw = _import_image_libs()


# ---------------------------------------------------------------------------
# Fixed camera + labelled object poses (must match SDF defaults).
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
# Bench mat (top plane) — same trick the background script uses.
# ---------------------------------------------------------------------------
BENCH_TOP_Z = 0.900
MAT_X = 0.0
MAT_Y = 0.0
MAT_Z = BENCH_TOP_Z + 0.001  # plane CENTRE 1 mm above bench top
MAT_SIZE_X = 0.50
MAT_SIZE_Y = 0.85
MAT_THICKNESS = 0.002

MAT_MODEL_NAME = "material_bench"


# ---------------------------------------------------------------------------
# Object wraps.
#
# Each labelled object gets an OPAQUE cylinder spawned at its world
# pose. The wrap is slightly larger than the original
# (``WRAP_RADIUS_MARGIN_M`` extra radius, full original height) so it
# fully covers the glass / blue cap / water visual underneath. From the
# overhead camera you see only the coloured wrap.
#
# Because the wrap is concentric with the original, the YOLO bbox we
# emit (using the labelled object's own half-extents) still matches
# the on-screen wrap to within ~1 mm — well below the bbox-rounding
# we apply for YOLO labels.
# ---------------------------------------------------------------------------
WRAP_RADIUS_MARGIN_M = 0.0015  # 1.5 mm extra radius to fully hide the original

# Per-object wrap geometry, derived once from the SDF:
#   - solvent_bottle: full envelope = body (Ø85x150) + cap (Ø50x25)
#     centred at world (0.10, 0.25, 0.9875), total height 0.175 m
#   - beaker:         glass cylinder Ø50x70 mm, centred at (0.05, y, 0.935)
WrapDef = Tuple[str, str, Tuple[float, float, float], float, float]
WRAPS: List[WrapDef] = [
    # (slug,           model_name,        world_xyz,           radius,  length)
    ("solvent_bottle", "material_bottle", (0.10,  0.25, 0.9875), 0.0425, 0.175),
    ("beaker_1",       "material_beaker_1", (0.05, -0.30, 0.935), 0.025, 0.070),
    ("beaker_2",       "material_beaker_2", (0.05, -0.18, 0.935), 0.025, 0.070),
    ("beaker_3",       "material_beaker_3", (0.05, -0.06, 0.935), 0.025, 0.070),
]

# Bench mat counts as a fifth recoloured element. The order of colour
# allocation per frame is: [bench, solvent_bottle, beaker_1, beaker_2, beaker_3].
N_ELEMENTS = 1 + len(WRAPS)


# ---------------------------------------------------------------------------
# Colour sampling.
#
# Sampling in HSV (with high saturation + value) gives vivid, visibly
# distinct colours every frame. Pure RGB sampling tends to produce dull
# midtones that all look greyish under Gazebo's default lighting.
# ---------------------------------------------------------------------------
SAT_RANGE = (0.65, 1.00)
VAL_RANGE = (0.65, 1.00)


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[float, float, float]:
    """h, s, v in [0, 1] -> (r, g, b) in [0, 1].

    Standard 6-sector HSV -> RGB conversion. Matches colorsys.hsv_to_rgb
    but kept inline so the script has no extra imports.
    """
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0: return v, t, p
    if i == 1: return q, v, p
    if i == 2: return p, v, t
    if i == 3: return p, q, v
    if i == 4: return t, p, v
    return v, p, q


def random_colour(rng: random.Random) -> Tuple[float, float, float]:
    h = rng.random()
    s = rng.uniform(*SAT_RANGE)
    v = rng.uniform(*VAL_RANGE)
    return hsv_to_rgb(h, s, v)


# ---------------------------------------------------------------------------
# Math helpers (identical to the sibling scripts).
# ---------------------------------------------------------------------------
def look_at(cam_pos, target):
    dx = target[0] - cam_pos[0]; dy = target[1] - cam_pos[1]; dz = target[2] - cam_pos[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    return (0.0, math.atan2(-dz, horiz), math.atan2(dy, dx))


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
    dx = p_world[0] - cam_pos[0]; dy = p_world[1] - cam_pos[1]; dz = p_world[2] - cam_pos[2]
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
                corners.append((
                    cy_ * lx - sy_ * ly + obj_xyz[0],
                    sy_ * lx + cy_ * ly + obj_xyz[1],
                    lz + obj_xyz[2],
                ))
    return corners


def pixel_bbox_for_object(obj_xyz, obj_yaw, half_extents, cam_pos, cam_rpy):
    pixels = []
    for corner in object_aabb_corners(obj_xyz, obj_yaw, half_extents):
        p = world_to_pixel(corner, cam_pos, cam_rpy)
        if p is not None:
            pixels.append(p)
    if not pixels:
        return None
    us = [p[0] for p in pixels]; vs = [p[1] for p in pixels]
    u_min = max(0.0, min(us)); u_max = min(float(IMG_W), max(us))
    v_min = max(0.0, min(vs)); v_max = min(float(IMG_H), max(vs))
    if u_max <= u_min or v_max <= v_min:
        return None
    return (u_min, v_min, u_max, v_max)


def yolo_bbox_for_object(obj_xyz, obj_yaw, half_extents, cam_pos, cam_rpy):
    rect = pixel_bbox_for_object(obj_xyz, obj_yaw, half_extents, cam_pos, cam_rpy)
    if rect is None:
        return None
    u_min, v_min, u_max, v_max = rect
    return ((u_min + u_max) / 2.0 / IMG_W,
            (v_min + v_max) / 2.0 / IMG_H,
            (u_max - u_min) / IMG_W,
            (v_max - v_min) / IMG_H)


# ---------------------------------------------------------------------------
# Labels / classes / overlay (objects are static -> labels are static).
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
# gz services: create / remove / set_pose.
# ---------------------------------------------------------------------------
def _pb_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def build_bench_mat_sdf(name: str, color_rgb: Tuple[float, float, float]) -> str:
    r = color_rgb
    size = f"{MAT_SIZE_X} {MAT_SIZE_Y} {MAT_THICKNESS}"
    return (
        "<?xml version='1.0'?>"
        "<sdf version='1.10'>"
        f"<model name='{name}'>"
        f"  <static>true</static>"
        f"  <link name='link'>"
        f"    <visual name='v'>"
        f"      <geometry><box><size>{size}</size></box></geometry>"
        f"      <material>"
        f"        <ambient>{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} 1</ambient>"
        f"        <diffuse>{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} 1</diffuse>"
        f"      </material>"
        f"    </visual>"
        f"    <collision name='c'>"
        f"      <geometry><box><size>{size}</size></box></geometry>"
        f"    </collision>"
        f"  </link>"
        f"</model>"
        "</sdf>"
    )


def build_wrap_sdf(name: str, radius: float, length: float,
                   color_rgb: Tuple[float, float, float]) -> str:
    """Build a coloured cylinder slightly larger than the wrapped object.

    Static so it never falls; visual + matching collision (the
    distractor / background scripts that work always have both).
    """
    r = color_rgb
    cyl = f"<cylinder><radius>{radius:.4f}</radius><length>{length:.4f}</length></cylinder>"
    return (
        "<?xml version='1.0'?>"
        "<sdf version='1.10'>"
        f"<model name='{name}'>"
        f"  <static>true</static>"
        f"  <link name='link'>"
        f"    <visual name='v'>"
        f"      <geometry>{cyl}</geometry>"
        f"      <material>"
        f"        <ambient>{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} 1</ambient>"
        f"        <diffuse>{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} 1</diffuse>"
        f"      </material>"
        f"    </visual>"
        f"    <collision name='c'>"
        f"      <geometry>{cyl}</geometry>"
        f"    </collision>"
        f"  </link>"
        f"</model>"
        "</sdf>"
    )


def spawn_model(name: str, sdf_xml: str, x: float, y: float, z: float) -> Tuple[bool, str]:
    req = (
        f'sdf: "{_pb_str(sdf_xml)}" '
        f'name: "{_pb_str(name)}" '
        f'pose {{ position {{ x: {x} y: {y} z: {z} }} '
        f'        orientation {{ x: 0 y: 0 z: 0 w: 1 }} }} '
        f'allow_renaming: false'
    )
    result = subprocess.run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD}/create",
            "--reqtype", "gz.msgs.EntityFactory",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "2000",
            "--req", req,
        ],
        capture_output=True, text=True,
    )
    ok = "data: true" in (result.stdout or "")
    return ok, ((result.stdout or "") + ("\n--- stderr ---\n" + result.stderr if result.stderr else "")).strip()


def remove_model(name: str) -> Tuple[bool, str]:
    req = f'name: "{_pb_str(name)}" type: MODEL'
    result = subprocess.run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD}/remove",
            "--reqtype", "gz.msgs.Entity",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "2000",
            "--req", req,
        ],
        capture_output=True, text=True,
    )
    return ("data: true" in (result.stdout or ""),
            (result.stdout or result.stderr or "").strip())


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
# Image conversion + frame cache.
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
# Park the scene.
# ---------------------------------------------------------------------------
def park_scene_to_defaults(cam_rpy) -> None:
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


def cleanup_all_overlays() -> None:
    """Best-effort removal of every overlay this script may have spawned."""
    remove_model(MAT_MODEL_NAME)
    for _slug, model_name, _xyz, _r, _l in WRAPS:
        remove_model(model_name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames", type=int, default=5)
    p.add_argument("--dwell", type=float, default=2.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=DEFAULT_SAVE_DIR)
    p.add_argument("--no-overlay", dest="overlay", action="store_false")
    p.set_defaults(overlay=True)
    args = p.parse_args()

    save_dir = args.out.resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    classes_path = write_classes_file(save_dir)
    overlay_dir: Optional[Path] = None
    if args.overlay:
        overlay_dir = save_dir / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)
    log_path = save_dir / "materials.jsonl"
    log_path.write_text("")

    cam_rpy = look_at(CAMERA_POSITION, LOOK_AT_TARGET)

    print(f"gz-transport Python: {GZ_LABEL}")
    print(f"subscribing to       {CAMERA_TOPIC}")
    print(f"saving PNGs to       {save_dir}/")
    print(f"image intrinsics     {IMG_W}x{IMG_H}  hfov={math.degrees(HFOV_RAD):.0f}deg")
    print(f"camera (fixed)       pos={CAMERA_POSITION}  aim={LOOK_AT_TARGET}")
    print(f"bench mat            {MAT_SIZE_X}x{MAT_SIZE_Y} m at z={MAT_Z}  "
          f"({MAT_THICKNESS*1000:.1f} mm thick)  name='{MAT_MODEL_NAME}'")
    for slug, model_name, xyz, radius, length in WRAPS:
        wrap_r = radius + WRAP_RADIUS_MARGIN_M
        print(f"object wrap          {slug:>14s} -> r={wrap_r*1000:.1f} mm, "
              f"len={length*1000:.0f} mm at ({xyz[0]:+.3f}, {xyz[1]:+.3f}, {xyz[2]:+.3f}) "
              f"name='{model_name}'")
    print(f"random seed          {args.seed}  "
          f"(sat={SAT_RANGE}, val={VAL_RANGE}, hue=full)")
    if overlay_dir is not None:
        print(f"bbox overlays to     {overlay_dir}/  (disable with --no-overlay)")
    else:
        print("bbox overlays        OFF (--no-overlay was passed)")
    print()

    node = GzNode()
    cache = FrameCache()
    if not node.subscribe(GzImage, CAMERA_TOPIC, cache.on_image):
        sys.exit(f"ERROR: subscribe({CAMERA_TOPIC}) returned False.")

    print("parking camera + objects at SDF defaults ...")
    park_scene_to_defaults(cam_rpy)

    # Best-effort: remove any overlays a previous interrupted run left.
    cleanup_all_overlays()

    print("\nwaiting for the first frame ...")
    sub_started_at = time.time()
    if not wait_for_first_frame(cache, timeout_s=5.0):
        print("WARNING: no frame in 5 s.")
    else:
        print(f"first frame received after "
              f"{(cache.first_seen_at or sub_started_at) - sub_started_at:.1f} s")

    rng = random.Random(args.seed)
    saved = 0
    for frame_idx in range(args.frames):
        # Pick one random colour for each of the N_ELEMENTS surfaces.
        # Order: [bench, solvent_bottle, beaker_1, beaker_2, beaker_3].
        colours = [random_colour(rng) for _ in range(N_ELEMENTS)]
        bench_rgb = colours[0]
        wrap_rgbs = colours[1:]

        print(f"\n[frame {frame_idx:02d}]")
        print(f"  bench   rgb=({bench_rgb[0]:.2f},{bench_rgb[1]:.2f},{bench_rgb[2]:.2f})")

        # Clear any previous-frame overlays before spawning the new set.
        cleanup_all_overlays()
        time.sleep(0.2)  # let /remove propagate

        # Spawn the bench mat.
        bench_sdf = build_bench_mat_sdf(MAT_MODEL_NAME, bench_rgb)
        ok, reply = spawn_model(MAT_MODEL_NAME, bench_sdf, MAT_X, MAT_Y, MAT_Z)
        if not ok:
            print(f"  spawn bench FAIL — reply:")
            for line in reply.splitlines():
                print(f"    {line}")
            continue

        # Spawn one wrap per labelled object.
        spawned: List[Tuple[str, dict]] = []
        spawn_failure = False
        for (slug, model_name, (x, y, z), radius, length), rgb in zip(WRAPS, wrap_rgbs):
            wrap_r = radius + WRAP_RADIUS_MARGIN_M
            wrap_sdf = build_wrap_sdf(model_name, wrap_r, length, rgb)
            ok, reply = spawn_model(model_name, wrap_sdf, x, y, z)
            print(f"  wrap   {slug:>14s} rgb=({rgb[0]:.2f},{rgb[1]:.2f},{rgb[2]:.2f}) "
                  f"-> {'OK' if ok else 'FAIL'}")
            if not ok:
                for line in reply.splitlines():
                    print(f"      {line}")
                spawn_failure = True
                break
            spawned.append((model_name, {
                "slug": slug, "x": x, "y": y, "z": z,
                "radius_m": wrap_r, "length_m": length,
                "color_rgb": list(rgb),
            }))

        if spawn_failure:
            cleanup_all_overlays()
            continue

        time.sleep(args.dwell)
        if cache.latest is None:
            print("  no image received — is the topic publishing?")
            cleanup_all_overlays()
            continue

        img_path = save_dir / f"frame_{frame_idx:02d}.png"
        txt_path = img_path.with_suffix(".txt")
        msg_to_png(cache.latest, img_path)
        n_boxes = write_yolo_labels(txt_path, CAMERA_POSITION, cam_rpy)
        extra = ""
        if overlay_dir is not None:
            ov = overlay_dir / f"{img_path.stem}_bbox.png"
            drew = save_overlay(cache.latest, ov, CAMERA_POSITION, cam_rpy)
            extra = f"  overlay={drew} -> overlays/{ov.name}"

        with log_path.open("a") as fh:
            fh.write(json.dumps({
                "frame": frame_idx,
                "image": img_path.name,
                "bench": {
                    "model_name": MAT_MODEL_NAME,
                    "rgb": list(bench_rgb),
                    "size": [MAT_SIZE_X, MAT_SIZE_Y, MAT_THICKNESS],
                    "centre": [MAT_X, MAT_Y, MAT_Z],
                },
                "wraps": [info for _, info in spawned],
            }) + "\n")

        saved += 1
        print(f"  -> {img_path.resolve()}  ({cache.latest.width}x{cache.latest.height})  "
              f"labels={n_boxes} -> {txt_path.name}{extra}")

    # Final cleanup so the world is back to its SDF-default appearance.
    cleanup_all_overlays()

    print()
    print(f"done. saved {saved} PNGs -> {save_dir}/")
    print(f"      per-frame materials -> {log_path}")


if __name__ == "__main__":
    main()
