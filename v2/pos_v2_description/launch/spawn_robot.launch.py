"""Launch the v2 backroom world with the v2 robot spawned at home.

Brings up:
  - Gazebo Harmonic + the backroom world (via pos_v2_bringup)
  - robot_state_publisher fed by xacro
  - ros_gz_sim `create` to spawn the URDF at the home marker
  - ros_gz_bridge for cmd_vel / odom / scan / tf / imu / joint_states / clock

Drive the robot from another terminal with e.g. teleop_twist_keyboard:
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('pos_v2_description')
    pkg_bringup = get_package_share_directory('pos_v2_bringup')

    xacro_file = os.path.join(pkg_description, 'urdf', 'robot.urdf.xacro')
    bridge_config = os.path.join(pkg_description, 'config', 'bridge.yaml')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'backroom.launch.py')
        ),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    # Spawn the URDF into Gazebo at the yellow home marker (-3, -3),
    # facing north (+Y) toward the pallet racks.
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_pos_v2_robot',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'pos_v2_robot',
            '-x', '-3.0',
            '-y', '-3.0',
            '-z', '0.10',
            '-Y', '1.5707963',
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True,
        }],
    )

    return LaunchDescription([
        world_launch,
        robot_state_publisher,
        bridge,
        spawn_robot,
    ])
