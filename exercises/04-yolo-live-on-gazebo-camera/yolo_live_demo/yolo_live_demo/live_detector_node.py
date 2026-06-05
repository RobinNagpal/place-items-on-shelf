"""Run a YOLOv8 .pt checkpoint on every Gazebo camera frame.

High-level workflow (the part beginners should remember):

    Gazebo camera  ->  sensor_msgs/Image  ->  this node  ->  vision_msgs/Detection2DArray
                                              also draws boxes  ->  sensor_msgs/Image (annotated)

The node never talks to Gazebo directly. It only knows about ROS 2
topics, which is what makes the same code work on a real camera
later (just point the subscription at a different topic).

Parameters (all overridable from the launch file):

  weights         path to the trained .pt checkpoint (e.g. exercise 3's best.pt)
  image_topic     ROS topic the camera publishes on
  detections_topic where to publish vision_msgs/Detection2DArray
  annotated_topic where to publish the image with boxes drawn on top
  conf_threshold  drop predictions below this confidence
  device          "cpu" or "0" (first GPU)
"""

from __future__ import annotations

from typing import List

import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    BoundingBox2D,
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)


class LiveDetectorNode(Node):
    """Subscribe to a camera, run YOLO, publish detections + overlay."""

    def __init__(self) -> None:
        super().__init__("yolo_live_detector")

        # --- Declare parameters with defaults --------------------------------
        # The launch file overrides these; the defaults make `ros2 run`
        # usable on its own too.
        self.declare_parameter("weights", "best.pt")
        self.declare_parameter("image_topic", "/overhead_camera/image_raw")
        self.declare_parameter("detections_topic", "/yolo/detections")
        self.declare_parameter("annotated_topic", "/yolo/image_annotated")
        self.declare_parameter("conf_threshold", 0.25)
        self.declare_parameter("device", "cpu")

        weights = self.get_parameter("weights").value
        image_topic = self.get_parameter("image_topic").value
        det_topic = self.get_parameter("detections_topic").value
        ann_topic = self.get_parameter("annotated_topic").value
        self._conf = float(self.get_parameter("conf_threshold").value)
        self._device = str(self.get_parameter("device").value)

        # --- Load the model ONCE on startup ----------------------------------
        # ultralytics is heavy — pulling it in inside the callback would
        # stutter every frame. We import here, after rclpy.init, so import
        # errors surface with a clean rclpy error.
        from ultralytics import YOLO

        self.get_logger().info(f"loading YOLO weights: {weights}")
        self._model = YOLO(weights)
        # `names` is {class_id: "class_name"} — used for both the
        # Detection2DArray hypothesis_id and the overlay text.
        self._names = self._model.names

        # cv_bridge converts between ROS Image messages and OpenCV/numpy.
        self._bridge = CvBridge()

        # --- ROS plumbing ----------------------------------------------------
        # qos_profile=10 = keep the last 10 messages. Camera frames are
        # cheap to drop; we always process the latest available frame.
        self._image_sub = self.create_subscription(
            Image, image_topic, self._on_image, 10
        )
        self._det_pub = self.create_publisher(Detection2DArray, det_topic, 10)
        self._ann_pub = self.create_publisher(Image, ann_topic, 10)

        self.get_logger().info(
            f"listening on {image_topic} -> publishing {det_topic} "
            f"and {ann_topic} (conf >= {self._conf}, device={self._device})"
        )

    # ---------------------------------------------------------------------
    # Per-frame callback
    # ---------------------------------------------------------------------
    def _on_image(self, msg: Image) -> None:
        """Called once per camera frame."""
        # Step 1 — ROS Image to a numpy BGR array (OpenCV's native layout).
        frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        # Step 2 — Run YOLO. `verbose=False` silences ultralytics' per-frame
        # console spam. `conf` filters low-confidence boxes for us.
        results = self._model.predict(
            source=frame,
            conf=self._conf,
            device=self._device,
            verbose=False,
        )

        # Step 3 — Build the ROS detections message from the YOLO result.
        det_array = self._build_detections_msg(results[0], header=msg.header)
        self._det_pub.publish(det_array)

        # Step 4 — Re-publish the frame with boxes drawn on top.
        # ultralytics' .plot() returns a numpy BGR image identical in
        # size to the input frame.
        annotated: np.ndarray = results[0].plot()
        ann_msg = self._bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
        ann_msg.header = msg.header   # keep the same timestamp + frame_id
        self._ann_pub.publish(ann_msg)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _build_detections_msg(
        self, result, header
    ) -> Detection2DArray:
        """Convert one ultralytics Result into vision_msgs/Detection2DArray.

        vision_msgs is the ROS 2 standard for detection / segmentation
        messages. Detection2D carries a 2D pixel bbox (centre + size) and
        a list of `ObjectHypothesisWithPose` (one entry per candidate
        class). YOLO emits one class per box, so each Detection2D gets a
        single hypothesis.
        """
        msg = Detection2DArray()
        msg.header = header  # match the camera frame's timestamp + frame_id

        boxes = result.boxes
        if boxes is None or boxes.cls is None:
            return msg

        # Vectorised numpy access — one tensor per field.
        cls_arr = boxes.cls.cpu().numpy().astype(int)
        conf_arr = boxes.conf.cpu().numpy().astype(float)
        xywh_arr = boxes.xywh.cpu().numpy()  # centre_x, centre_y, w, h

        det_list: List[Detection2D] = []
        for cls_id, conf, (cx, cy, w, h) in zip(cls_arr, conf_arr, xywh_arr):
            det = Detection2D()
            det.header = header

            bbox = BoundingBox2D()
            bbox.center.position.x = float(cx)
            bbox.center.position.y = float(cy)
            bbox.center.theta = 0.0       # YOLOv8 boxes are axis-aligned
            bbox.size_x = float(w)
            bbox.size_y = float(h)
            det.bbox = bbox

            hyp = ObjectHypothesisWithPose()
            # vision_msgs wants a string class id; convention is the name.
            hyp.hypothesis.class_id = self._names[int(cls_id)]
            hyp.hypothesis.score = float(conf)
            det.results.append(hyp)

            det_list.append(det)

        msg.detections = det_list
        return msg


def main() -> None:
    rclpy.init()
    node = LiveDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
