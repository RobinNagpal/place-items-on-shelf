#!/usr/bin/env python3
"""Launch the cartesian_pose_demo node with addison's MoveIt config attached.

The world this exercise targets is
  ../../01-custom-gazebo-world/worlds/autosampler_cell.sdf
(the HPLC autosampler bench, source rack on the +Y side, destination
tray on the -Y side). We do NOT redeclare the world - the demo just
runs against whatever Gazebo world is already up.

Pose targets are written in the arm's base_link frame inside the C++
file. The arm base sits at world (-0.18, 0, 0.775) per the SDF, so
world coords convert to base_link by subtracting that origin.

Prereqs (each in its own terminal):

  Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher:
        ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \\
            world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf

  Terminal B - move_group action server:
        ros2 launch mycobot_moveit_config move_group.launch.py

  Terminal C - this exercise:
        ros2 launch cartesian_pose_demo cartesian_pose_demo.launch.py

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
    """Resolve runtime args and assemble the Node action.

    OpaqueFunction lets us call Python at launch time so we can do
    the MoveItConfigsBuilder dance (which needs concrete file paths,
    not LaunchConfiguration substitutions).
    """
    robot_name = LaunchConfiguration("robot_name").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context).lower() == "true"

    # Pull SRDF + kinematics + joint limits + trajectory exec config
    # out of addison's mycobot_moveit_config. We do not duplicate any
    # of those files in this exercise.
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
            package="cartesian_pose_demo",
            executable="cartesian_pose_demo",
            output="screen",
            parameters=[
                # URDF (robot_description) is pulled from the running
                # robot_state_publisher's /robot_description topic,
                # so we do NOT pass moveit_config.robot_description.
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
