#!/usr/bin/env python3
"""Generate a small RGB + YOLO-box dataset from the Step 2 world.

What this script does, in one paragraph:

1. Subscribes to `/overhead_camera/image_raw` — the camera frames
   that the Gazebo SDF publishes, bridged into ROS 2 by
   `ros_gz_bridge`.
2. Subscribes to `/world/ketchup_extraction_cell/pose/info` — the
   true 3D pose of every model in the scene, also bridged in.
3. Every <save-period> seconds, OPTIONALLY teleports the tracked
   objects and the camera to small random offsets (so the dataset
   has real variety instead of 50 copies of the same picture),
   then takes the latest image, projects every tracked model's 3D
   bounding box into the image with a pinhole-camera model, and
   writes:
       images/frame_<N>.jpg          (the picture)
       labels/frame_<N>.txt          (one YOLO line per box)
4. Stops after <num-frames> saved pairs, or on Ctrl+C.

There is no manual labelling. Gazebo already knows where every
model is — that is the entire point of synthetic data.

YOLO line format (one per visible model):

    <class_id> <cx> <cy> <w> <h>

All four numbers are fractions of image width / height. Class ids:

    0 = solvent_bottle
    1 = beaker

Run order — see synthetic_data/README.md for the full WSL recipe.
"""

from __future__ import annotations

import argparse
import math
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from tf2_msgs.msg import TFMessage


WORLD_NAME = "ketchup_extraction_cell"

# ---------------------------------------------------------------------------
# Camera config — MUST match the <sensor type="camera"> tag in
# `ketchup_extraction.sdf`. If you move or resize the camera there,
# update these constants too or the projected boxes will not line up
# with the pixels.
#
# Only the image size and FOV are constants; the camera POSITION is
# tracked from Gazebo at runtime so --jitter can move the camera and
# the projection stays correct.
# ---------------------------------------------------------------------------
IMG_W, IMG_H = 640, 480                  # pixels
HFOV = 1.0472                            # 60 deg in radians
NOMINAL_CAM = (0.0, 0.0, 1.5)            # x, y, z; pitch always +pi/2

# Pinhole intrinsics derived from the FOV.
# fx = (W / 2) / tan(HFOV / 2). Square pixels -> fy = fx.
FX = (IMG_W / 2) / math.tan(HFOV / 2)
FY = FX
CX_PX, CY_PX = IMG_W / 2, IMG_H / 2


# ---------------------------------------------------------------------------
# Which models to label, how big they are, and where they nominally sit.
#
# half_extents = (half_x, half_y, half_z) of an axis-aligned box around
# the model's pose, in metres. The numbers below come straight from the
# README of the world (Pyrex 100 mL beaker = Ø50 x 70 mm, Schott 500 mL
# bottle body + cap = Ø85 x 175 mm overall).
#
# nominal = (x, y, z) world pose, taken from <model><pose> in the SDF.
#
# Names MUST match <model name="..."> in the SDF and the names that
# show up on /world/<...>/pose/info.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TrackedObject:
    class_id: int
    half_extents: Tuple[float, float, float]
    nominal: Tuple[float, float, float]


TRACKED: Dict[str, TrackedObject] = {
    "solvent_bottle": TrackedObject(
        class_id=0,
        half_extents=(0.0425, 0.0425, 0.0875),
        nominal=(0.10, 0.25, 0.975),
    ),
    "beaker_1": TrackedObject(
        class_id=1,
        half_extents=(0.025, 0.025, 0.035),
        nominal=(0.05, -0.30, 0.935),
    ),
    "beaker_2": TrackedObject(
        class_id=1,
        half_extents=(0.025, 0.025, 0.035),
        nominal=(0.05, -0.18, 0.935),
    ),
    "beaker_3": TrackedObject(
        class_id=1,
        half_extents=(0.025, 0.025, 0.035),
        nominal=(0.05, -0.06, 0.935),
    ),
}

# Jitter ranges per axis, applied symmetrically (uniform in [-r, +r]).
# Kept small so beakers do not fall off the bench or overlap.
OBJ_JITTER_XY = 0.02      # m  -> +-20 mm shuffle for each object
OBJ_JITTER_YAW = math.radians(20)    # rad -> +-20 deg yaw rotation
CAM_JITTER_XY = 0.05      # m  -> +-50 mm shuffle for the camera


# ---------------------------------------------------------------------------
# Pinhole projection
# ---------------------------------------------------------------------------
def project_point(xw: float, yw: float, zw: float,
                  cam_x: float, cam_y: float, cam_z: float) -> Tuple[float, float]:
    """World point -> image pixel for the straight-down overhead camera.

    The camera sits at (cam_x, cam_y, cam_z) with pitch = +pi/2, so its
    optical axis points along world -Z. With that orientation:

        right in image (+u)  <->  +Y in world
        down  in image (+v)  <->  +X in world

    The pinhole projection then simplifies to:

        u = cx + fx * (Yw - cam_y) / depth
        v = cy + fy * (Xw - cam_x) / depth
        depth = cam_z - Zw
    """
    depth = cam_z - zw
    if depth <= 1e-3:
        return -1.0, -1.0
    u = CX_PX + FX * (yw - cam_y) / depth
    v = CY_PX + FY * (xw - cam_x) / depth
    return u, v


def project_box(
    pose: Tuple[float, float, float],
    half: Tuple[float, float, float],
    cam: Tuple[float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    """Project all 8 corners of a box and return the enclosing pixel rect.

    Returns (u_min, v_min, u_max, v_max), clipped to the image, or None
    if the projection is entirely off-frame.
    """
    cx_, cy_, cz_ = pose
    hx, hy, hz = half
    us: List[float] = []
    vs: List[float] = []
    for sx in (-1, +1):
        for sy in (-1, +1):
            for sz in (-1, +1):
                u, v = project_point(
                    cx_ + sx * hx, cy_ + sy * hy, cz_ + sz * hz,
                    cam[0], cam[1], cam[2],
                )
                if u < 0:
                    continue
                us.append(u)
                vs.append(v)
    if not us:
        return None
    u_min = max(0.0, min(us))
    v_min = max(0.0, min(vs))
    u_max = min(float(IMG_W), max(us))
    v_max = min(float(IMG_H), max(vs))
    if u_max <= u_min or v_max <= v_min:
        return None
    return u_min, v_min, u_max, v_max


def to_yolo(box_px: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    """(u_min, v_min, u_max, v_max) pixels -> (cx, cy, w, h) normalised."""
    u_min, v_min, u_max, v_max = box_px
    cx = (u_min + u_max) / 2.0 / IMG_W
    cy = (v_min + v_max) / 2.0 / IMG_H
    w = (u_max - u_min) / IMG_W
    h = (v_max - v_min) / IMG_H
    return cx, cy, w, h


# ---------------------------------------------------------------------------
# Gazebo `set_pose` service call (used by --jitter mode)
# ---------------------------------------------------------------------------
def yaw_to_quat(yaw: float) -> Tuple[float, float, float, float]:
    """Yaw (Z rotation) -> (qx, qy, qz, qw)."""
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def pitch_to_quat(pitch: float) -> Tuple[float, float, float, float]:
    """Pitch (Y rotation) -> (qx, qy, qz, qw)."""
    return 0.0, math.sin(pitch / 2.0), 0.0, math.cos(pitch / 2.0)


def set_pose(model: str, x: float, y: float, z: float,
             qx: float = 0.0, qy: float = 0.0, qz: float = 0.0, qw: float = 1.0) -> bool:
    """Teleport `model` via `gz service /world/<W>/set_pose`.

    Returns True on success. Failures are logged but not raised so
    the loop keeps going if one entity is missing.
    """
    req = (
        f'name: "{model}" '
        f'position {{ x: {x} y: {y} z: {z} }} '
        f'orientation {{ x: {qx} y: {qy} z: {qz} w: {qw} }}'
    )
    result = subprocess.run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD_NAME}/set_pose",
            "--reqtype", "gz.msgs.Pose",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "500",
            "--req", req,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return "data: true" in (result.stdout or "")


# ---------------------------------------------------------------------------
# The ROS 2 node
# ---------------------------------------------------------------------------
class DatasetGenerator(Node):

    def __init__(self, out_dir: Path, save_period_s: float, num_frames: int,
                 jitter: bool, seed: int) -> None:
        super().__init__("synthetic_dataset_generator")

        self._bridge = CvBridge()
        self._latest_image = None
        self._latest_poses: Dict[str, Tuple[float, float, float]] = {}
        self._cam_pose: Tuple[float, float, float] = NOMINAL_CAM
        self._frame_idx = 0
        self._num_frames = num_frames
        self._jitter = jitter
        self._rng = random.Random(seed)
        self._image_msgs_seen = 0
        self._pose_msgs_seen = 0

        self._images_dir = out_dir / "images"
        self._labels_dir = out_dir / "labels"
        self._images_dir.mkdir(parents=True, exist_ok=True)
        self._labels_dir.mkdir(parents=True, exist_ok=True)

        # ros_gz_bridge publishes the camera with BEST_EFFORT QoS (sensor
        # data). A subscriber with the default RELIABLE QoS never matches
        # it, so callbacks never fire and the script just prints
        # "waiting for first image..." forever. qos_profile_sensor_data is
        # BEST_EFFORT and matches BEST_EFFORT or RELIABLE publishers, so it
        # is the safe choice for both topics.
        self.create_subscription(
            Image,
            "/overhead_camera/image_raw",
            self._on_image,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            TFMessage,
            f"/world/{WORLD_NAME}/pose/info",
            self._on_poses,
            qos_profile_sensor_data,
        )

        self.create_timer(save_period_s, self._save_tick)

        mode = "with jitter" if jitter else "static (no jitter)"
        self.get_logger().info(
            f"saving (image, label) pairs every {save_period_s}s to "
            f"{out_dir} — target {num_frames} frames, mode: {mode}. "
            f"Ctrl+C to stop."
        )

    # ------------------------------------------------------------------ subs
    def _on_image(self, msg: Image) -> None:
        # bgr8 keeps it ready for cv2.imwrite without a colour swap.
        self._latest_image = self._bridge.imgmsg_to_cv2(msg, "bgr8")
        self._image_msgs_seen += 1

    def _on_poses(self, msg: TFMessage) -> None:
        self._pose_msgs_seen += 1
        for t in msg.transforms:
            name = t.child_frame_id
            p = t.transform.translation
            if name in TRACKED:
                self._latest_poses[name] = (p.x, p.y, p.z)
            elif name == "overhead_camera":
                self._cam_pose = (p.x, p.y, p.z)

    # ------------------------------------------------------------------ tick
    def _save_tick(self) -> None:
        if self._frame_idx >= self._num_frames:
            self.get_logger().info("done — shutting down")
            rclpy.shutdown()
            return

        if self._latest_image is None or not self._latest_poses:
            img_status = (
                f"OK ({self._image_msgs_seen} msgs)"
                if self._latest_image is not None else
                f"MISSING (saw {self._image_msgs_seen} msgs)"
            )
            pose_status = (
                f"OK ({self._pose_msgs_seen} msgs, "
                f"{len(self._latest_poses)} tracked models)"
                if self._latest_poses else
                f"MISSING (saw {self._pose_msgs_seen} msgs)"
            )
            self.get_logger().info(
                f"waiting — image: {img_status}; poses: {pose_status}. "
                "If both say MISSING with 0 msgs, the script is not "
                "subscribing to the bridged topics (QoS mismatch, stale "
                "code, wrong topic names, or no ROS 2 sourced). See "
                "synthetic_data/README.md > Troubleshooting."
            )
            return

        # --- 1. jitter the scene if asked. ----------------------------------
        if self._jitter:
            self._randomise_scene()

        # --- 2. save the frame and labels. ----------------------------------
        stem = f"frame_{self._frame_idx:04d}"
        img_path = self._images_dir / f"{stem}.jpg"
        lbl_path = self._labels_dir / f"{stem}.txt"

        cv2.imwrite(str(img_path), self._latest_image)

        lines: List[str] = []
        for name, obj in TRACKED.items():
            pose = self._latest_poses.get(name)
            if pose is None:
                continue
            box_px = project_box(pose, obj.half_extents, self._cam_pose)
            if box_px is None:
                continue
            cx, cy, w, h = to_yolo(box_px)
            lines.append(f"{obj.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

        lbl_path.write_text("\n".join(lines) + ("\n" if lines else ""))

        self.get_logger().info(
            f"[{self._frame_idx + 1}/{self._num_frames}] wrote {stem}.jpg "
            f"+ {len(lines)} boxes (cam @ {self._cam_pose})"
        )
        self._frame_idx += 1

    # --------------------------------------------------------------- jitter
    def _randomise_scene(self) -> None:
        """Teleport every tracked object + the camera to a small random offset.

        Uses `gz service set_pose`. We sleep briefly afterwards so the
        new positions land on /pose/info and on the next camera frame
        before we capture.
        """
        # Each beaker / bottle: jitter XY around its nominal pose; rotate
        # around Z (yaw) so the labels and water-level visuals look
        # different. Z stays at nominal so nothing falls off the bench.
        for name, obj in TRACKED.items():
            nx, ny, nz = obj.nominal
            x = nx + self._rng.uniform(-OBJ_JITTER_XY, OBJ_JITTER_XY)
            y = ny + self._rng.uniform(-OBJ_JITTER_XY, OBJ_JITTER_XY)
            yaw = self._rng.uniform(-OBJ_JITTER_YAW, OBJ_JITTER_YAW)
            qx, qy, qz, qw = yaw_to_quat(yaw)
            set_pose(name, x, y, nz, qx, qy, qz, qw)

        # Camera: jitter XY only; keep z and the +pi/2 pitch so the
        # straight-down pinhole math stays correct.
        cx_, cy_, cz_ = NOMINAL_CAM
        cx_n = cx_ + self._rng.uniform(-CAM_JITTER_XY, CAM_JITTER_XY)
        cy_n = cy_ + self._rng.uniform(-CAM_JITTER_XY, CAM_JITTER_XY)
        qx, qy, qz, qw = pitch_to_quat(math.pi / 2.0)
        set_pose("overhead_camera", cx_n, cy_n, cz_, qx, qy, qz, qw)

        # Let physics + the pose-info topic catch up before we grab a frame.
        # 0.3 s is enough — beakers do not fall on this short shuffle.
        import time
        time.sleep(0.3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("./synthetic_dataset"),
        help="output folder; images/ and labels/ are created inside",
    )
    parser.add_argument(
        "--save-period",
        type=float,
        default=1.0,
        help="seconds between saved frames (default: 1.0)",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=50,
        help="stop after this many saved frames (default: 50)",
    )
    parser.add_argument(
        "--jitter",
        action="store_true",
        help="teleport objects + camera randomly before each save so the "
             "frames are not all identical (recommended for any real "
             "training set)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="RNG seed for --jitter; pick a different one to get a "
             "different dataset",
    )
    args = parser.parse_args()

    rclpy.init()
    node = DatasetGenerator(
        args.out, args.save_period, args.num_frames,
        args.jitter, args.seed,
    )
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
