#!/usr/bin/env python3
"""Launch the cobot280_move_to_named_pose task node.

Loads addison's mycobot_moveit_config so MoveGroupInterface inside the task
node sees robot_description_semantic, kinematics, joint limits, and the
trajectory_execution config. URDF is pulled from /robot_description (published
by robot_state_publisher inside mycobot_gazebo) so we do not duplicate it here.

Prereqs:
  - mycobot_gazebo.mycobot.gazebo.launch.py is already running (Gazebo + RViz
    + ros2_control + robot_state_publisher).
  - mycobot_moveit_config move_group.launch.py is already running (move_group
    action server).

Run:
  ros2 launch cobot280_moveit_task move_to_named_pose.launch.py
"""

import os

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def _build_node(context, *_args, **_kwargs):
    robot_name = LaunchConfiguration("robot_name").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context).lower() == "true"

    pkg_share_moveit_config = FindPackageShare("mycobot_moveit_config").perform(context)
    config_path = os.path.join(pkg_share_moveit_config, "config", robot_name)

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="mycobot_moveit_config")
        .robot_description_semantic(file_path=os.path.join(config_path, f"{robot_name}.srdf"))
        .robot_description_kinematics(file_path=os.path.join(config_path, "kinematics.yaml"))
        .joint_limits(file_path=os.path.join(config_path, "joint_limits.yaml"))
        .trajectory_execution(file_path=os.path.join(config_path, "moveit_controllers.yaml"))
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )

    return [
        Node(
            package="cobot280_moveit_task",
            executable="move_to_named_pose",
            output="screen",
            parameters=[
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.joint_limits,
                moveit_config.planning_pipelines,
                moveit_config.trajectory_execution,
                {"use_sim_time": use_sim_time},
            ],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "robot_name",
            default_value="mycobot_280",
            description="Robot name; must match the subdirectory under mycobot_moveit_config/config/.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use Gazebo sim clock when true (the normal case for this stack).",
        ),
        OpaqueFunction(function=_build_node),
    ])
