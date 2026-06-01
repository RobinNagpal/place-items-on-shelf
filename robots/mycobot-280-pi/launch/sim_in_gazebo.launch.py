"""Step 2: bring the myCobot 280 Pi up in Gazebo Sim (Harmonic) with ros2_control.

Launches:
  - gz sim with our worlds/empty.sdf (gravity disabled — kinematic only for now)
  - robot_state_publisher fed by description/mycobot_280_pi_sim.urdf.xacro
  - ros_gz_sim 'create' to spawn the robot from /robot_description
  - controller_manager spawner for joint_state_broadcaster
  - controller_manager spawner for arm_controller (JointTrajectoryController)

After it's up you can send a test trajectory with ros2 action send_goal; see
docs/run_sim.md for the exact command.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    pkg_root = os.path.abspath(os.path.join(this_dir, ".."))

    urdf_xacro = os.path.join(pkg_root, "description", "mycobot_280_pi_sim.urdf.xacro")
    controllers_yaml = os.path.join(pkg_root, "config", "controllers.yaml")
    world_sdf = os.path.join(pkg_root, "worlds", "empty.sdf")

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use simulation clock"
    )

    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                urdf_xacro,
                " controllers_yaml:=",
                controllers_yaml,
            ]
        ),
        value_type=str,
    )

    # gz sim (Gazebo Harmonic) — uses the launch file shipped by ros_gz_sim.
    gz_sim_share = get_package_share_directory("ros_gz_sim")
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": f"-r -v 3 {world_sdf}"}.items(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }
        ],
    )

    # Spawn the URDF as an entity in Gazebo.
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_mycobot_280_pi",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-name", "mycobot_280_pi",
            "-z", "0.05",
        ],
    )

    # Controller spawners — chained on entity-spawn completion so we don't race the plugin init.
    jsb_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    arm_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    chain_jsb_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[jsb_spawner])
    )
    chain_arm_after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=jsb_spawner, on_exit=[arm_spawner])
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            gz_sim,
            robot_state_publisher,
            spawn_entity,
            chain_jsb_after_spawn,
            chain_arm_after_jsb,
        ]
    )
