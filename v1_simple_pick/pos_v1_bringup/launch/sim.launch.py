"""Launch Gazebo Harmonic with the v1 store world, spawn the robot, and start the ROS↔Gazebo bridge."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('pos_v1_bringup')
    pkg_description = get_package_share_directory('pos_v1_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_bringup, 'worlds', 'store.sdf')
    urdf_file = os.path.join(pkg_description, 'urdf', 'pos_robot.urdf')
    bridge_config = os.path.join(pkg_bringup, 'config', 'gz_bridge.yaml')

    with open(urdf_file, 'r', encoding='utf-8') as f:
        robot_description_xml = f.read()

    # Start Gazebo Harmonic with the world.
    # -r = run on start, -v 3 = verbose level 3 (info).
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 3 {world_file}'}.items(),
    )

    # Publishes /robot_description and TF for the URDF.
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_xml,
            'use_sim_time': True,
        }],
    )

    # Spawns the robot in Gazebo from the /robot_description topic.
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'pos_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen',
    )

    # Bridges Gazebo topics ↔ ROS 2 topics per config file.
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True,
        }],
        output='screen',
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
    ])
