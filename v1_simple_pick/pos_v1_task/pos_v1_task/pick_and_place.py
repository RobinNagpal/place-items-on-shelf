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
  squeeze force on the can. With high finger/can friction (mu=3.0,1.6)
  that's plenty to hold a 355 g object. No DetachableJoint, no
  set_pose teleport hack.
* Base drive uses CLOSED-LOOP odometry feedback (`drive_to_x`) with a
  bounded-acceleration trapezoidal profile. Earlier the drive was
  open-loop time-based — but with even small wheel slip the robot
  under-shot by 5-15 cm, leaving the can outside arm reach. Now the
  drive ramps up to cruise speed, then decelerates based on remaining
  distance from /odom, stopping exactly where the IK expects.

Sequence:
  INIT -> wait for controllers, stow arm + open gripper
  S1   -> drive forward 1.5 m (ramped)
  S2   -> IK to pre-grasp pose (6 cm above can, gripper horizontal)
  S3   -> IK to grasp pose (gripper at can centre)
  S4   -> close gripper (command 0.012; can blocks at 0.033 -> squeeze)
  S5   -> IK to lift pose (15 cm above shelf, gripper horizontal)
  S6   -> IK to carry pose (above tray front, gripper still horizontal so
          the can stays vertical between the finger pads)
  S7   -> drive back 1.5 m (ramped, still carrying)
  S8   -> IK to place pose (just above tray top)
  S9   -> open gripper -> can drops onto tray
  S10  -> stow arm
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
DRIVE_SPEED = 0.12             # was 0.20 — slower cruise so the inertia
                               # spike on the can at start-of-drive is
                               # smaller (the friction grasp couldn't hold
                               # at 0.20 m/s, the can slipped forward).
DRIVE_ACCEL = 0.10             # m/s^2 — linear velocity ramp magnitude
                               # for start-of-drive and end-of-drive. Limits
                               # the impulse the can has to resist.

# Closed-loop drive targets (world x). The previous version drove for a
# fixed time and trusted v*t to give the distance — but with even small
# wheel slip the robot under-shot by ~5-15 cm, leaving the can outside
# arm reach (arm max reach = 0.58 m; can horizontal from shoulder at
# robot_x=1.40 is 0.63 m — unreachable). drive_to_x() below uses odom
# feedback to stop at the target x exactly.
APPROACH_X = 1.54              # robot_x to stop at when approaching shelf.
                               # Why 1.54 and not "further from the shelf":
                               #   base half-length X = 0.25, so robot's front
                               #   face at x_world = APPROACH_X + 0.25 = 1.79.
                               #   Shelf front at 1.80 -> 1 cm clearance, as
                               #   close as is safe without the base touching.
                               # Why "as close as possible" matters:
                               #   shoulder world x = APPROACH_X - 0.15 = 1.39.
                               #   Can world x = 1.88. Horizontal shoulder->can
                               #   distance 0.49 m. Arm max end-effector reach
                               #   A1+A2+A3 = 0.58 m -> 9 cm margin.
                               # The previous value (1.52) left only 5 cm of
                               # reach margin, and combined with the closed-loop
                               # tolerance below the robot was stopping 1-2 cm
                               # SHORT of target, so by STAGE 3 the wrist was
                               # at 89% of A1+A2, the arm couldn't take up the
                               # last bit under gravity sag, and the gripper
                               # came up ~3 cm short of the can. Visible
                               # symptom: "robot's hand has a gap to the can,
                               # so it never grips it." Closing this margin
                               # (and shrinking the tolerance) fixes that.
HOME_X = 0.0                   # robot_x to stop at when returning home.

STARTUP_DELAY_S = 5.0          # let controllers load + sim settle
ARM_MOVE_TIME_S = 3.0          # sim-s for each arm-trajectory point
GRIPPER_CLOSE_TIME_S = 2.5     # was 1.5 — give the effort PID enough time
                               # to fully build the squeeze force against
                               # the cube's flat side before STAGE 5 lifts.
                               # User report: the lift was starting before
                               # the grasp had finished, so the cube fell
                               # out of the gripper.
GRIPPER_OPEN_TIME_S = 0.8
SETTLE_S = 1.0                 # post-motion pause. Bumped from 0.5 -> 1.0
                               # so each pose holds long enough to settle
                               # fully (most relevant after STAGE 4 close
                               # gripper, but applies to every stage).
PUBLISH_PERIOD_S = 0.05

# ---- Target object (from store.sdf) ----
# It is a 6 cm cube now, not a soda can. See store.sdf for the full
# why; short version: parallel-jaw grippers grip flat-on-flat way more
# reliably than they grip cylinders, and the cube is wide enough in X
# that the gripper has 3 cm of tolerance on the GRASP target.
CAN_X = 1.85       # cube centre X (world)
CAN_Z = 0.555      # cube centre Z (shelf top 0.525 + half cube 0.030)
CAN_TOP_Z = 0.585  # shelf top + cube height (= 0.525 + 0.060)

# ---- Gripper orientations ----
PHI_HORIZONTAL = 0.0       # gripper pointing forward — fingers vertical,
                           # can held vertically between them

# ---- Arm targets ----
# X offset on the GRASP target relative to the can centre. NEGATIVE here
# (pull the gripper centre BEHIND the can centre) — the reason is that
# the IK targets the pad-centre, but the GRIPPER BASE (the 5 cm × 6 cm
# palm block between the wrist and the fingers) sits 3 cm BEHIND the
# pad-centre. With pad-centre at can-centre (offset = 0) the gripper
# base front face is at can_back + 3 mm — barely poking inside the
# can's collision volume. With the previous +0.04 offset the base
# front was 4 cm INSIDE the can and physically pushed it off the shelf
# before the fingers even closed (that was the screenshot of the can
# lying on its side). With -0.01 here, gripper-base front sits 7 mm
# CLEAR of can-back. The pads (6 cm long in X) still cover the can
# from x ∈ [1.81, 1.87] vs can ∈ [1.817, 1.883] → 5.3 cm overlap —
# plenty for the friction grasp.
GRASP_X_OFFSET = -0.01

# Z target for the pre-grasp pose. Raised from CAN_Z + 0.06 (= 0.6465,
# i.e. only 1.5 mm below the can top) to a height that is WELL ABOVE
# the can top. The previous low pre-grasp made the joint-space
# trajectory from STOW to PRE_GRASP arc through the can's collision
# volume at the midpoint (gripper-base z ≈ 0.65 → exactly can-top
# height while still inside the can's x range). Approaching from
# z = 0.85 means the gripper-base midpoint sits 4.5 cm above the can
# top — completely clear — and only the descent PRE_GRASP → GRASP
# brings the gripper down to grasp height, by which point the base
# x has settled BEHIND the can (no x-overlap during the descent).
PRE_GRASP_Z = 0.85

PRE_GRASP_WORLD = (CAN_X + GRASP_X_OFFSET, PRE_GRASP_Z,    PHI_HORIZONTAL)
GRASP_WORLD     = (CAN_X + GRASP_X_OFFSET, CAN_Z,          PHI_HORIZONTAL)
LIFT_WORLD      = (CAN_X + GRASP_X_OFFSET, CAN_Z + 0.15,   PHI_HORIZONTAL)

# Carry / place poses are ROBOT-FRAME (relative to base_link). We add the
# current robot_x at command time so they track the robot.
#
# Tray geometry (from URDF):
#   base_link rest world z       = 0.125  (wheel bottom 5 cm below base bottom)
#   tray_joint origin (in base)  = (0, 0, 0.08)
#   tray plate half-thickness    = 0.005
#   -> tray top world z          = 0.125 + 0.08 + 0.005 = 0.210
#   tray extends x_robot ∈ [-0.225, +0.225].
#
# CARRY pose: arm pulled BACK above the tray but STILL AT LIFT HEIGHT.
# The previous CARRY pose at z=0.30 had the gripper centre descend straight
# from LIFT z=0.7365 to z=0.30 while the robot was still parked at the
# shelf. Joint-space interpolation of that move swept the gripper (and
# the can held inside it) through z ≈ 0.49 at world x ≈ 1.87 — right
# through the shelf collision volume (shelf top z=0.525, shelf x ∈
# [1.80, 2.20]). The shelf either snagged the can or stalled the arm.
# Keeping CARRY at LIFT z means every point of the LIFT->CARRY arc stays
# above z=0.74, well clear of the shelf top. The actual descent over the
# tray happens AFTER drive-back, when the shelf is no longer in the way.
CARRY_ROBOT_XZ = (0.20, CAN_Z + 0.15)   # x near tray front, z = LIFT height

# PLACE pose: descend over the tray to a height where the can held in the
# gripper just clears the tray top before release.
#   pad centre at z = 0.29  ->  can centre at 0.29
#                            -> can bottom at 0.29 - 0.0615 = 0.2285
#                            -> clearance above tray top = 0.0185 = 1.85 cm
# The previous z=0.23 (with comment "4.5 cm above tray top") was computed
# against an incorrect tray-top estimate of 0.185 m. Actual tray top is
# 0.210, so z=0.23 would have put the can BOTTOM at 0.169 — 4 cm BELOW
# the tray surface. Gazebo would resolve that as the can being pushed
# back up by the tray, fighting the wrist PID, before the gripper opened.
PLACE_ROBOT_XZ = (0.20, 0.29)

# ---- Stow pose (hand-picked: arm folded back over the column) ----
STOW_ANGLES = (-1.30, 2.20, 0.00)   # (shoulder, elbow, wrist)

# ---- Gripper finger positions (per-finger offset from centreline, metres) ----
GRIPPER_OPEN  = 0.045   # fully open (90 mm fingertip gap)
GRIPPER_GRASP = 0.012   # OVERSHOOT inside the can (33 mm radius).
                        # Tightened 0.018 -> 0.012: bigger steady-state
                        # position error -> larger saturated squeeze
                        # effort from the PID -> more normal force ->
                        # more friction holding the can against inertia.

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


def drive_to_x(node, pub, get_x, target_x, max_speed, accel,
               timeout_s=45.0, tolerance=0.005):
    """Drive straight until odom reports robot x near target_x.

    Closed-loop trapezoidal velocity profile: accelerate to max_speed,
    cruise, then decelerate based on current odom remaining-distance,
    stop within `tolerance` metres of target_x.

    Replaces the previous time-based drive_ramped, which trusted
    v*t to give the distance. With even small wheel slip / dart
    integration drift the robot under-shot by several cm — enough to
    leave the can outside arm reach. Odom-based feedback closes the
    loop and stops exactly where the IK math expects.

    Direction is inferred from the sign of (target_x - current_x), so
    the SAME function handles the approach-shelf and the return-home
    legs.

    Acceleration is still bounded to `accel` so the friction grasp on
    the can isn't broken by an inertia spike at start-of-drive (this
    was the reason for the ramp in the first place).
    """
    clock = node.get_clock()
    start_x = get_x()
    sign = 1.0 if target_x >= start_x else -1.0
    speed = 0.0
    cmd = Twist()
    t_start = clock.now()
    last_t = t_start
    while (clock.now() - t_start) < Duration(seconds=timeout_s):
        now = clock.now()
        dt = (now - last_t).nanoseconds * 1e-9
        if dt <= 0.0:
            dt = PUBLISH_PERIOD_S
        last_t = now

        current_x = get_x()
        remaining = sign * (target_x - current_x)
        if remaining <= tolerance:
            break

        brake_dist = (speed * speed) / (2.0 * accel)
        if brake_dist + 0.5 * speed * dt >= remaining:
            speed = max(0.0, speed - accel * dt)
        elif speed < max_speed:
            speed = min(max_speed, speed + accel * dt)
        # else cruise at max_speed

        cmd.linear.x = sign * speed
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

    # ---- STAGE 1: drive forward (closed-loop on odom) ----
    logger.info(f'STAGE 1: driving forward until robot_x ≈ {APPROACH_X:.2f}')
    drive_to_x(node, pp.cmd_vel, lambda: pp.robot_x,
               APPROACH_X, DRIVE_SPEED, DRIVE_ACCEL)
    logger.info(f'  stopped at robot x ≈ {pp.robot_x:.2f}')
    wait_sim_seconds(node, SETTLE_S)

    # ---- STAGES 2-6: pick up the can. ----
    # Anything in this block can fail (IK error, can has fallen off the
    # shelf and isn't where we expect, controller goal aborted, ...).
    # Whatever happens, the robot MUST still drive back home in STAGE 7
    # so it doesn't get stranded at the shelf. We track grasp_ok and use
    # it to decide whether to run the place-on-tray stages later.
    grasp_ok = False
    try:
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

        # ---- STAGE 6: carry pose (above tray at LIFT height — clears shelf top) ----
        # NOT the previous "low carry" pose (z=0.30). That swept the can
        # through the shelf during joint-space interpolation. Holding at
        # LIFT height for the duration of drive-back keeps the gripper
        # safely above the shelf top throughout the transition; the actual
        # descent over the tray happens in STAGE 8 after we're home.
        logger.info('STAGE 6: carry pose (above tray, still at lift height)')
        pp.move_arm_to_robot_xz(CARRY_ROBOT_XZ[0], CARRY_ROBOT_XZ[1], PHI_HORIZONTAL)
        wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)

        grasp_ok = True
    except Exception as exc:
        logger.error(
            f'Pick-up sequence failed at some stage: {exc!r}. '
            f'Aborting pick, opening gripper, and continuing to drive-back '
            f'so the robot returns home.'
        )
        # Open the gripper and try to stow the arm so we don't drag
        # anything during the drive back. Best-effort — ignore failures here.
        try:
            pp.send_gripper(GRIPPER_OPEN, time_s=GRIPPER_OPEN_TIME_S)
            wait_sim_seconds(node, GRIPPER_OPEN_TIME_S + SETTLE_S)
            pp.send_arm_angles(*STOW_ANGLES, time_s=ARM_MOVE_TIME_S)
            wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)
        except Exception as cleanup_exc:
            logger.warning(f'Cleanup after failed pick also raised: {cleanup_exc!r}')

    # ---- STAGE 7: drive back (ALWAYS runs, even if pick-up failed). ----
    # Closed-loop on odom (drive_to_x infers direction from current vs
    # target). Bounded acceleration so the friction grasp on the can
    # isn't broken by an inertia spike at start-of-drive.
    logger.info(
        f'STAGE 7: driving back to robot_x ≈ {HOME_X:.2f} '
        f'({"carrying can" if grasp_ok else "no can — pick-up failed"})'
    )
    try:
        drive_to_x(node, pp.cmd_vel, lambda: pp.robot_x,
                   HOME_X, DRIVE_SPEED, DRIVE_ACCEL)
    except Exception as exc:
        logger.error(f'Drive-back failed: {exc!r}')
    logger.info(f'  stopped at robot x ≈ {pp.robot_x:.2f}')
    wait_sim_seconds(node, SETTLE_S)

    if grasp_ok:
        # ---- STAGE 8: lower arm to place pose ----
        logger.info('STAGE 8: place pose (just above tray)')
        try:
            pp.move_arm_to_robot_xz(PLACE_ROBOT_XZ[0], PLACE_ROBOT_XZ[1], PHI_HORIZONTAL)
            wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)
        except Exception as exc:
            logger.error(f'Place pose failed: {exc!r}')

        # ---- STAGE 9: open gripper -> can drops onto tray ----
        logger.info('STAGE 9: opening gripper — can drops onto tray')
        pp.send_gripper(GRIPPER_OPEN, time_s=GRIPPER_OPEN_TIME_S)
        wait_sim_seconds(node, GRIPPER_OPEN_TIME_S + 1.5)   # let it settle
    else:
        logger.info('STAGES 8-9 skipped — no can was grasped, nothing to place.')

    # ---- STAGE 10: stow ----
    logger.info('STAGE 10: stowing arm')
    try:
        pp.send_arm_angles(*STOW_ANGLES, time_s=ARM_MOVE_TIME_S)
        wait_sim_seconds(node, ARM_MOVE_TIME_S + SETTLE_S)
    except Exception as exc:
        logger.error(f'Stow failed: {exc!r}')

    logger.info(f'Done. Grasp success: {grasp_ok}.')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
