"""Hand-eye calibration for the overhead camera -- exercise 12.

Our camera is **fixed in the world** (not mounted on the arm), so
this is the **eye-to-hand** flavour of hand-eye calibration. The
unknown we want is the static transform from the camera frame to
the arm base frame:

    T_base_cam  --  the 4x4 matrix item 12 leaves behind

The recipe, in plain English:

    1. Stick an ArUco marker on the end-effector.
    2. Drive the arm to N different poses (N ~= 20).
    3. At each pose grab two things:
         - T_base_ee   from TF        (the arm tells us)
         - T_cam_marker from ArUco   (the camera tells us)
    4. Send the N pairs to cv2.calibrateHandEye -- it solves the
       AX = XB pose problem and returns the one transform that
       makes every pair consistent.

OpenCV's API is named for the eye-IN-hand case (camera on EE). The
documented trick for eye-TO-hand is to **invert all EE poses**
before calling the function and **invert the result** afterwards.
We do exactly that in solve_eye_to_hand().

Run after ArUco detection (item 10) is publishing and the arm is
moving through 20 poses (a small `move_through_calibration_poses.py`
helper is the natural companion -- not shipped here because it is
just a loop of exercise 19's setPoseTarget):

    python3 hand_eye_calibrate.py --ros-args \
        -p marker_topic:=/aruco/marker_pose \
        -p ee_frame:=tool0 \
        -p base_frame:=base_link \
        -p num_samples:=20
"""

from __future__ import annotations

import math
from typing import List, Tuple

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


def quat_to_rmat(qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
    """Quaternion -> 3x3 rotation matrix (right-handed, w-last)."""
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
    qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    return np.array([
        [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)],
    ])


def pose_to_rt(pose) -> Tuple[np.ndarray, np.ndarray]:
    """geometry_msgs Pose / Transform -> (R 3x3, t 3x1) numpy arrays."""
    p = pose.position if hasattr(pose, "position") else pose.translation
    q = pose.orientation if hasattr(pose, "orientation") else pose.rotation
    R = quat_to_rmat(q.x, q.y, q.z, q.w)
    t = np.array([[p.x], [p.y], [p.z]])
    return R, t


def invert_rt(R: np.ndarray, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Inverse of a rigid transform: (R, t) -> (R.T, -R.T @ t)."""
    Ri = R.T
    ti = -Ri @ t
    return Ri, ti


def solve_eye_to_hand(
    R_base_ee_list: List[np.ndarray], t_base_ee_list: List[np.ndarray],
    R_cam_marker_list: List[np.ndarray], t_cam_marker_list: List[np.ndarray],
) -> Tuple[np.ndarray, np.ndarray]:
    """Solve T_base_cam from N (base->ee, cam->marker) pose pairs.

    cv2.calibrateHandEye assumes EYE-IN-HAND (camera on the gripper).
    For eye-to-hand we invert the gripper-to-base poses before
    calling it, and invert the result. The OpenCV docs spell this
    out under "Eye-to-Hand variant".
    """
    R_ee_base, t_ee_base = [], []
    for R, t in zip(R_base_ee_list, t_base_ee_list):
        Ri, ti = invert_rt(R, t)
        R_ee_base.append(Ri)
        t_ee_base.append(ti)

    # OpenCV recommends DANIILIDIS for general-purpose; TSAI is a
    # well-known faster alternative if N is very large.
    R_cam_in_base, t_cam_in_base = cv2.calibrateHandEye(
        R_gripper2base=R_ee_base,
        t_gripper2base=t_ee_base,
        R_target2cam=R_cam_marker_list,
        t_target2cam=t_cam_marker_list,
        method=cv2.CALIB_HAND_EYE_DANIILIDIS,
    )
    return R_cam_in_base, t_cam_in_base


def rt_to_xyzrpy(R: np.ndarray, t: np.ndarray) -> Tuple[float, ...]:
    """3x3 R + 3x1 t -> (x, y, z, roll, pitch, yaw) for printing."""
    sy = math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
    if sy > 1e-6:
        roll = math.atan2(R[2, 1], R[2, 2])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = math.atan2(R[1, 0], R[0, 0])
    else:
        roll = math.atan2(-R[1, 2], R[1, 1])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = 0.0
    return float(t[0]), float(t[1]), float(t[2]), roll, pitch, yaw


class HandEyeCalibrator(Node):

    def __init__(self) -> None:
        super().__init__("hand_eye_calibrate")

        self.declare_parameter("marker_topic", "/aruco/marker_pose")
        self.declare_parameter("ee_frame", "tool0")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("num_samples", 20)
        self.declare_parameter("min_pose_spread_m", 0.05)

        self._marker_topic = str(self.get_parameter("marker_topic").value)
        self._ee_frame = str(self.get_parameter("ee_frame").value)
        self._base_frame = str(self.get_parameter("base_frame").value)
        self._num_samples = int(self.get_parameter("num_samples").value)
        self._spread = float(self.get_parameter("min_pose_spread_m").value)

        self._tf_buf = Buffer()
        self._tf_lis = TransformListener(self._tf_buf, self)

        # Pose pairs accumulate here -- one entry per arm pose.
        self._R_base_ee: List[np.ndarray] = []
        self._t_base_ee: List[np.ndarray] = []
        self._R_cam_marker: List[np.ndarray] = []
        self._t_cam_marker: List[np.ndarray] = []

        self.create_subscription(
            PoseStamped, self._marker_topic, self._on_marker, 10
        )

        self.get_logger().info(
            f"collecting {self._num_samples} samples from {self._marker_topic} "
            f"+ TF({self._base_frame} <- {self._ee_frame})"
        )

    # ------------------------------------------------------------------ subs
    def _on_marker(self, marker_msg: PoseStamped) -> None:
        """Each ArUco message is one calibration sample candidate."""
        if len(self._R_base_ee) >= self._num_samples:
            return

        # T_cam_marker is the message itself.
        R_cm, t_cm = pose_to_rt(marker_msg.pose)

        # T_base_ee from TF at the same timestamp.
        try:
            tf: TransformStamped = self._tf_buf.lookup_transform(
                self._base_frame, self._ee_frame, marker_msg.header.stamp
            )
        except TransformException as ex:
            self.get_logger().warn(f"TF unavailable: {ex}; skipping sample")
            return

        R_be, t_be = pose_to_rt(tf.transform)

        # Skip near-duplicate poses -- calibration accuracy depends on
        # pose VARIETY. A few millimetres of motion adds no information.
        if self._is_too_close(t_be):
            return

        self._R_base_ee.append(R_be)
        self._t_base_ee.append(t_be)
        self._R_cam_marker.append(R_cm)
        self._t_cam_marker.append(t_cm)

        n = len(self._R_base_ee)
        self.get_logger().info(f"sample {n}/{self._num_samples} captured")

        if n >= self._num_samples:
            self._solve_and_publish()

    def _is_too_close(self, t_new: np.ndarray) -> bool:
        for t_old in self._t_base_ee:
            if float(np.linalg.norm(t_new - t_old)) < self._spread:
                return True
        return False

    # ------------------------------------------------------------------ solve
    def _solve_and_publish(self) -> None:
        R, t = solve_eye_to_hand(
            self._R_base_ee, self._t_base_ee,
            self._R_cam_marker, self._t_cam_marker,
        )
        x, y, z, roll, pitch, yaw = rt_to_xyzrpy(R, t)

        self.get_logger().info(
            "\n=== T_base_cam (overhead camera in robot base frame) ==="
            f"\n  translation: x={x:.4f}  y={y:.4f}  z={z:.4f}  metres"
            f"\n  rotation:    roll={roll:.4f}  pitch={pitch:.4f}  yaw={yaw:.4f}  rad"
        )

        # The output is meant to be baked in as a static TF. Print the
        # ros2 command verbatim so the user can paste it into a launch.
        cmd = (
            "ros2 run tf2_ros static_transform_publisher "
            f"--x {x:.4f} --y {y:.4f} --z {z:.4f} "
            f"--roll {roll:.4f} --pitch {pitch:.4f} --yaw {yaw:.4f} "
            f"--frame-id {self._base_frame} "
            "--child-frame-id overhead_camera_optical_frame"
        )
        self.get_logger().info(f"\nstatic TF command:\n  {cmd}")

        # Compute a sanity error: project marker pose i into the base
        # frame using T_base_cam, compare with T_base_ee_i (which is
        # where the marker actually is, ignoring the marker mount
        # offset which is constant across samples).
        self._report_residuals(R, t)

        # Shut the node down so the script exits cleanly.
        self.get_logger().info("calibration complete; shutting down")
        rclpy.shutdown()

    def _report_residuals(self, R_bc: np.ndarray, t_bc: np.ndarray) -> None:
        """Average position error after applying the solved transform."""
        errs: List[float] = []
        for R_be, t_be, R_cm, t_cm in zip(
            self._R_base_ee, self._t_base_ee,
            self._R_cam_marker, self._t_cam_marker,
        ):
            # Marker pose expressed in base frame, two ways:
            t_via_cam = R_bc @ t_cm + t_bc        # camera path
            t_via_arm = t_be                       # arm path (ignores
                                                   # mount offset, so this
                                                   # is a relative number)
            errs.append(float(np.linalg.norm(t_via_cam - t_via_arm)))

        mean = float(np.mean(errs))
        std = float(np.std(errs))
        self.get_logger().info(
            f"residual mean={mean*1000:.2f} mm  std={std*1000:.2f} mm  "
            "(treat as a relative consistency check, not absolute error)"
        )


def main() -> None:
    rclpy.init()
    node = HandEyeCalibrator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
