"""Launch the v2 backroom world + robot + slam_toolbox (+ RViz).

This is the "build a map" launch. Workflow:
  1. Run this launch.
  2. In another terminal, run teleop_twist_keyboard and drive the robot
     slowly around the backroom until the map looks complete in RViz.
  3. Save the map with:
        ros2 run nav2_map_server map_saver_cli -f \\
            install/pos_v2_navigation/share/pos_v2_navigation/maps/backroom
     (or save into the source tree under v2/pos_v2_navigation/maps/ and
     rebuild — see maps/README.md).

Toggle RViz with `rviz:=false` if you only want the headless mapping
process (e.g. while saving the map).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_navigation = get_package_share_directory('pos_v2_navigation')
    pkg_description = get_package_share_directory('pos_v2_description')

    slam_params = os.path.join(pkg_navigation, 'config', 'slam_toolbox_async.yaml')
    rviz_config = os.path.join(pkg_navigation, 'config', 'slam.rviz')

    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Whether to launch RViz with the SLAM preset',
    )

    spawn_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_description, 'launch', 'spawn_robot.launch.py')
        ),
    )

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params, {'use_sim_time': True}],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen',
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        rviz_arg,
        spawn_robot,
        slam,
        rviz,
    ])
