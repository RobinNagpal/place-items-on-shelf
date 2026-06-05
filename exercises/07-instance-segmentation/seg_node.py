"""Run YOLOv8-seg live on the Gazebo camera and publish pixel masks.

Same camera, same image topic, same Gazebo world as exercise 04.
The only thing that changes is the model: instead of YOLOv8-nano
(detection -> boxes) we load YOLOv8-nano-seg (segmentation ->
per-pixel masks).

Three topics come out:

    /yolo_seg/detections      vision_msgs/Detection2DArray
                              (bounding boxes — same shape as ex 04)

    /yolo_seg/instance_mask   sensor_msgs/Image, mono8
                              pixel value 0 = background, 1..N = instance id

    /yolo_seg/image_annotated sensor_msgs/Image, bgr8
                              the frame with translucent coloured masks on top
                              (built by ultralytics' .plot() for free)

Run after exercise 04's launch is already up:

    python3 seg_node.py --ros-args -p weights:=/abs/path/to/yolov8n-seg.pt
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


class SegNode(Node):

    def __init__(self) -> None:
        super().__init__("yolo_seg_node")

        # Parameters mirror the exercise 04 detector so launch files
        # can pass the same overrides.
        self.declare_parameter("weights", "yolov8n-seg.pt")
        self.declare_parameter("image_topic", "/overhead_camera/image_raw")
        self.declare_parameter("conf_threshold", 0.25)
        self.declare_parameter("device", "cpu")

        weights = self.get_parameter("weights").value
        image_topic = self.get_parameter("image_topic").value
        self._conf = float(self.get_parameter("conf_threshold").value)
        self._device = str(self.get_parameter("device").value)

        # Heavy import: only after rclpy.init so failures land cleanly.
        from ultralytics import YOLO

        self.get_logger().info(f"loading YOLOv8-seg weights: {weights}")
        self._model = YOLO(weights)
        self._names = self._model.names
        self._bridge = CvBridge()

        self.create_subscription(Image, image_topic, self._on_image, 10)
        self._det_pub = self.create_publisher(
            Detection2DArray, "/yolo_seg/detections", 10
        )
        self._mask_pub = self.create_publisher(
            Image, "/yolo_seg/instance_mask", 10
        )
        self._ann_pub = self.create_publisher(
            Image, "/yolo_seg/image_annotated", 10
        )

        self.get_logger().info(
            f"listening on {image_topic}; publishing /yolo_seg/detections, "
            "/yolo_seg/instance_mask, /yolo_seg/image_annotated"
        )

    # ---------------------------------------------------------------- per frame
    def _on_image(self, msg: Image) -> None:
        frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        # YOLOv8-seg has the same API as YOLOv8 — the only difference
        # is `results[0].masks` is populated.
        results = self._model.predict(
            source=frame,
            conf=self._conf,
            device=self._device,
            verbose=False,
        )
        r = results[0]

        # 1. Detections (boxes still come for free, same as ex 04).
        self._det_pub.publish(self._build_detections(r, msg.header))

        # 2. Instance map: single-channel image, pixel value = instance id.
        instance_map = self._build_instance_map(r, frame.shape[:2])
        mask_msg = self._bridge.cv2_to_imgmsg(instance_map, encoding="mono8")
        mask_msg.header = msg.header
        self._mask_pub.publish(mask_msg)

        # 3. Annotated overlay (translucent masks drawn by ultralytics).
        annotated: np.ndarray = r.plot()       # bgr uint8, same H x W as input
        ann_msg = self._bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
        ann_msg.header = msg.header
        self._ann_pub.publish(ann_msg)

    # -------------------------------------------------------------- helpers
    def _build_detections(self, result, header) -> Detection2DArray:
        """Same as the exercise 04 helper — the bbox half of a seg result."""
        msg = Detection2DArray()
        msg.header = header
        if result.boxes is None or result.boxes.cls is None:
            return msg

        cls_arr = result.boxes.cls.cpu().numpy().astype(int)
        conf_arr = result.boxes.conf.cpu().numpy().astype(float)
        xywh_arr = result.boxes.xywh.cpu().numpy()

        det_list: List[Detection2D] = []
        for cls_id, conf, (cx, cy, w, h) in zip(cls_arr, conf_arr, xywh_arr):
            det = Detection2D()
            det.header = header
            det.bbox = BoundingBox2D()
            det.bbox.center.position.x = float(cx)
            det.bbox.center.position.y = float(cy)
            det.bbox.size_x = float(w)
            det.bbox.size_y = float(h)
            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = self._names[int(cls_id)]
            hyp.hypothesis.score = float(conf)
            det.results.append(hyp)
            det_list.append(det)
        msg.detections = det_list
        return msg

    def _build_instance_map(self, result, hw) -> np.ndarray:
        """One pixel = one instance id.

        result.masks.data is a torch tensor of shape (N, H, W) with values
        in [0, 1] (per-pixel soft mask). We threshold at 0.5 and paint
        each instance with a unique uint8 id. Background stays 0.

        Cap at 254 instances so the value fits in mono8 (255 stays
        reserved as "overflow" if you ever need it).
        """
        h, w = hw
        instance_map = np.zeros((h, w), dtype=np.uint8)
        if result.masks is None:
            return instance_map

        masks = result.masks.data.cpu().numpy()   # (N, H, W) float
        for i, m in enumerate(masks):
            iid = min(i + 1, 254)
            instance_map[m > 0.5] = iid
        return instance_map


def main() -> None:
    rclpy.init()
    node = SegNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
