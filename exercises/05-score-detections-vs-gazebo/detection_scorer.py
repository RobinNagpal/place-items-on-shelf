"""Score YOLO detections against Gazebo ground truth — exercise 5.

This is the only new piece on top of exercise 04. Run exercise 04's
launch as-is, then run this script in a second terminal:

    python3 detection_scorer.py

What it does, in one paragraph:

1. Listens on `/yolo/detections` for the same Detection2DArray
   exercise 04 already publishes.
2. Listens on `/gazebo/pose_info` (a tf2_msgs/TFMessage bridged from
   the Gazebo Transport topic `/world/autosampler_cell/pose/info`)
   for the **true 3D pose of every model in the scene** — vials
   included.
3. For each tracked vial, projects its true `(X, Y, Z)` through a
   pinhole model into a 2D pixel bounding box (the **ground truth**
   we wish YOLO had drawn).
4. Compares ground-truth boxes to YOLO predictions with IoU.
5. Keeps a running tally — TP, FP, FN, mean IoU — and prints it
   every second.

There is **no manual labelling anywhere**. Gazebo already knows
where every model is.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
from vision_msgs.msg import Detection2DArray


# ---------------------------------------------------------------------------
# Camera setup — matches worlds/autosampler_cell_with_camera.sdf from ex 04.
# Change these constants if you move the camera.
# ---------------------------------------------------------------------------
CAM_X, CAM_Y, CAM_Z = 0.05, 0.00, 1.30      # world position (metres)
IMG_W, IMG_H = 640, 480
HFOV = 1.0472                                # 60 deg

# Pinhole intrinsics derived from the FOV.
# fx = (W/2) / tan(HFOV/2). Square pixels -> fy = fx.
FX = (IMG_W / 2) / math.tan(HFOV / 2)
FY = FX
CX_PX, CY_PX = IMG_W / 2, IMG_H / 2

# Models we care about. Names must match <model name="..."> in the SDF.
# Each entry is the YOLO class id we expect for that model.
TRACKED_MODELS: Dict[str, str] = {
    "vial_a1": "vial",      # red cap — also publishes cap_red detections, ignored for now
    "vial_a3": "vial",      # blue cap
    "vial_a5": "vial",      # green cap
}

# Constant-size GT bbox in pixels for an upright 12x32 mm vial seen
# top-down from ~0.475 m away. Derived once:
#   pixel_per_metre at depth d = FX / d  ≈ 1166
#   vial diameter = 12 mm -> ~14 px wide
#   vial height (projected outline of cap+body) -> ~14 px tall too
# At true top-down view the projection of an upright cylinder is a
# disc, so width ≈ height. We bake this in as a constant rather than
# re-projecting both ends of the cylinder every frame.
GT_BBOX_PX = (14.0, 14.0)


# ---------------------------------------------------------------------------
# Maths helpers
# ---------------------------------------------------------------------------
def project_to_pixel(xw: float, yw: float, zw: float) -> Tuple[float, float]:
    """World point -> image pixel for our specific straight-down camera.

    The camera in the SDF sits at (CAM_X, CAM_Y, CAM_Z) with pitch +90 deg,
    so it looks down the world -Z axis. With that orientation:

        right in image (+u) ↔ +Y in world
        down in image  (+v) ↔ +X in world

    Pinhole projection then simplifies to:

        u = cx + fx * (Yw - CAM_Y) / depth
        v = cy + fy * (Xw - CAM_X) / depth
        with depth = CAM_Z - Zw
    """
    depth = CAM_Z - zw
    if depth <= 1e-3:
        return (-1.0, -1.0)         # behind / above the camera
    u = CX_PX + FX * (yw - CAM_Y) / depth
    v = CY_PX + FY * (xw - CAM_X) / depth
    return u, v


def iou_xywh(a: Tuple[float, float, float, float],
             b: Tuple[float, float, float, float]) -> float:
    """IoU between two axis-aligned boxes in (cx, cy, w, h) pixel form."""
    ax1, ay1 = a[0] - a[2] / 2, a[1] - a[3] / 2
    ax2, ay2 = a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1 = b[0] - b[2] / 2, b[1] - b[3] / 2
    bx2, by2 = b[0] + b[2] / 2, b[1] + b[3] / 2

    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Running tally
# ---------------------------------------------------------------------------
@dataclass
class RunningStats:
    """Cumulative counts since the node started."""
    tp: int = 0          # IoU >= 0.5 with a ground-truth vial
    fp: int = 0          # YOLO detection that did not match any GT
    fn: int = 0          # GT vial that YOLO did not find
    iou_sum: float = 0.0
    iou_n: int = 0
    frames: int = 0
    per_class: Dict[str, int] = field(default_factory=dict)

    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    def mean_iou(self) -> float:
        return self.iou_sum / self.iou_n if self.iou_n else 0.0


# ---------------------------------------------------------------------------
# The node itself
# ---------------------------------------------------------------------------
class DetectionScorer(Node):

    def __init__(self) -> None:
        super().__init__("detection_scorer")
        self._stats = RunningStats()
        self._gt_world: Dict[str, Tuple[float, float, float]] = {}
        self._latest_dets: List[Tuple[str, Tuple[float, float, float, float]]] = []

        # Gazebo bridges its pose topic to a tf2 message. Each transform's
        # child_frame_id is the model name; we filter for TRACKED_MODELS.
        self.create_subscription(TFMessage, "/gazebo/pose_info",
                                 self._on_poses, 10)
        self.create_subscription(Detection2DArray, "/yolo/detections",
                                 self._on_detections, 10)
        # Score and print at 1 Hz — much cheaper than scoring per frame.
        self.create_timer(1.0, self._score_tick)

        self.get_logger().info(
            "scoring /yolo/detections vs /gazebo/pose_info for "
            f"{list(TRACKED_MODELS.keys())}"
        )

    # ------------------------------------------------------------------ subs
    def _on_poses(self, msg: TFMessage) -> None:
        for t in msg.transforms:
            name = t.child_frame_id
            if name in TRACKED_MODELS:
                p = t.transform.translation
                self._gt_world[name] = (p.x, p.y, p.z)

    def _on_detections(self, msg: Detection2DArray) -> None:
        latest: List[Tuple[str, Tuple[float, float, float, float]]] = []
        for det in msg.detections:
            if not det.results:
                continue
            cls = det.results[0].hypothesis.class_id
            b = det.bbox
            latest.append((cls, (b.center.position.x, b.center.position.y,
                                 b.size_x, b.size_y)))
        self._latest_dets = latest

    # ------------------------------------------------------------------ tick
    def _score_tick(self) -> None:
        """Match every ground-truth vial to a YOLO detection. Update stats."""
        self._stats.frames += 1

        # Filter detections by class once.
        yolo_vials = [box for cls, box in self._latest_dets if cls == "vial"]
        gt_used: List[int] = []                       # indices of matched YOLO boxes

        # 1. Walk every tracked GT pose. Project; find best-IoU YOLO match.
        for name, xyz in self._gt_world.items():
            u, v = project_to_pixel(*xyz)
            if u < 0:
                continue                              # outside the frustum
            gt_box = (u, v, GT_BBOX_PX[0], GT_BBOX_PX[1])

            best_i, best_iou = -1, 0.0
            for i, det_box in enumerate(yolo_vials):
                if i in gt_used:
                    continue
                score = iou_xywh(gt_box, det_box)
                if score > best_iou:
                    best_iou, best_i = score, i

            if best_iou >= 0.5:
                self._stats.tp += 1
                gt_used.append(best_i)
            else:
                self._stats.fn += 1
            self._stats.iou_sum += best_iou
            self._stats.iou_n += 1

        # 2. Unmatched YOLO detections are false positives.
        self._stats.fp += max(0, len(yolo_vials) - len(gt_used))

        s = self._stats
        self.get_logger().info(
            f"[t={s.frames:>4}s] "
            f"TP={s.tp} FP={s.fp} FN={s.fn}  "
            f"P={s.precision():.2f} R={s.recall():.2f}  "
            f"meanIoU={s.mean_iou():.2f}"
        )

    # On shutdown, print the final summary so it does not scroll past.
    def destroy_node(self) -> bool:
        s = self._stats
        self.get_logger().info(
            "\n=== final score ==="
            f"\nframes scored: {s.frames}"
            f"\nTP={s.tp}  FP={s.fp}  FN={s.fn}"
            f"\nprecision={s.precision():.3f}  recall={s.recall():.3f}"
            f"\nmean IoU on matched pairs={s.mean_iou():.3f}"
        )
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = DetectionScorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
