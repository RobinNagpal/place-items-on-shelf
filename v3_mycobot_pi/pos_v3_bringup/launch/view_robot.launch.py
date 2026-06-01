"""Launch file: display the myCobot 280 Pi URDF in RViz with a
joint_state_publisher_gui so the user can drag sliders and verify
the arm's exact dimensions and joint motion before the hardware
arrives.

This is Step 1 of v3 — visualization only, no physics or controllers.
Gazebo + ros2_control come in Step 3.
"""

import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_description = get_package_share_directory('pos_v3_description')
    pkg_bringup = get_package_share_directory('pos_v3_bringup')

    urdf_file = os.path.join(pkg_description, 'urdf', 'mycobot_280pi.urdf')
    rviz_config = os.path.join(pkg_bringup, 'rviz', 'view_robot.rviz')

    # xacro.process_file handles both plain URDF and xacro syntax, so the
    # .urdf-with-xacro-macros pattern used by v1 works here too.
    robot_description_xml = xacro.process_file(urdf_file).toxml()

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_xml}],
    )

    # Drives /joint_states from a slider GUI — one slider per movable joint.
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz,
    ])
