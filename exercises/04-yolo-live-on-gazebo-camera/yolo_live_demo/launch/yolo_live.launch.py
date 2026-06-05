"""Launch Gazebo + ros_gz_image bridge + the YOLO live detector + RViz.

Five processes start together:

    1. Gazebo Sim with worlds/autosampler_cell_with_camera.sdf
       (publishes frames on the Gazebo Transport topic
       /overhead_camera/image_raw)
    2. ros_gz_image bridge that re-publishes those frames as
       sensor_msgs/Image on the SAME ROS 2 topic name
    3. The YOLO live detector node (this package)
    4. RViz with a saved layout that shows both the raw camera
       image and the annotated overlay topic

The weights file path is required - pass it on the command line:

    ros2 launch yolo_live_demo yolo_live.launch.py \\
        weights:=/abs/path/to/best.pt
"""

from __future__ import annotations

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    # ---- launch args ------------------------------------------------------
    # `weights` is REQUIRED — no sensible default. The user passes a path to
    # exercise 3's best.pt (or any other YOLOv8 .pt).
    weights_arg = DeclareLaunchArgument(
        "weights",
        description="Absolute path to the YOLOv8 .pt checkpoint",
    )
    # `world` defaults to the SDF shipped next to this exercise (resolved
    # from the source tree, so a colcon workspace symlink still works).
    default_world = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "worlds", "autosampler_cell_with_camera.sdf",
        )
    )
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=default_world,
        description="Absolute path to the SDF world file",
    )
    # Toggle CPU/GPU without editing code.
    device_arg = DeclareLaunchArgument(
        "device",
        default_value="cpu",
        description='"cpu" or "0" for the first GPU',
    )
    # Drop low-confidence boxes here, not in the visualiser.
    conf_arg = DeclareLaunchArgument(
        "conf",
        default_value="0.25",
        description="Confidence threshold passed to YOLO.predict",
    )

    # ---- processes --------------------------------------------------------
    # 1. Gazebo Sim with the world.
    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", LaunchConfiguration("world")],  # -r = start unpaused
        output="screen",
    )

    # 2. Image bridge — Gazebo Transport -> ROS 2 sensor_msgs/Image.
    # Same topic name on both sides keeps the data flow obvious.
    image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/overhead_camera/image_raw"],
        output="screen",
    )

    # 3. The YOLO live detector node.
    detector = Node(
        package="yolo_live_demo",
        executable="live_detector",
        name="yolo_live_detector",
        output="screen",
        parameters=[{
            "weights": LaunchConfiguration("weights"),
            "image_topic": "/overhead_camera/image_raw",
            "detections_topic": "/yolo/detections",
            "annotated_topic": "/yolo/image_annotated",
            "conf_threshold": LaunchConfiguration("conf"),
            "device": LaunchConfiguration("device"),
        }],
    )

    # 4. RViz with a saved layout that opens the two image topics.
    rviz_config = os.path.join(
        get_package_share_directory("yolo_live_demo"),
        "config", "yolo_live.rviz",
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        output="screen",
    )

    return LaunchDescription([
        weights_arg,
        world_arg,
        device_arg,
        conf_arg,
        gazebo,
        image_bridge,
        detector,
        rviz,
    ])
