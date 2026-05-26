"""Mobile-manipulator pick-and-place demo for place-items-on-shelf v1 (Tier 2).

Architecture (changed since previous version):

* Arm + gripper are driven by ros2_control via gz_ros2_control. We publish
  trajectory_msgs/JointTrajectory to /arm_controller/joint_trajectory and
  /gripper_controller/joint_trajectory; joint_trajectory_controller with
  EFFORT command interface (PID gains in controllers.yaml) does the rest.
* Arm joint angles are computed by ANALYTICAL inverse kinematics
  (see ik.py) from world-frame Cartesian targets, instead of hand-tuned
  POSE_* constants.
* Grasp is FRICTION-BASED: we command the fingers to a position INSIDE
  the can (overshoot). The joint can't physically reach the target
  because the can is in the way; the trajectory controller's PID
  saturates its effort on that joint and the result is a sustained
  squeeze force on the can. With high finger/can friction (mu=2.0,1.2)
  that's plenty to hold a 355 g object. No DetachableJoint, no
  set_pose teleport hack.

Sequence (place-at-shelf flow — set up for future multi-pick):
  INIT -> wait for controllers, stow arm + open gripper
  S1   -> drive forward 1.5 m
  S2   -> IK to pre-grasp pose (6 cm above can, gripper horizontal)
  S3   -> IK to grasp pose (gripper at can centre)
  S4   -> close gripper (command 0.018; can blocks at 0.033 -> squeeze)
  S5   -> IK to lift pose (15 cm above shelf, gripper horizontal)
  S6   -> IK to carry pose (50 cm world height — well above the shelf
          so the arm can fold back to the tray without the gripper
          clipping the shelf during the joint-space interpolation)
  S7   -> IK to place pose (8 mm above tray top, robot still at shelf)
  S8   -> open gripper -> can drops a few mm onto tray
  S9   -> stow arm (so the arm clears the shelf during drive-back)
  S10  -> drive back 1.5 m (can rides freely on the tray, held by
          friction)
"""

import rclpy
from rclpy.duration import Duration
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration as RosDuration

from pos_v1_task.ik import ik_solve, shoulder_frame, IKError


# ============================================================================
# Tunables — durations sim-s, distances metres, angles radians.
# ============================================================================
DRIVE_SPEED = 0.2
DRIVE_TIME_S = 7.5             # 1.5 m at 0.2 m/s
STARTUP_DELAY_S = 5.0          # let controllers load + sim settle
ARM_MOVE_TIME_S = 3.0          # sim-s for each arm-trajectory point
GRIPPER_CLOSE_TIME_S = 1.5
GRIPPER_OPEN_TIME_S = 1.5     # slow open so the squeeze releases gently
                              # (sudden release shoves the can sideways)
SETTLE_S = 0.5                 # post-motion pause
PUBLISH_PERIOD_S = 0.05

# ---- Target object (from store.sdf) ----
CAN_X = 1.88
CAN_Z = 0.5865     # can centre height (shelf top 0.525 + half can 0.0615)
CAN_TOP_Z = 0.648  # shelf top + can height

# ---- Gripper orientations ----
PHI_HORIZONTAL = 0.0       # gripper pointing forward — fingers vertical,
                           # can held vertically between them

# ---- Arm targets ----
# Above-can poses are world-frame (the can sits at a known world pose).
PRE_GRASP_WORLD = (CAN_X, CAN_Z + 0.06, PHI_HORIZONTAL)
GRASP_WORLD     = (CAN_X, CAN_Z,        PHI_HORIZONTAL)
LIFT_WORLD      = (CAN_X, CAN_Z + 0.15, PHI_HORIZONTAL)

# Carry / place poses are ROBOT-FRAME (x relative to base_link, z is world).
# We add the current robot_x at command time so they track the robot.
#   tray extends x_robot ∈ [-0.225, 0.225]; top at world z = 0.185.
#   gripper x_robot = +0.20 keeps the gripper near the front of the tray
#   (this also keeps the wrist angle inside its ±2.0 rad limit).
# CARRY is held higher than the shelf top (0.525) so the LIFT→CARRY
# joint-space interpolation doesn't sweep the gripper through the shelf
# while folding back.
# PLACE is high enough that the can BOTTOM (z = z_target - 0.0615) stays
# above the tray top (0.185) -- otherwise the can gets pressed into the
# tray collision and shoots out when the gripper releases.
CARRY_ROBOT_XZ = (0.20, 0.50)      # gripper ~33 cm above tray top
PLACE_ROBOT_XZ = (0.20, 0.27)      # can bottom ≈ 8 mm above tray top
                                    # (0.27 − 0.0615 ≈ 0.208 > 0.185)

# ---- Stow pose (hand-picked: arm folded back over the column) ----
STOW_ANGLES = (-1.30, 2.20, 0.00)   # (shoulder, elbow, wrist)

# ---- Gripper finger positions (per-finger offset from centreline, metres) ----
GRIPPER_OPEN  = 0.045   # fully open (90 mm fingertip gap)
GRIPPER_GRASP = 0.018   # OVERSHOOT inside the can (33 mm radius)
                        # -> joint blocks at ~0.033, PID applies squeeze

ARM_JOINTS = ['arm_shoulder_joint', 'arm_elbow_joint', 'arm_wrist_joint']
GRIPPER_JOINTS = ['left_finger_joint', 'right_finger_joint']


# ============================================================================
def make_traj_msg(joint_names, positions, time_from_start_s):
    msg = JointTrajectory()
    msg.joint_names = list(joint_names)
    pt = JointTrajectoryPoint()
    pt.positions = [float(p) for p in positions]
    pt.velocities = [0.0] * len(positions)
    sec = int(time_from_start_s)
    nsec = int((time_from_start_s - sec) * 1e9)
    pt.time_from_start = RosDuration(sec=sec, nanosec=nsec)
    msg.points.append(pt)
    return msg


def wait_sim_seconds(node, duration_s):
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)


def drive(node, pub, linear_x, duration_s):
    cmd = Twist()
    cmd.linear.x = linear_x
    clock = node.get_clock()
    target = clock.now() + Duration(seconds=duration_s)
    while clock.now() < target:
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)
    pub.publish(Twist())


class PickAndPlace:
    def __init__(self, node):
        self.node = node
        self.logger = node.get_logger()
        self.cmd_vel = node.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_arm = node.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10
        )
        self.pub_gripper = node.create_publisher(
            JointTrajectory, '/gripper_controller/joint_trajectory', 10
        )
        self.robot_x = 0.0
        node.create_subscription(Odometry, '/odom', self._on_odom, 10)

    def _on_odom(self, msg):
        self.robot_x = msg.pose.pose.position.x

    # ---- arm helpers ----
    def send_arm_angles(self, s, e, w, time_s=ARM_MOVE_TIME_S):
        self.pub_arm.publish(make_traj_msg(ARM_JOINTS, [s, e, w], time_s))

    def move_arm_to_world(self, x_world, z_world, phi, time_s=ARM_MOVE_TIME_S):
        """Solve IK from a world-frame target and command the arm."""
        sx, sz = shoulder_frame(x_world, z_world, self.robot_x)
        try:
            s, e, w = ik_solve(sx, sz, phi, elbow_up=True)
        except IKError as exc:
            self.logger.error(f'IK failed: {exc}')
            raise
        self.logger.info(
            f'  IK target_world=({x_world:.3f},{z_world:.3f},phi={phi:+.3f}) '
            f'shoulder=({sx:+.3f},{sz:+.3f}) -> S={s:+.3f} E={e:+.3f} W={w:+.3f}'
        )
        self.send_arm_angles(s, e, w, time_s)

    def move_arm_to_robot_xz(self, x_robot, z_world, phi, time_s=ARM_MOVE_TIME_S):
        """Move arm so the gripper is at (robot_x + x_robot, z_world) in world."""
        self.move_arm_to_world(self.robot_x + x_robot, z_world, phi, time_s)

    # ---- gripper helpers ----
    def send_gripper(self, offset, time_s=GRIPPER_CLOSE_TIME_S):
        self.pub_gripper.publish(
            make_traj_msg(GRIPPER_JOINTS, [offset, offset], time_s)
        )


def main():
    rclpy.init()
    node = rclpy.create_node(
        'pick_and_place',
        parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)],
        automatically_declare_parameters_from_overrides=True,
    )
    pp = PickAndPlace(node)
    logger = pp.logger

    # ---- INIT ----
    logger.info(f'INIT: waiting {STARTUP_DELAY_S:.1f}s (sim) for controllers + sim')
    wait_sim_seconds(node, STARTUP_DELAY_S)
    pp.send_arm_angles(*STOW_ANGLES, time_s=2.0)
    pp.send_gripper(GRIPPER_OPEN, time_s=GRIPPER_OPEN_TIME_S)
    wait_sim_seconds(node, 2.5)

    # ---- STAGE 1: drive forward ----
    logger.info('STAGE 1: driving forward to shelf')
    drive(node, pp.cmd_vel, +DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  stopped at robot x ≈ {pp.robot_x:.2f}')
    wait_sim_seconds(node, SETTLE_S)

    # ---- STAGE 2: pre-grasp ----
    logger.info('STAGE 2: pre-grasp pose (above can)')
    pp.move_arm_to_world(*PRE_GRASP_WORLD)
    wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

    # ---- STAGE 3: grasp pose ----
    logger.info('STAGE 3: grasp pose (gripper at can centre)')
    pp.move_arm_to_world(*GRASP_WORLD)
    wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

    # ---- STAGE 4: close gripper (friction grasp) ----
    logger.info(f'STAGE 4: closing gripper (target {GRIPPER_GRASP:.3f} — overshoots can radius)')
    pp.send_gripper(GRIPPER_GRASP)
    wait_sim_seconds(node, GRIPPER_CLOSE_TIME_S + SETTLE_S)

    # ---- STAGE 5: lift can clear of shelf ----
    logger.info('STAGE 5: lift pose')
    pp.move_arm_to_world(*LIFT_WORLD)
    wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

    # ---- STAGE 6: carry pose — fold arm back over the tray.  Robot is
    # still AT THE SHELF; this just rotates the arm-with-can backwards
    # so the gripper is now above the tray. Gripper stays horizontal so
    # the can stays vertical between the finger pads.
    logger.info('STAGE 6: carry pose (fold arm back, above tray)')
    pp.move_arm_to_robot_xz(CARRY_ROBOT_XZ[0], CARRY_ROBOT_XZ[1], PHI_HORIZONTAL)
    wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

    # ---- STAGE 7: place pose — lower the can to just above the tray.
    # PLACE z is chosen so the can BOTTOM clears the tray top by ~8 mm;
    # if the can collides with the tray while still held, the release
    # in S8 will fling it sideways ("throws toward shelf").
    logger.info('STAGE 7: place pose (just above tray, robot still at shelf)')
    pp.move_arm_to_robot_xz(PLACE_ROBOT_XZ[0], PLACE_ROBOT_XZ[1], PHI_HORIZONTAL)
    wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

    # ---- STAGE 8: open gripper — can drops a few mm onto the tray.
    # Slow open (1.5 s) so the saturated squeeze releases gradually
    # rather than springing the can outward.
    logger.info('STAGE 8: opening gripper — can drops onto tray')
    pp.send_gripper(GRIPPER_OPEN, time_s=GRIPPER_OPEN_TIME_S)
    wait_sim_seconds(node, GRIPPER_OPEN_TIME_S + 1.0)

    # ---- STAGE 9: stow arm BEFORE driving — folds it back so it doesn't
    # clip the shelf on the way out, and so the gripper isn't hovering
    # over the can if it bounces.
    logger.info('STAGE 9: stowing arm (clear shelf for drive-back)')
    pp.send_arm_angles(*STOW_ANGLES, time_s=ARM_MOVE_TIME_S)
    wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

    # ---- STAGE 10: drive back to start. Can rides on the tray, held
    # by friction (mu=1.2 on can vs. default tray mu). For this v1 the
    # acceleration profile of gz-sim DiffDrive is gentle enough that
    # the can doesn't slide. ----
    logger.info('STAGE 10: driving back to start (can rides on tray)')
    drive(node, pp.cmd_vel, -DRIVE_SPEED, DRIVE_TIME_S)
    logger.info(f'  stopped at robot x ≈ {pp.robot_x:.2f}')
    wait_sim_seconds(node, SETTLE_S)

    logger.info('Done.')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
