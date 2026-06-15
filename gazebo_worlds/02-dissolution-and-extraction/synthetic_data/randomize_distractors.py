#!/usr/bin/env python3
"""Spawn random distractor objects + save the camera frames as PNGs + YOLO labels.

This is the **fifth** of the six domain-randomisation axes from
``docs/synthetic-data/features/01-detection-images-and-masks.md``.
``move_camera.py``, ``randomize_objects.py`` and ``randomize_lighting.py``
cover axes #1, #2 and #3. This script implements axis #5
(distractor objects): the camera, every labelled object AND the
sun light all stay fixed; what changes per frame is the set of
**unlabelled clutter** dropped around the bench (a pen, a tape
roll, a marker cap, a notebook, a marker pen).

The point is to teach a future detector that "a cylinder on the
bench" is not automatically a beaker — it has to actually look like
a beaker. The distractors are NEVER added to the YOLO labels; the
labelled-object .txt content is identical across all 5 frames.

What this does, end to end:

  1. Subscribes to /overhead_camera/image_raw via gz-transport.
  2. Parks the camera + every labelled object at the SDF defaults.
  3. For each of N (default 5) frames:
       a. Picks ``--n-distractors`` (default 2-4) distractor types
          from ``DISTRACTOR_TYPES`` with the seeded RNG.
       b. For each, draws a random (x, y) on the bench and rejects
          the sample if it would touch (within
          ``SAFETY_MARGIN_M``) any labelled object or any earlier
          distractor in the same frame.
       c. Spawns each accepted distractor via
          /world/<world>/create  (gz.msgs.EntityFactory).
       d. Waits ``--dwell`` seconds, captures the frame, writes
          frame_NN.png + frame_NN.txt + overlays/frame_NN_bbox.png.
       e. Removes each spawned distractor via
          /world/<world>/remove  (gz.msgs.Entity, type=MODEL).
  4. Writes captured_frames/distractors.jsonl — one JSON line per
     frame recording which distractors landed where. Reproducible
     from disk alone.

NO ROS. NO ros_gz_bridge.

Prerequisites — same as the sibling scripts.

Run order:

  Terminal 1:  gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
  Terminal 2:  python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_distractors.py

Common flags:

  --frames N         number of randomised frames (default 5)
  --n-distractors LO HI  how many distractors per frame (default 2 4)
  --dwell S          seconds to wait after spawning (default 2)
  --seed K           RNG seed (default 0)
  --out PATH         output folder (default ./captured_frames)
  --no-overlay       skip the bbox overlay PNGs
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
# gz-transport / gz-msgs Python bindings (same fallback ladder).
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
            "ERROR: numpy and Pillow are required.\n"
            f"  last import error: {e}\n"
            "  fix:  sudo apt install python3-numpy python3-pil\n"
        )


GzNode, GzImage, GZ_LABEL = _import_gz_bindings()
np, PILImage, PILImageDraw = _import_image_libs()


# ---------------------------------------------------------------------------
# Fixed camera + labelled objects (must match the SDF defaults so the
# YOLO labels we emit don't drift).
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
# Distractor catalogue.
#
# Each entry is a small, plausible piece of lab clutter — a pen, a
# marker, a roll of tape, a notebook, a stray cap. Geometry is just
# a single cylinder or box visual; physics is disabled
# (<static>true</static>) so the spawn position is exactly where we
# want it without waiting for things to settle.
#
# ``footprint_r`` is the *plan-view* radius (or half-diagonal for the
# box) used by the collision-free placement check. Add SAFETY_MARGIN_M
# on top to guarantee a visible gap to the labelled objects.
#
# z_offset: where the bottom of the object sits relative to the bench
# top (0.900 m). For a cylinder of length L lying upright, z_offset =
# L/2 so the bottom is on the bench. For a flat object (notebook), the
# z_offset is half its thickness.
# ---------------------------------------------------------------------------
DistractorType = Tuple[str, str, str, float, float, Tuple[float, float, float]]
DISTRACTOR_TYPES: List[DistractorType] = [
    # (slug, kind, geometry_block, footprint_r, z_offset, color_rgb)
    ("pen",      "cyl",  "<cylinder><radius>0.006</radius><length>0.140</length></cylinder>",
        0.006, 0.070, (0.20, 0.20, 0.65)),
    ("marker",   "cyl",  "<cylinder><radius>0.009</radius><length>0.130</length></cylinder>",
        0.009, 0.065, (0.05, 0.05, 0.05)),
    ("tape",     "cyl",  "<cylinder><radius>0.035</radius><length>0.025</length></cylinder>",
        0.035, 0.0125, (0.85, 0.75, 0.30)),
    ("cap",      "cyl",  "<cylinder><radius>0.018</radius><length>0.018</length></cylinder>",
        0.018, 0.009, (0.85, 0.10, 0.10)),
    ("notebook", "box",  "<box><size>0.110 0.080 0.012</size></box>",
        0.068, 0.006, (0.30, 0.55, 0.30)),
    ("clip",     "box",  "<box><size>0.045 0.025 0.010</size></box>",
        0.026, 0.005, (0.75, 0.75, 0.75)),
]

# Bench top surface and usable area (avoiding the legs).
BENCH_TOP_Z = 0.900
BENCH_X_RANGE = (-0.20, 0.20)
BENCH_Y_RANGE = (-0.40, 0.40)

# Minimum gap between any two object footprints (labelled or distractor).
SAFETY_MARGIN_M = 0.015  # 1.5 cm visible gap


# ---------------------------------------------------------------------------
# Math helpers (same as the sibling scripts).
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
# Distractor placement
# ---------------------------------------------------------------------------
def labelled_object_footprints() -> List[Tuple[float, float, float]]:
    """Return (x, y, footprint_radius) for every labelled object.

    Footprint radius is the larger of the object's x/y half-extents
    so a circular keep-out around it strictly contains its AABB.
    """
    out = []
    for _cid, _name, _model, (x, y, _z, _yaw), (hx, hy, _hz) in LABELLED_OBJECTS:
        out.append((x, y, max(hx, hy)))
    return out


def try_place_distractor(
    rng: random.Random,
    footprint_r: float,
    keep_out: List[Tuple[float, float, float]],
    attempts: int = 200,
) -> Optional[Tuple[float, float]]:
    """Reject-sample a (x, y) on the bench that doesn't touch anything in ``keep_out``.

    Each entry of ``keep_out`` is (cx, cy, radius). A candidate is
    accepted if its distance to every keep_out centre exceeds
    candidate_r + keep_out_r + SAFETY_MARGIN_M.
    """
    for _ in range(attempts):
        cx = rng.uniform(*BENCH_X_RANGE)
        cy = rng.uniform(*BENCH_Y_RANGE)
        ok = True
        for ox, oy, orad in keep_out:
            if math.hypot(cx - ox, cy - oy) < footprint_r + orad + SAFETY_MARGIN_M:
                ok = False
                break
        if ok:
            return (cx, cy)
    return None


# ---------------------------------------------------------------------------
# gz service: create + remove
# ---------------------------------------------------------------------------
def _pb_str(s: str) -> str:
    """Escape for protobuf text-format string literal (C-style escapes)."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def build_distractor_sdf(name: str, kind: str, geometry_block: str,
                         color_rgb: Tuple[float, float, float]) -> str:
    """Build a tiny, static SDF model that wraps one visual + one collision.

    Static so it never falls or jitters away from the spawn pose;
    the collision is kept so the bench doesn't render through the
    distractor in Gazebo's pick-and-place visuals later.

    Uses single quotes throughout the XML so the protobuf
    text-format escape only has to handle backslashes + newlines.
    """
    r = color_rgb
    return (
        "<?xml version='1.0'?>"
        "<sdf version='1.10'>"
        f"<model name='{name}'>"
        f"  <static>true</static>"
        f"  <link name='link'>"
        f"    <visual name='v'>"
        f"      <geometry>{geometry_block}</geometry>"
        f"      <material>"
        f"        <ambient>{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} 1</ambient>"
        f"        <diffuse>{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} 1</diffuse>"
        f"      </material>"
        f"    </visual>"
        f"    <collision name='c'>"
        f"      <geometry>{geometry_block}</geometry>"
        f"    </collision>"
        f"  </link>"
        f"</model>"
        "</sdf>"
    )


def spawn_model(name: str, sdf_xml: str, x: float, y: float, z: float) -> Tuple[bool, str]:
    """Call /world/<world>/create with a fully-formed EntityFactory request.

    NOTE: model names starting with `__` are reserved by gz-sim. If
    you try to spawn one, the service writes
    "Error Code 3: ... is reserved" to gz sim's *server* log and
    replies data: false to the client — so the failure is silent on
    our side. Pick a plain name (no leading double underscores).
    """
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
    reply = (result.stdout or "").strip()
    if result.stderr:
        reply = (reply + "\n--- stderr ---\n" + result.stderr.strip()).strip()
    return ok, reply


def remove_model(name: str) -> Tuple[bool, str]:
    """Call /world/<world>/remove with type=MODEL.

    Silently 'succeeds' if the named model doesn't exist on a given
    gz version. Other versions return data:false — we treat both as
    fine because the next-frame spawn would use a fresh name anyway.
    """
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
    ok = "data: true" in (result.stdout or "")
    return ok, (result.stdout or result.stderr or "").strip()


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
# Labels, classes, overlay (objects are static -> labels are static).
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
# Park camera + labelled objects (so the labels stay correct).
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


# ---------------------------------------------------------------------------
# Main capture loop
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames", type=int, default=5)
    p.add_argument("--n-distractors", nargs=2, type=int, default=[2, 4],
                   metavar=("LO", "HI"),
                   help="random integer in [LO, HI] inclusive (default: 2 4)")
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
    log_path = save_dir / "distractors.jsonl"
    log_path.write_text("")

    cam_rpy = look_at(CAMERA_POSITION, LOOK_AT_TARGET)

    print(f"gz-transport Python: {GZ_LABEL}")
    print(f"subscribing to       {CAMERA_TOPIC}")
    print(f"saving PNGs to       {save_dir}/")
    print(f"YOLO classes file    {classes_path}")
    print(f"image intrinsics     {IMG_W}x{IMG_H}  hfov={math.degrees(HFOV_RAD):.0f}deg")
    print(f"camera (fixed)       pos={CAMERA_POSITION}  aim={LOOK_AT_TARGET}")
    print(f"distractor catalog   {len(DISTRACTOR_TYPES)} entries: "
          f"{', '.join(t[0] for t in DISTRACTOR_TYPES)}")
    print(f"create service       /world/{WORLD}/create  remove: /world/{WORLD}/remove")
    print(f"random seed          {args.seed}  "
          f"n_distractors per frame in [{args.n_distractors[0]}, {args.n_distractors[1]}]")
    if overlay_dir is not None:
        print(f"bbox overlays to     {overlay_dir}/")
    print()

    node = GzNode()
    cache = FrameCache()
    if not node.subscribe(GzImage, CAMERA_TOPIC, cache.on_image):
        sys.exit(f"ERROR: subscribe({CAMERA_TOPIC}) returned False.")

    print("parking camera + objects at SDF defaults ...")
    park_scene_to_defaults(cam_rpy)

    # Best-effort: clean up any leftover distractors from a previous
    # interrupted run before we start spawning new ones.
    for i in range(20):
        remove_model(f"distractor_{i:02d}")

    print("\nwaiting for the first frame ...")
    sub_started_at = time.time()
    if not wait_for_first_frame(cache, timeout_s=5.0):
        print("WARNING: no frame in 5 s.")
    else:
        print(f"first frame received after "
              f"{(cache.first_seen_at or sub_started_at) - sub_started_at:.1f} s")

    rng = random.Random(args.seed)
    static_keep_out = labelled_object_footprints()
    lo, hi = args.n_distractors
    saved = 0

    for frame_idx in range(args.frames):
        n = rng.randint(lo, hi)
        types_this_frame = [rng.choice(DISTRACTOR_TYPES) for _ in range(n)]
        spawned: List[Tuple[str, dict]] = []
        keep_out = list(static_keep_out)
        print(f"\n[frame {frame_idx:02d}] target {n} distractor(s)")

        for d_idx, dtype in enumerate(types_this_frame):
            slug, kind, geom, footprint_r, z_off, color = dtype
            xy = try_place_distractor(rng, footprint_r, keep_out)
            if xy is None:
                print(f"  -> skipped #{d_idx} ({slug}): no free spot found in 200 tries")
                continue
            x, y = xy
            z = BENCH_TOP_Z + z_off
            name = f"distractor_{d_idx:02d}"
            sdf = build_distractor_sdf(name, kind, geom, color)
            ok, stdout = spawn_model(name, sdf, x, y, z)
            if not ok:
                # Print every line of the gz service reply (and stderr)
                # so we don't repeat the silent-fail debugging episode
                # caused by gz reserving names starting with '__'.
                print(f"  -> spawn FAIL #{d_idx} ({slug}) — gz service reply:")
                for line in (stdout or "(no reply text)").splitlines() or [stdout]:
                    print(f"       {line}")
                continue
            spawned.append((name, {
                "slug": slug, "x": x, "y": y, "z": z, "footprint_r": footprint_r,
                "color_rgb": list(color),
            }))
            # The next candidate has to avoid this one too.
            keep_out.append((x, y, footprint_r))
            print(f"  spawned {name} ({slug}) at ({x:+.3f}, {y:+.3f}, {z:+.3f})")

        time.sleep(args.dwell)
        if cache.latest is None:
            print("  no image received — is the topic publishing?")
            for name, _info in spawned:
                remove_model(name)
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
                "distractors": [info for _, info in spawned],
            }) + "\n")

        saved += 1
        print(f"  -> {img_path.resolve()}  ({cache.latest.width}x{cache.latest.height})  "
              f"labels={n_boxes} -> {txt_path.name}{extra}")

        # Remove every distractor we spawned so the next frame starts clean.
        for name, _info in spawned:
            remove_model(name)

    print()
    print(f"done. saved {saved} PNGs -> {save_dir}/")
    print(f"      per-frame distractor placements -> {log_path}")


if __name__ == "__main__":
    main()
