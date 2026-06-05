"""Depth-camera point cloud -> 3D centroid per detected object.

Builds directly on exercise 07 (instance segmentation). All this node
does is the one extra step item 8 calls for:

    instance mask (2D)  +  depth image (per-pixel metres)
                              |
                              v
                    one 3D centroid per instance

It does NOT rerun YOLO, does NOT redraw the overlay, and does NOT
care about the bbox. It only consumes what exercise 07 already
publishes plus a depth image from a Gazebo depth camera.

Subscriptions:
    /yolo_seg/instance_mask     sensor_msgs/Image, mono8
                                pixel value = instance id (0 = bg)
    /yolo_seg/detections        vision_msgs/Detection2DArray
                                same length; result[i-1] has the class
                                for instance id i
    /overhead_camera/depth      sensor_msgs/Image, 32FC1 metres
                                Gazebo depth-camera plugin output

Publication:
    /objects/centroids          vision_msgs/Detection3DArray
                                one Detection3D per instance with
                                (X, Y, Z) in the camera frame, plus
                                the original class id and score.

Run after exercise 07 is already publishing:

    python3 centroid_node.py --ros-args -p depth_topic:=/overhead_camera/depth
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2DArray,
    Detection3D,
    Detection3DArray,
    ObjectHypothesisWithPose,
)


# ---------------------------------------------------------------------------
# Camera intrinsics — matches the SDF camera from exercise 04.
# Same constants as exercise 05's scorer. Change here if the SDF moves.
# ---------------------------------------------------------------------------
IMG_W, IMG_H = 640, 480
HFOV = 1.0472                                # 60 deg
FX = (IMG_W / 2) / math.tan(HFOV / 2)
FY = FX
CX_PX, CY_PX = IMG_W / 2.0, IMG_H / 2.0


def deproject(u: float, v: float, depth_m: float) -> Tuple[float, float, float]:
    """Pixel + depth -> 3D point in the camera frame.

    The inverse of the pinhole projection from exercise 05:
        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy
        Z = depth_m
    """
    z = depth_m
    x = (u - CX_PX) * z / FX
    y = (v - CY_PX) * z / FY
    return x, y, z


class CentroidNode(Node):

    def __init__(self) -> None:
        super().__init__("depth_centroid_node")

        self.declare_parameter("mask_topic", "/yolo_seg/instance_mask")
        self.declare_parameter("det_topic", "/yolo_seg/detections")
        self.declare_parameter("depth_topic", "/overhead_camera/depth")

        mask_topic = str(self.get_parameter("mask_topic").value)
        det_topic = str(self.get_parameter("det_topic").value)
        depth_topic = str(self.get_parameter("depth_topic").value)

        self._bridge = CvBridge()

        # Latest depth frame (32FC1 metres) and latest detection list.
        # We do not sync strictly — depth is steady; nearest-in-time is
        # fine for a stationary overhead camera.
        self._depth: Optional[np.ndarray] = None
        self._classes: Dict[int, Tuple[str, float]] = {}

        self.create_subscription(Image, depth_topic, self._on_depth, 10)
        self.create_subscription(
            Detection2DArray, det_topic, self._on_dets, 10
        )
        self.create_subscription(Image, mask_topic, self._on_mask, 10)

        self._pub = self.create_publisher(
            Detection3DArray, "/objects/centroids", 10
        )

        self.get_logger().info(
            f"depth<-{depth_topic}, mask<-{mask_topic}, det<-{det_topic}; "
            "publishing /objects/centroids"
        )

    # ------------------------------------------------------------------ subs
    def _on_depth(self, msg: Image) -> None:
        # Gazebo depth-camera plugin emits 32FC1 metres.
        self._depth = self._bridge.imgmsg_to_cv2(msg, desired_encoding="32FC1")

    def _on_dets(self, msg: Detection2DArray) -> None:
        # detections[i] describes instance id (i+1) — same ordering the
        # seg node used when painting the instance map.
        self._classes = {}
        for i, det in enumerate(msg.detections):
            if not det.results:
                continue
            r = det.results[0]
            self._classes[i + 1] = (r.hypothesis.class_id, float(r.hypothesis.score))

    def _on_mask(self, msg: Image) -> None:
        """Mask is the trigger — one published frame per incoming mask."""
        if self._depth is None:
            return

        instance_map = self._bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
        depth = self._depth
        if depth.shape != instance_map.shape:
            self.get_logger().warn(
                f"depth shape {depth.shape} != mask shape {instance_map.shape}; "
                "skipping frame"
            )
            return

        out = Detection3DArray()
        out.header = msg.header                  # camera frame
        out.detections = self._compute_centroids(instance_map, depth, msg.header)
        self._pub.publish(out)

    # ---------------------------------------------------------------- core
    def _compute_centroids(
        self,
        instance_map: np.ndarray,
        depth: np.ndarray,
        header,
    ) -> List[Detection3D]:
        results: List[Detection3D] = []

        ids = np.unique(instance_map)
        for iid in ids:
            if iid == 0:                          # background
                continue

            pixel_mask = instance_map == iid
            zs = depth[pixel_mask]

            # Drop invalid depth: NaN, Inf, or absurdly far (no return).
            zs = zs[np.isfinite(zs)]
            zs = zs[zs > 0.05]
            if zs.size < 10:                      # not enough good pixels
                continue

            # Median depth is far more robust than mean — rim pixels of a
            # vial cap can pick up table depth, dragging the mean down.
            z_med = float(np.median(zs))

            # Mask pixel centroid in image space, then deproject ONCE.
            # We don't bother averaging per-pixel 3D points; with the
            # median depth the result is the same to within sub-mm.
            ys, xs = np.where(pixel_mask)
            u = float(xs.mean())
            v = float(ys.mean())
            X, Y, Z = deproject(u, v, z_med)

            d = Detection3D()
            d.header = header
            d.bbox.center.position.x = X
            d.bbox.center.position.y = Y
            d.bbox.center.position.z = Z

            cls, score = self._classes.get(int(iid), (f"id_{int(iid)}", 0.0))
            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = cls
            hyp.hypothesis.score = score
            hyp.pose.pose.position.x = X
            hyp.pose.pose.position.y = Y
            hyp.pose.pose.position.z = Z
            d.results.append(hyp)
            results.append(d)

        return results


def main() -> None:
    rclpy.init()
    node = CentroidNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
