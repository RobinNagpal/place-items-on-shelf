"""No-hardware RViz viewer for the Elephant Robotics myCobot 280 Pi.

Loads the manufacturer URDF (`mycobot_description/urdf/mycobot_280_pi/`)
from the vendored `mycobot_ros2` submodule, runs robot_state_publisher
and joint_state_publisher_gui, and opens RViz with our pinned config.

No serial port, no SDK, no real arm needed — this is purely so you can
verify the URDF, dimensions, and joint limits before ordering hardware.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    urdf_default = os.path.join(
        get_package_share_directory("mycobot_description"),
        "urdf",
        "mycobot_280_pi",
        "mycobot_280_pi.urdf",
    )
    rviz_default = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "rviz",
        "view.rviz",
    )

    model_arg = DeclareLaunchArgument("model", default_value=urdf_default)
    rviz_arg = DeclareLaunchArgument("rvizconfig", default_value=rviz_default)

    robot_description = ParameterValue(
        Command(["xacro ", LaunchConfiguration("model")]),
        value_type=str,
    )

    return LaunchDescription(
        [
            model_arg,
            rviz_arg,
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                output="screen",
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", LaunchConfiguration("rvizconfig")],
            ),
        ]
    )
