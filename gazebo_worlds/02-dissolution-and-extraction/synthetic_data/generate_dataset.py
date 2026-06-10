#!/usr/bin/env python3
"""Generate a small RGB + YOLO-box dataset from the Step 2 world.

What this script does, in one paragraph:

1. Subscribes to `/overhead_camera/image_raw` — the camera frames
   that the Gazebo SDF publishes, bridged into ROS 2 by
   `ros_gz_bridge`.
2. Subscribes to `/world/ketchup_extraction_cell/pose/info` — the
   true 3D pose of every model in the scene, also bridged in.
3. Every <save-period> seconds, takes the latest image, projects
   every tracked model's 3D bounding box into the image with a
   pinhole-camera model, writes:
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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from tf2_msgs.msg import TFMessage


# ---------------------------------------------------------------------------
# Camera config — MUST match the <sensor type="camera"> tag in
# `ketchup_extraction.sdf`. If you move or resize the camera there,
# update these constants too or the projected boxes will not line up
# with the pixels.
# ---------------------------------------------------------------------------
CAM_X, CAM_Y, CAM_Z = 0.0, 0.0, 1.5     # world position (metres)
IMG_W, IMG_H = 640, 480                  # pixels
HFOV = 1.0472                            # 60 deg in radians

# Pinhole intrinsics derived from the FOV.
# fx = (W / 2) / tan(HFOV / 2). Square pixels -> fy = fx.
FX = (IMG_W / 2) / math.tan(HFOV / 2)
FY = FX
CX_PX, CY_PX = IMG_W / 2, IMG_H / 2


# ---------------------------------------------------------------------------
# Which models to label, and how big they are.
#
# half_extents = (half_x, half_y, half_z) of an axis-aligned box around
# the model's pose, in metres. The numbers below come straight from the
# README of the world (Pyrex 100 mL beaker = Ø50 x 70 mm, Schott 500 mL
# bottle body + cap = Ø85 x 175 mm overall).
#
# Names MUST match the <model name="..."> values in the SDF.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TrackedObject:
    class_id: int
    half_extents: Tuple[float, float, float]


TRACKED: Dict[str, TrackedObject] = {
    "solvent_bottle": TrackedObject(class_id=0, half_extents=(0.0425, 0.0425, 0.0875)),
    "beaker_1":       TrackedObject(class_id=1, half_extents=(0.025, 0.025, 0.035)),
    "beaker_2":       TrackedObject(class_id=1, half_extents=(0.025, 0.025, 0.035)),
    "beaker_3":       TrackedObject(class_id=1, half_extents=(0.025, 0.025, 0.035)),
}


# ---------------------------------------------------------------------------
# Pinhole projection
# ---------------------------------------------------------------------------
def project_point(xw: float, yw: float, zw: float) -> Tuple[float, float]:
    """World point -> image pixel for the straight-down overhead camera.

    The camera sits at (CAM_X, CAM_Y, CAM_Z) with pitch = +pi/2, so its
    optical axis points along world -Z. With that orientation:

        right in image (+u)  <->  +Y in world
        down  in image (+v)  <->  +X in world

    The pinhole projection then simplifies to:

        u = cx + fx * (Yw - CAM_Y) / depth
        v = cy + fy * (Xw - CAM_X) / depth
        depth = CAM_Z - Zw
    """
    depth = CAM_Z - zw
    if depth <= 1e-3:
        # Behind / above the camera. Treat as invisible.
        return -1.0, -1.0
    u = CX_PX + FX * (yw - CAM_Y) / depth
    v = CY_PX + FY * (xw - CAM_X) / depth
    return u, v


def project_box(
    pose: Tuple[float, float, float],
    half: Tuple[float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    """Project all 8 corners of a box and return the enclosing pixel rect.

    Returns (u_min, v_min, u_max, v_max), clipped to the image, or None
    if the projection is entirely off-frame.
    """
    cx, cy, cz = pose
    hx, hy, hz = half
    us: List[float] = []
    vs: List[float] = []
    for sx in (-1, +1):
        for sy in (-1, +1):
            for sz in (-1, +1):
                u, v = project_point(cx + sx * hx, cy + sy * hy, cz + sz * hz)
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
# The ROS 2 node
# ---------------------------------------------------------------------------
class DatasetGenerator(Node):

    def __init__(self, out_dir: Path, save_period_s: float, num_frames: int) -> None:
        super().__init__("synthetic_dataset_generator")

        self._bridge = CvBridge()
        self._latest_image = None
        self._latest_poses: Dict[str, Tuple[float, float, float]] = {}
        self._frame_idx = 0
        self._num_frames = num_frames

        self._images_dir = out_dir / "images"
        self._labels_dir = out_dir / "labels"
        self._images_dir.mkdir(parents=True, exist_ok=True)
        self._labels_dir.mkdir(parents=True, exist_ok=True)

        self.create_subscription(
            Image, "/overhead_camera/image_raw", self._on_image, 10
        )
        self.create_subscription(
            TFMessage,
            "/world/ketchup_extraction_cell/pose/info",
            self._on_poses,
            10,
        )

        self.create_timer(save_period_s, self._save_tick)

        self.get_logger().info(
            f"saving (image, label) pairs every {save_period_s}s to "
            f"{out_dir} — target {num_frames} frames. Press Ctrl+C to stop."
        )

    def _on_image(self, msg: Image) -> None:
        # bgr8 keeps it ready for cv2.imwrite without a colour swap.
        self._latest_image = self._bridge.imgmsg_to_cv2(msg, "bgr8")

    def _on_poses(self, msg: TFMessage) -> None:
        for t in msg.transforms:
            name = t.child_frame_id
            if name in TRACKED:
                p = t.transform.translation
                self._latest_poses[name] = (p.x, p.y, p.z)

    def _save_tick(self) -> None:
        if self._frame_idx >= self._num_frames:
            self.get_logger().info("done — shutting down")
            rclpy.shutdown()
            return

        if self._latest_image is None or not self._latest_poses:
            self.get_logger().info(
                "waiting for first image / poses — is the bridge running "
                "and is gz sim playing?"
            )
            return

        stem = f"frame_{self._frame_idx:04d}"
        img_path = self._images_dir / f"{stem}.jpg"
        lbl_path = self._labels_dir / f"{stem}.txt"

        cv2.imwrite(str(img_path), self._latest_image)

        lines: List[str] = []
        for name, obj in TRACKED.items():
            pose = self._latest_poses.get(name)
            if pose is None:
                continue
            box_px = project_box(pose, obj.half_extents)
            if box_px is None:
                continue
            cx, cy, w, h = to_yolo(box_px)
            lines.append(f"{obj.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

        lbl_path.write_text("\n".join(lines) + ("\n" if lines else ""))

        self.get_logger().info(
            f"[{self._frame_idx + 1}/{self._num_frames}] wrote {stem}.jpg "
            f"+ {len(lines)} boxes"
        )
        self._frame_idx += 1


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
    args = parser.parse_args()

    rclpy.init()
    node = DatasetGenerator(args.out, args.save_period, args.num_frames)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
