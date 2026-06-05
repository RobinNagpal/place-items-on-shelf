"""ArUco marker 6-DoF pose detector -- exercise 10.

Takes a plain RGB image from the overhead camera, finds every
ArUco marker in it, and publishes each one's full 6-DoF pose
(position + orientation) in the camera frame.

A single RGB image is enough -- depth is NOT required. The 4
corners of a known-size square give 4 known 3D-to-2D point
correspondences, and 4 such correspondences are enough to solve
the camera-to-marker rigid transform. That problem is called
'Perspective-n-Point' (PnP) and OpenCV's `cv2.solvePnP` solves it
in a few milliseconds.

Input:
    /overhead_camera/image_raw    sensor_msgs/Image (bgr8)

Output:
    /aruco/markers                vision_msgs/Detection3DArray
        detections[i].bbox.center  = 6-DoF pose of the marker
                                     (position in metres, orientation
                                      as a quaternion, all in the
                                      camera frame)
        detections[i].bbox.size    = (marker_size, marker_size, ~0)
        detections[i].results[0].hypothesis.class_id = "aruco_<id>"

Hand-eye calibration (exercise 12) consumes this topic to recover
the camera <-> arm-base transform.
"""

from __future__ import annotations

import math
from typing import Tuple

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection3D,
    Detection3DArray,
    ObjectHypothesisWithPose,
)


# ---------------------------------------------------------------------------
# Camera intrinsics -- match worlds/autosampler_cell_with_camera.sdf from
# exercise 04. Same constants as exercises 05 and 08.
# ---------------------------------------------------------------------------
IMG_W, IMG_H = 640, 480
HFOV = 1.0472                                # 60 deg
FX = (IMG_W / 2) / math.tan(HFOV / 2)
FY = FX
CX_PX, CY_PX = IMG_W / 2.0, IMG_H / 2.0

CAMERA_MATRIX = np.array(
    [[FX, 0.0, CX_PX], [0.0, FY, CY_PX], [0.0, 0.0, 1.0]],
    dtype=np.float32,
)
# Gazebo's camera plugin emits ideal pinhole images (no lens distortion).
DIST_COEFFS = np.zeros((5,), dtype=np.float32)


def rmat_to_quat(R: np.ndarray) -> Tuple[float, float, float, float]:
    """3x3 rotation matrix -> (qx, qy, qz, qw). Standard trace formula."""
    trace = R[0, 0] + R[1, 1] + R[2, 2]
    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        qw = 0.25 / s
        qx = (R[2, 1] - R[1, 2]) * s
        qy = (R[0, 2] - R[2, 0]) * s
        qz = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    return qx, qy, qz, qw


class ArucoDetectorNode(Node):

    def __init__(self) -> None:
        super().__init__("aruco_detector")

        self.declare_parameter("image_topic", "/overhead_camera/image_raw")
        self.declare_parameter("marker_size_m", 0.030)        # 30 mm default
        self.declare_parameter("dictionary", "DICT_4X4_50")

        image_topic = str(self.get_parameter("image_topic").value)
        self._marker_size = float(self.get_parameter("marker_size_m").value)
        dict_name = str(self.get_parameter("dictionary").value)

        # Resolve cv2.aruco.DICT_* by string name.
        dict_id = getattr(cv2.aruco, dict_name)
        dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
        params = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(dictionary, params)

        # The 4 corners of the marker in the MARKER's own frame.
        # Z=0 plane, centred on the marker centre. Order matches what
        # cv2.aruco.detectMarkers returns: top-left, top-right,
        # bottom-right, bottom-left.
        s = self._marker_size / 2.0
        self._object_pts = np.array(
            [[-s,  s, 0.0],
             [ s,  s, 0.0],
             [ s, -s, 0.0],
             [-s, -s, 0.0]],
            dtype=np.float32,
        )

        self._bridge = CvBridge()
        self.create_subscription(Image, image_topic, self._on_image, 10)
        self._pub = self.create_publisher(
            Detection3DArray, "/aruco/markers", 10
        )

        self.get_logger().info(
            f"subscribed to {image_topic}; marker size "
            f"{self._marker_size * 1000:.1f} mm; dictionary {dict_name}; "
            "publishing /aruco/markers"
        )

    # ------------------------------------------------------------------ frame
    def _on_image(self, msg: Image) -> None:
        frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Step 1: find the markers' corners + IDs in the image.
        corners, ids, _ = self._detector.detectMarkers(gray)

        out = Detection3DArray()
        out.header = msg.header
        if ids is None or len(ids) == 0:
            self._pub.publish(out)        # empty array; still publish
            return

        # Step 2: for each marker, solve PnP to get the 6-DoF pose.
        # SOLVEPNP_IPPE_SQUARE is specifically designed for planar
        # 4-corner targets like ArUco. It is ~5x faster than the
        # iterative solver and as accurate.
        for marker_corners, marker_id in zip(corners, ids.flatten()):
            image_pts = marker_corners.reshape(-1, 2).astype(np.float32)
            ok, rvec, tvec = cv2.solvePnP(
                self._object_pts, image_pts,
                CAMERA_MATRIX, DIST_COEFFS,
                flags=cv2.SOLVEPNP_IPPE_SQUARE,
            )
            if not ok:
                continue

            # rvec is axis-angle (3 numbers); convert to a 3x3 matrix
            # then to a quaternion for the ROS message.
            R, _ = cv2.Rodrigues(rvec)
            qx, qy, qz, qw = rmat_to_quat(R)

            det = Detection3D()
            det.header = msg.header
            det.bbox.center.position.x = float(tvec[0])
            det.bbox.center.position.y = float(tvec[1])
            det.bbox.center.position.z = float(tvec[2])
            det.bbox.center.orientation.x = qx
            det.bbox.center.orientation.y = qy
            det.bbox.center.orientation.z = qz
            det.bbox.center.orientation.w = qw
            det.bbox.size.x = self._marker_size
            det.bbox.size.y = self._marker_size
            det.bbox.size.z = 0.001                  # marker is flat-ish

            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = f"aruco_{int(marker_id)}"
            hyp.hypothesis.score = 1.0               # PnP either solved or didn't
            hyp.pose.pose = det.bbox.center
            det.results.append(hyp)
            out.detections.append(det)

        self._pub.publish(out)


def main() -> None:
    rclpy.init()
    node = ArucoDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
