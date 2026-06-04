#!/usr/bin/env python3
"""Launch the collision_demo node with addison's MoveIt config attached.

The world this exercise targets is
  ../worlds/autosampler_cell_v2.sdf
(v1 + housing back wall + a semi-transparent no-fly marker over
vial_a1). The matching MoveIt collision objects are added at runtime
by collision_demo.cpp; we don't load them from any YAML.

Prereqs (each in its own terminal):

  Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher:
        ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \\
            world:=$(pwd)/exercises/20-collision-objects/worlds/autosampler_cell_v2.sdf

  Terminal B - move_group action server:
        ros2 launch mycobot_moveit_config move_group.launch.py

  Terminal C - this exercise:
        ros2 launch collision_demo collision_demo.launch.py

Args:
  robot_name    addison's robot folder under mycobot_moveit_config/config/.
                Default "mycobot_280".
  use_sim_time  true (the normal case - Gazebo clock).
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def _build_node(context, *_args, **_kwargs):
    robot_name = LaunchConfiguration("robot_name").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context).lower() == "true"

    pkg_share = FindPackageShare("mycobot_moveit_config").perform(context)
    cfg_dir = os.path.join(pkg_share, "config", robot_name)

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="mycobot_moveit_config")
        .robot_description_semantic(file_path=os.path.join(cfg_dir, f"{robot_name}.srdf"))
        .robot_description_kinematics(file_path=os.path.join(cfg_dir, "kinematics.yaml"))
        .joint_limits(file_path=os.path.join(cfg_dir, "joint_limits.yaml"))
        .trajectory_execution(file_path=os.path.join(cfg_dir, "moveit_controllers.yaml"))
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )

    return [
        Node(
            package="collision_demo",
            executable="collision_demo",
            output="screen",
            parameters=[
                # URDF (robot_description) comes from robot_state_publisher.
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.joint_limits,
                moveit_config.trajectory_execution,
                moveit_config.planning_pipelines,
                {"use_sim_time": use_sim_time},
            ],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "robot_name",
            default_value="mycobot_280",
            description="Robot name; must match the subdir under mycobot_moveit_config/config/.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use Gazebo sim clock when true (the normal case for this stack).",
        ),
        OpaqueFunction(function=_build_node),
    ])
