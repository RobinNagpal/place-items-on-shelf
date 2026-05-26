"""Launch Gazebo Harmonic with the v1 store world, spawn the robot, start
the ros2_control controller_manager (in-process inside Gazebo via the
gz_ros2_control plugin), then spawn the controllers in sequence.

Sequence:
  1) gz sim brings up the store world
  2) robot_state_publisher publishes /robot_description (URDF processed
     through xacro to expand $(find pos_v1_bringup) into an absolute path
     for the gz_ros2_control plugin's <parameters> element)
  3) ros_gz_sim/create spawns the robot from /robot_description
  4) When the create node exits, the joint_state_broadcaster spawner runs
  5) When that exits, arm_controller spawner runs
  6) When that exits, gripper_controller spawner runs
  7) Bridge runs in parallel with the rest
"""

import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('pos_v1_bringup')
    pkg_description = get_package_share_directory('pos_v1_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_bringup, 'worlds', 'store.sdf')
    urdf_file = os.path.join(pkg_description, 'urdf', 'pos_robot.urdf')
    bridge_config = os.path.join(pkg_bringup, 'config', 'gz_bridge.yaml')

    # Process URDF as xacro so $(find ...) is expanded. The result is plain
    # URDF that robot_state_publisher and Gazebo can read.
    robot_description_xml = xacro.process_file(urdf_file).toxml()

    # Start Gazebo Harmonic with the world.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 3 {world_file}'}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_xml,
            'use_sim_time': True,
        }],
    )

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

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True,
        }],
        output='screen',
    )

    # Controller spawners — must run AFTER the gz_ros2_control plugin is up
    # (which happens when the robot model is spawned into Gazebo).
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    # Chain: spawn_robot -> joint_state_broadcaster -> arm_controller -> gripper_controller.
    # spawner exits as soon as the controller is active, so OnProcessExit
    # is the right trigger.
    after_spawn_robot = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )
    after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        )
    )
    after_arm = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[gripper_controller_spawner],
        )
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        after_spawn_robot,
        after_jsb,
        after_arm,
    ])
