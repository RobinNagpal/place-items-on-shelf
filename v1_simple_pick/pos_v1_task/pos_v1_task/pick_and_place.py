"""Open-loop pick-and-place demo for place-items-on-shelf v1.

The node publishes Twist commands to /cmd_vel to drive the simulated robot:

  startup pause → forward to shelf → "pick" pause → back to start → "place" pause → done.

No feedback, no perception, no planning. Future versions replace each stage
with the real subsystem (Nav2, MoveIt, OpenCV, ...).
"""

import time

import rclpy
from geometry_msgs.msg import Twist


# ----------------------------------------------------------------------------
# Tunables — adjust if the robot under/overshoots in your simulation.
# ----------------------------------------------------------------------------
DRIVE_SPEED = 0.2          # linear m/s (forward and backward)
DRIVE_TIME_S = 7.5         # seconds to drive forward (and back).
                           # At 0.2 m/s this covers ~1.5 m; shelf is at x=2.0
                           # and robot starts at x=0.0 with body half-length ~0.25,
                           # so stopping at x~1.5 leaves ~0.25 m to the shelf face.
PICK_PAUSE_S = 3.0         # pretend-pick duration at shelf
PLACE_PAUSE_S = 1.0        # pretend-place duration at start
STARTUP_DELAY_S = 2.0      # let Gazebo + bridge come up before commanding motion
PUBLISH_PERIOD_S = 0.05    # how often we re-publish cmd_vel during a drive phase


def drive(pub, logger, linear_x, duration_s):
    """Publish a constant Twist for `duration_s` seconds, then stop."""
    cmd = Twist()
    cmd.linear.x = linear_x
    t0 = time.monotonic()
    while time.monotonic() - t0 < duration_s:
        pub.publish(cmd)
        time.sleep(PUBLISH_PERIOD_S)
    pub.publish(Twist())  # stop
    logger.info(f'  (stopped after {duration_s:.1f}s @ {linear_x:+.2f} m/s)')


def main():
    rclpy.init()
    node = rclpy.create_node('pick_and_place')
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    logger = node.get_logger()

    logger.info(f'Waiting {STARTUP_DELAY_S:.1f}s for sim to settle ...')
    time.sleep(STARTUP_DELAY_S)

    logger.info('STAGE 1: driving forward to shelf')
    drive(pub, logger, +DRIVE_SPEED, DRIVE_TIME_S)

    logger.info(f'STAGE 2: at shelf — simulated PICK for {PICK_PAUSE_S:.1f}s')
    time.sleep(PICK_PAUSE_S)

    logger.info('STAGE 3: driving back to start')
    drive(pub, logger, -DRIVE_SPEED, DRIVE_TIME_S)

    logger.info(f'STAGE 4: at start — simulated PLACE for {PLACE_PAUSE_S:.1f}s')
    time.sleep(PLACE_PAUSE_S)

    logger.info('Done.')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
