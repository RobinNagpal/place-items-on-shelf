#!/usr/bin/env python3
"""Minimal subscription debug for the synthetic-data pipeline.

If `generate_dataset.py` says "waiting for first image / poses..."
forever, run this instead. It does NOTHING except subscribe to the
two bridged topics and print one line per message. If you do not
see prints, the problem is at the ROS 2 / bridge level — not in
the dataset code.

Run after starting gz sim and ros_gz_bridge:

    source /opt/ros/$ROS_DISTRO/setup.bash
    python3 test_subscribe.py

Expected output (one of these lines per second once gz sim is
playing):

    [image]   640x480 bgr8        — bridge -> ROS 2 OK
    [poses]   12 transforms (beaker_1, beaker_2, ...)  — bridge -> ROS 2 OK

If neither line appears within ~10 s, the subscription is not
matching the publisher. Use the commands at the bottom of this
file to dig further.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from tf2_msgs.msg import TFMessage


WORLD_NAME = "ketchup_extraction_cell"


class Probe(Node):
    def __init__(self) -> None:
        super().__init__("synthetic_data_probe")

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

        self._img_n = 0
        self._pose_n = 0
        self.create_timer(2.0, self._heartbeat)

        self.get_logger().info(
            "subscribed; waiting for messages. Press Ctrl+C to stop."
        )

    def _on_image(self, msg: Image) -> None:
        self._img_n += 1
        if self._img_n <= 5 or self._img_n % 30 == 0:
            self.get_logger().info(
                f"[image] {msg.width}x{msg.height} {msg.encoding}  "
                f"(#{self._img_n})"
            )

    def _on_poses(self, msg: TFMessage) -> None:
        self._pose_n += 1
        if self._pose_n <= 5 or self._pose_n % 100 == 0:
            names = ", ".join(t.child_frame_id for t in msg.transforms[:6])
            self.get_logger().info(
                f"[poses] {len(msg.transforms)} transforms "
                f"({names}{'...' if len(msg.transforms) > 6 else ''})  "
                f"(#{self._pose_n})"
            )

    def _heartbeat(self) -> None:
        if self._img_n == 0 and self._pose_n == 0:
            self.get_logger().warn(
                "no messages on either topic yet. Likely causes: "
                "(1) bridge not running, (2) gz sim paused, "
                "(3) topic names wrong, (4) DDS discovery blocked. "
                "Run the commands at the bottom of test_subscribe.py."
            )
        else:
            self.get_logger().info(
                f"heartbeat — image msgs: {self._img_n}, "
                f"pose msgs: {self._pose_n}"
            )


def main() -> None:
    rclpy.init()
    node = Probe()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Manual debug commands (run in a separate terminal with ROS 2 sourced)
# ---------------------------------------------------------------------------
#
# 1) Confirm the bridge is publishing both topics:
#    ros2 topic list
#
# 2) Confirm publisher QoS — look for "Reliability: BEST_EFFORT" or
#    "RELIABLE":
#    ros2 topic info /overhead_camera/image_raw -v
#    ros2 topic info /world/ketchup_extraction_cell/pose/info -v
#
# 3) Force a BEST_EFFORT echo. If this prints a message, the bridge is
#    publishing and BEST_EFFORT subscribers match:
#    ros2 topic echo /overhead_camera/image_raw --qos-reliability best_effort --once
#    ros2 topic echo /world/ketchup_extraction_cell/pose/info --qos-reliability best_effort --once
#
# 4) Confirm `gz sim` is playing — click ▶ in the GUI, or relaunch with
#    `gz sim -r path/to/world.sdf`.
#
# 5) DDS discovery sanity check (same domain ID across terminals):
#    echo $ROS_DOMAIN_ID         # if empty, default 0
#    ros2 daemon stop && ros2 daemon start
#
# 6) Final fallback — switch DDS implementation:
#    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp   # one terminal
#    Repeat for every terminal (bridge, generator, gz sim).
