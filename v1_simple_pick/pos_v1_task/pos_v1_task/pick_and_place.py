"""Open-loop pick-and-place demo for place-items-on-shelf v1.

There is no real arm or gripper in v1 — the grasp is faked by teleporting
``bottle_1`` (the middle shelf bottle) onto the robot's tray and later down
to the ground next to the start. The teleport is done by calling Gazebo's
``/world/<world>/set_pose`` service via the ``gz`` CLI as a subprocess.
While the robot drives back the script re-snaps the bottle to the tray every
``CARRY_SYNC_PERIOD_S`` so it visually tracks the moving robot. A real grasp
(arm + ros2_control + fingers + detachable joint) lands in v2/v3.

Robot pose comes from /odom (DiffDrive wheel-encoder estimate). For a
straight forward/back drive on a flat floor that's accurate enough; odom and
world frame are aligned at spawn.

Timing is sim-time based (the node sets ``use_sim_time=True`` so
``node.get_clock().now()`` reads from ``/clock``). On WSL2 + Iris Xe Gazebo
typically runs at 40-60% real-time factor; using sim time means "drive 7.5 s
at 0.2 m/s" reliably moves the robot ~1.5 m regardless of how slowly Gazebo
is grinding.
"""

import subprocess

import rclpy
from rclpy.duration import Duration
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


# ----------------------------------------------------------------------------
# Tunables — all durations are in SIM seconds, all distances in metres.
# ----------------------------------------------------------------------------
DRIVE_SPEED = 0.2          # linear m/s (forward and backward)
DRIVE_TIME_S = 7.5         # sim-seconds to drive (≈ 1.5 m at 0.2 m/s)
PICK_PAUSE_S = 3.0         # pretend-pick duration at shelf
PLACE_PAUSE_S = 1.5        # post-place settle time
STARTUP_DELAY_S = 2.0      # let Gazebo + bridge settle before commanding motion
PUBLISH_PERIOD_S = 0.05    # how often we re-publish cmd_vel + spin for /clock

WORLD_NAME = 'store'
PICK_BOTTLE = 'bottle_1'           # middle bottle on the shelf
TRAY_Z_WORLD = 0.285               # tray top (~0.185) + bottle half-length (0.1)
PLACE_POSE_XY = (-0.5, 0.3)        # x, y where the bottle is dropped on return
PLACE_POSE_Z = 0.12                # spawn slightly above ground; gravity drops it
CARRY_SYNC_PERIOD_S = 0.5          # re-teleport bottle this often while carrying
GZ_TIMEOUT_MS = 300                # per gz service call


def gz_set_pose(name, x, y, z):
    """Teleport an entity in the current world via the ``gz service`` CLI."""
    req = (
        f'name: "{name}" '
        f'position {{ x: {x:.4f} y: {y:.4f} z: {z:.4f} }} '
        f'orientation {{ w: 1.0 }}'
    )
    try:
        subprocess.run(
            [
                'gz', 'service',
                '-s', f'/world/{WORLD_NAME}/set_pose',
                '--reqtype', 'gz.msgs.Pose',
                '--reptype', 'gz.msgs.Boolean',
                '--timeout', str(GZ_TIMEOUT_MS),
                '--req', req,
            ],
            check=False,
            capture_output=True,
            timeout=2.0,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


class CarryState:
    """Latest robot pose (from /odom) + throttled bottle-to-tray re-teleport."""

    def __init__(self, node):
        self._node = node
        self.robot_x = 0.0
        self.robot_y = 0.0
        node.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self._next_sync = None

    def _on_odom(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    def snap_now(self):
        """Force an immediate re-teleport (used at the start of PICK)."""
        gz_set_pose(PICK_BOTTLE, self.robot_x, self.robot_y, TRAY_Z_WORLD)
        self._next_sync = self._node.get_clock().now() + Duration(seconds=CARRY_SYNC_PERIOD_S)

    def sync_bottle_to_tray(self):
        """Spin-loop callback: re-snap at most every ``CARRY_SYNC_PERIOD_S``."""
        now = self._node.get_clock().now()
        if self._next_sync is None or now >= self._next_sync:
            gz_set_pose(PICK_BOTTLE, self.robot_x, self.robot_y, TRAY_Z_WORLD)
            self._next_sync = now + Duration(seconds=CARRY_SYNC_PERIOD_S)


def wait_sim_seconds(node, duration_s, on_tick=None):
    """Block until ``duration_s`` SIMULATED seconds have elapsed."""
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)
        if on_tick is not None:
            on_tick()


def drive(node, pub, linear_x, duration_s, on_tick=None):
    """Publish a constant Twist for ``duration_s`` SIMULATED seconds, then stop."""
    cmd = Twist()
    cmd.linear.x = linear_x
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)
        if on_tick is not None:
            on_tick()
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
    carry = CarryState(node)

    logger.info(f'Waiting {STARTUP_DELAY_S:.1f}s (sim) for sim to settle ...')
    wait_sim_seconds(node, STARTUP_DELAY_S)

    logger.info('STAGE 1: driving forward to shelf')
    drive(node, pub, +DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  (stopped after {DRIVE_TIME_S:.1f}s sim @ +{DRIVE_SPEED:.2f} m/s)')

    logger.info(f'STAGE 2: PICK — teleporting {PICK_BOTTLE} from shelf onto tray')
    carry.snap_now()
    wait_sim_seconds(node, PICK_PAUSE_S, on_tick=carry.sync_bottle_to_tray)

    logger.info('STAGE 3: driving back to start (carrying bottle)')
    drive(node, pub, -DRIVE_SPEED, DRIVE_TIME_S, on_tick=carry.sync_bottle_to_tray)
    logger.info(f'  (stopped after {DRIVE_TIME_S:.1f}s sim @ -{DRIVE_SPEED:.2f} m/s)')

    logger.info(
        f'STAGE 4: PLACE — dropping {PICK_BOTTLE} at '
        f'({PLACE_POSE_XY[0]:.2f}, {PLACE_POSE_XY[1]:.2f})'
    )
    gz_set_pose(PICK_BOTTLE, PLACE_POSE_XY[0], PLACE_POSE_XY[1], PLACE_POSE_Z)
    wait_sim_seconds(node, PLACE_PAUSE_S)

    logger.info('Done.')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
