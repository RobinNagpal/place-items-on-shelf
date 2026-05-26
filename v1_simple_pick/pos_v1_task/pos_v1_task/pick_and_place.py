"""Open-loop pick-and-place demo for place-items-on-shelf v1.

Timing is sim-time based (the node sets ``use_sim_time=True`` so
``node.get_clock().now()`` reads from ``/clock``). On WSL2 + Iris Xe Gazebo
typically runs at 40-60% real-time factor, so a wall-clock-based version of
this script would only cover ~half the intended distance before the timer
expired. Using sim time means "drive 7.5 s at 0.2 m/s" reliably moves the
robot ~1.5 m regardless of how slowly Gazebo is grinding.

Future versions will replace this open-loop timer with odometry feedback
(drive until /odom reports we've traveled N metres).
"""

import rclpy
from rclpy.duration import Duration
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist


# ----------------------------------------------------------------------------
# Tunables — all durations are in SIM seconds.
# ----------------------------------------------------------------------------
DRIVE_SPEED = 0.2          # linear m/s (forward and backward)
DRIVE_TIME_S = 7.5         # sim-seconds to drive (≈ 1.5 m at 0.2 m/s)
PICK_PAUSE_S = 3.0         # pretend-pick duration at shelf
PLACE_PAUSE_S = 1.0        # pretend-place duration at start
STARTUP_DELAY_S = 2.0      # let Gazebo + bridge settle before commanding motion
PUBLISH_PERIOD_S = 0.05    # how often we re-publish cmd_vel + spin for /clock


def wait_sim_seconds(node, duration_s):
    """Block until ``duration_s`` SIMULATED seconds have elapsed."""
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)


def drive(node, pub, linear_x, duration_s):
    """Publish a constant Twist for ``duration_s`` SIMULATED seconds, then stop."""
    cmd = Twist()
    cmd.linear.x = linear_x
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)
    pub.publish(Twist())  # explicit stop


def main():
    rclpy.init()
    # use_sim_time=True so get_clock() reads from /clock (published by Gazebo
    # via the ros_gz_bridge in pos_v1_bringup/config/gz_bridge.yaml).
    node = rclpy.create_node(
        'pick_and_place',
        parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)],
        automatically_declare_parameters_from_overrides=True,
    )
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    logger = node.get_logger()

    logger.info(f'Waiting {STARTUP_DELAY_S:.1f}s (sim) for sim to settle ...')
    wait_sim_seconds(node, STARTUP_DELAY_S)

    logger.info('STAGE 1: driving forward to shelf')
    drive(node, pub, +DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  (stopped after {DRIVE_TIME_S:.1f}s sim @ +{DRIVE_SPEED:.2f} m/s)')

    logger.info(f'STAGE 2: at shelf — simulated PICK for {PICK_PAUSE_S:.1f}s')
    wait_sim_seconds(node, PICK_PAUSE_S)

    logger.info('STAGE 3: driving back to start')
    drive(node, pub, -DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  (stopped after {DRIVE_TIME_S:.1f}s sim @ -{DRIVE_SPEED:.2f} m/s)')

    logger.info(f'STAGE 4: at start — simulated PLACE for {PLACE_PAUSE_S:.1f}s')
    wait_sim_seconds(node, PLACE_PAUSE_S)

    logger.info('Done.')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
