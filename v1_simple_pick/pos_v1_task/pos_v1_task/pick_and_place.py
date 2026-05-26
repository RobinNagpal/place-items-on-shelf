"""Mobile-manipulator pick-and-place demo for place-items-on-shelf v1.

The robot:
  1. Releases the initial pre-attached grasp joint (DetachableJoint in the
     URDF starts ATTACHED at world load — we detach so the can sits on the
     shelf normally).
  2. Drives forward to the shelf.
  3. Extends the 3-DOF arm to a pre-grasp pose above the can.
  4. Lowers the arm so the open gripper surrounds the can.
  5. Closes the parallel-jaw gripper around the can.
  6. Publishes /grasp/attach — the DetachableJoint re-forms at the current
     gripper-to-can offset, so the can rigidly follows the gripper.
  7. Lifts the arm and drives back to the start.
  8. Lowers the arm over the tray.
  9. Publishes /grasp/detach + opens the gripper — gravity drops the can
     onto the tray.
 10. Stows the arm.

All durations are sim-seconds (use_sim_time=True) so timing tracks Gazebo's
/clock and works correctly even on a slow RTF (WSL2 + Iris Xe runs at
~40-60% RTF).

Arm joint targets (POSE_*) are hand-tuned for the geometry in this folder
(robot stopping at world x ≈ 1.5, soda can at world (1.88, 0, 0.5865)). If
you change drive distance, can position, or link lengths, adjust them in
the constants block below.
"""

import rclpy
from rclpy.duration import Duration
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Empty, Float64


# ============================================================================
# Tunables
# ============================================================================
DRIVE_SPEED = 0.2           # m/s
DRIVE_TIME_S = 7.5          # 1.5 m forward (and back) at 0.2 m/s
STARTUP_DELAY_S = 3.0       # let Gazebo, controllers, and the initial
                            # detach settle before commanding motion
ARM_MOVE_TIME_S = 2.5       # sim-s allowed for arm to reach a new pose
GRIPPER_MOVE_TIME_S = 1.0   # sim-s for fingers to open/close
GRASP_SETTLE_S = 0.5        # sim-s after attach/detach
PUBLISH_PERIOD_S = 0.05

# ---- Arm poses: (shoulder, elbow, wrist) in radians ----
# At all-zeros the arm points horizontally forward at shoulder height
# (world z ≈ 0.575 when the robot is at its spawn z=0.1). Positive
# shoulder pitch raises the arm.
POSE_STOW       = (-1.30,  2.20,  0.00)   # arm folded back over the column
POSE_PRE_GRASP  = ( 0.10,  0.00,  0.00)   # arm extended, slightly raised
POSE_GRASP      = ( 0.02, -0.05,  0.00)   # gripper at can-grip height
POSE_LIFT       = ( 0.40, -0.30,  0.00)   # raised above shelf top
POSE_CARRY      = ( 1.10, -2.00,  0.80)   # folded up, gripper over tray
POSE_PLACE      = ( 0.55, -2.00,  1.15)   # arm angled down toward tray

# ---- Gripper finger offsets (per-finger, metres) ----
GRIPPER_OPEN   = 0.045   # ~90 mm between fingertips
GRIPPER_GRASP  = 0.032   # snug around 66 mm can diameter
GRIPPER_CLOSED = 0.005


# ============================================================================
def wait_sim_seconds(node, duration_s):
    """Block until ``duration_s`` SIMULATED seconds have elapsed."""
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)


def drive(node, pub, linear_x, duration_s):
    """Publish a constant Twist for ``duration_s`` SIM seconds, then stop."""
    cmd = Twist()
    cmd.linear.x = linear_x
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)
    pub.publish(Twist())


class PickAndPlace:
    """Holds publishers + state for the pick-and-place sequence."""

    def __init__(self, node):
        self.node = node
        self.logger = node.get_logger()

        self.cmd_vel = node.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_shoulder = node.create_publisher(Float64, '/arm/shoulder_cmd', 10)
        self.pub_elbow = node.create_publisher(Float64, '/arm/elbow_cmd', 10)
        self.pub_wrist = node.create_publisher(Float64, '/arm/wrist_cmd', 10)
        self.pub_left_finger = node.create_publisher(Float64, '/gripper/left_cmd', 10)
        self.pub_right_finger = node.create_publisher(Float64, '/gripper/right_cmd', 10)
        self.pub_attach = node.create_publisher(Empty, '/grasp/attach', 10)
        self.pub_detach = node.create_publisher(Empty, '/grasp/detach', 10)

        self.robot_x = 0.0
        node.create_subscription(Odometry, '/odom', self._on_odom, 10)

    def _on_odom(self, msg):
        self.robot_x = msg.pose.pose.position.x

    # ------ command helpers ----------------------------------------------
    def arm(self, pose):
        s, e, w = pose
        self.pub_shoulder.publish(Float64(data=float(s)))
        self.pub_elbow.publish(Float64(data=float(e)))
        self.pub_wrist.publish(Float64(data=float(w)))

    def gripper(self, offset):
        msg = Float64(data=float(offset))
        # Both fingers driven symmetrically; their joint axes are mirrored
        # in the URDF so the same positive value opens both.
        self.pub_left_finger.publish(msg)
        self.pub_right_finger.publish(msg)

    def grasp_attach(self):
        # Burst-publish to make sure the bridge has time to deliver.
        for _ in range(5):
            self.pub_attach.publish(Empty())
            rclpy.spin_once(self.node, timeout_sec=0.02)

    def grasp_detach(self):
        for _ in range(5):
            self.pub_detach.publish(Empty())
            rclpy.spin_once(self.node, timeout_sec=0.02)


def main():
    rclpy.init()
    # use_sim_time=True so get_clock() reads from /clock (published by
    # Gazebo via the ros_gz_bridge).
    node = rclpy.create_node(
        'pick_and_place',
        parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)],
        automatically_declare_parameters_from_overrides=True,
    )
    pp = PickAndPlace(node)
    logger = pp.logger

    # ---- INIT ----
    logger.info('INIT: detach pre-attached grasp joint so the can rests on the shelf')
    pp.grasp_detach()
    pp.arm(POSE_STOW)
    pp.gripper(GRIPPER_OPEN)
    logger.info(f'  waiting {STARTUP_DELAY_S:.1f}s (sim) for sim + controllers to settle')
    wait_sim_seconds(node, STARTUP_DELAY_S)

    # ---- STAGE 1: drive forward ----
    logger.info('STAGE 1: driving forward to shelf')
    drive(node, pp.cmd_vel, +DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  stopped at robot x ≈ {pp.robot_x:.2f}')

    # ---- STAGE 2: arm to pre-grasp (above the can) ----
    logger.info('STAGE 2: extending arm to pre-grasp pose (above can)')
    pp.arm(POSE_PRE_GRASP)
    wait_sim_seconds(node, ARM_MOVE_TIME_S)

    # ---- STAGE 3: lower arm to grasp pose ----
    logger.info('STAGE 3: lowering arm so gripper surrounds the can')
    pp.arm(POSE_GRASP)
    wait_sim_seconds(node, ARM_MOVE_TIME_S)

    # ---- STAGE 4: close gripper around can ----
    logger.info('STAGE 4: closing gripper around can')
    pp.gripper(GRIPPER_GRASP)
    wait_sim_seconds(node, GRIPPER_MOVE_TIME_S)

    # ---- STAGE 5: attach grasp joint ----
    logger.info('STAGE 5: attaching grasp joint (can rigidly follows gripper)')
    pp.grasp_attach()
    wait_sim_seconds(node, GRASP_SETTLE_S)

    # ---- STAGE 6: lift arm above shelf ----
    logger.info('STAGE 6: lifting arm above the shelf')
    pp.arm(POSE_LIFT)
    wait_sim_seconds(node, ARM_MOVE_TIME_S)

    # ---- STAGE 7: fold arm into carry pose over tray ----
    logger.info('STAGE 7: folding arm to carry pose')
    pp.arm(POSE_CARRY)
    wait_sim_seconds(node, ARM_MOVE_TIME_S)

    # ---- STAGE 8: drive back to start ----
    logger.info('STAGE 8: driving back to start (carrying can)')
    drive(node, pp.cmd_vel, -DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  stopped at robot x ≈ {pp.robot_x:.2f}')

    # ---- STAGE 9: lower arm over tray ----
    logger.info('STAGE 9: lowering arm over tray (place pose)')
    pp.arm(POSE_PLACE)
    wait_sim_seconds(node, ARM_MOVE_TIME_S)

    # ---- STAGE 10: release (detach + open gripper) ----
    logger.info('STAGE 10: detaching grasp joint + opening gripper — can drops onto tray')
    pp.grasp_detach()
    pp.gripper(GRIPPER_OPEN)
    wait_sim_seconds(node, GRIPPER_MOVE_TIME_S + GRASP_SETTLE_S)

    # ---- STAGE 11: stow ----
    logger.info('STAGE 11: stowing arm')
    pp.arm(POSE_STOW)
    wait_sim_seconds(node, ARM_MOVE_TIME_S)

    logger.info('Done.')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
