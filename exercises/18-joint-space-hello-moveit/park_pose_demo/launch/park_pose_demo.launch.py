#!/usr/bin/env python3
"""Launch the park_pose_demo node with addison's MoveIt config attached.

The world this exercise targets is
  ../../01-custom-gazebo-world/worlds/autosampler_cell.sdf
(the HPLC autosampler bench, the source rack on the +Y side, the tray
on the -Y side, three vials in the back row of the rack). We do NOT
declare the world again here - the demo just runs against whatever
Gazebo world is already up.

The SRDF "ready" pose is reused as the park-between-trays goal.
See ../README.md for why that one happens to be the right pose for
the autosampler cell.

Prereqs (each in its own terminal):

  Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher.
    Point Gazebo at the autosampler world if the upstream launch
    accepts a world arg:
        ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \\
            world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf
    Or fall back to the default world if it doesn't (see
    IMPLEMENTATION_NOTES.md).

  Terminal B - move_group action server:
        ros2 launch mycobot_moveit_config move_group.launch.py

  Terminal C - this exercise:
        ros2 launch park_pose_demo park_pose_demo.launch.py

Args:
  robot_name    addison's robot folder under mycobot_moveit_config/config/
                Default "mycobot_280".
  use_sim_time  true (the normal case - we use Gazebo's clock).
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

    OpaqueFunction lets us call into Python at launch time so we can
    do the MoveItConfigsBuilder dance (which needs concrete paths,
    not LaunchConfiguration substitutions).
    """
    robot_name = LaunchConfiguration("robot_name").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context).lower() == "true"

    # Pull the SRDF + kinematics + joint limits + trajectory exec
    # config out of addison's mycobot_moveit_config. We do not
    # duplicate any of those files in this exercise.
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
            package="park_pose_demo",
            executable="park_pose_demo",
            output="screen",
            parameters=[
                # URDF (robot_description) is pulled from the running
                # robot_state_publisher's /robot_description topic, so
                # we do NOT pass moveit_config.robot_description here.
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
