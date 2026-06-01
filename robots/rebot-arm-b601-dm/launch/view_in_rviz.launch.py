import os

from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare("rebotarm_bringup")
    urdf_file = PathJoinSubstitution(
        [bringup_share, "description", "urdf", "reBot-DevArm_fixend.urdf"]
    )
    # Seeed's bundled rebotarm.rviz is a stub: no Tools, no Views, no panels
    # besides Displays — so the viewport renders the arm but mouse pan/zoom
    # doesn't work and the camera sits at the default 10m distance, making a
    # ~30cm arm look like a pixel. Use our own config sitting next to this
    # launch file instead.
    rviz_config = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "rviz", "view.rviz"
    )
    robot_description = ParameterValue(Command(["cat ", urdf_file]), value_type=str)

    # Unlike Seeed's bundled rviz.launch.py, we do NOT remap /joint_states to
    # /rebotarm/joint_states. We want joint_state_publisher_gui's slider output
    # (which publishes on /joint_states) to flow into robot_state_publisher
    # so the arm animates without a real controller connected.
    return LaunchDescription(
        [
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
                arguments=["-d", rviz_config],
            ),
        ]
    )
