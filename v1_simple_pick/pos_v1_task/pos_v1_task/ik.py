"""Analytical inverse kinematics for the 3-DOF planar arm.

Arm model (all joint axes are Y):

    shoulder ── a1 ── elbow ── a2 ── wrist ── a3 ── end-effector
                                                    (grasp centre)

Lengths come from the URDF (`pos_v1_description/urdf/pos_robot.urdf`):

    a1 = 0.25   (shoulder link)
    a2 = 0.20   (elbow link)
    a3 = 0.13   (wrist joint -> grasp centre = 0.05 wrist link
                                              + 0.05 gripper_base
                                              + 0.03 finger half-length)

The shoulder joint sits at world (R_x - 0.15, 0, 0.600) when the robot
is at world x = R_x and resting on its wheels — the arm column is
mounted at base_link x = -0.15 and extends 0.40 m up from base top
z = 0.20 (base_link world z = 0.125 at rest, see explanation below).

`ik_solve(x, z, phi)` returns (S, E, W) joint angles such that the
end-effector reaches `(x, z)` in the shoulder frame (NOT world frame)
with the last link pointing at angle `phi` from the +X axis. The caller
is responsible for the world->shoulder-frame transform — typically
``x_shoulder = x_world - (R_x - 0.15)`` and ``z_shoulder = z_world - 0.600``.
"""

import math


# Link lengths (metres). Keep in sync with the URDF.
A1 = 0.25
A2 = 0.20
A3 = 0.13

# Shoulder position in robot (base_link) frame.
# Column root at base_link (-0.15, 0, 0.075), column length 0.40,
# shoulder joint sits at column top.
SHOULDER_X_IN_BASE = -0.15
SHOULDER_Z_IN_BASE = 0.075 + 0.40    # = 0.475

# Settled base_link world z. The wheel bottoms sit 0.125 m below the
# base_link origin (wheel joint z=-0.075 + wheel radius 0.05), so when
# the robot is at rest with wheel bottoms on the ground, base_link's
# origin is at world z = 0.125. (Spawn z in the launch file is 0.15 —
# the extra 0.025 m is just so the robot doesn't spawn with its wheels
# clipping the ground.)
ROBOT_BASE_Z_AT_REST = 0.125

SHOULDER_Z_WORLD = ROBOT_BASE_Z_AT_REST + SHOULDER_Z_IN_BASE   # = 0.600


class IKError(ValueError):
    """Raised when a target is unreachable or geometrically singular."""


def shoulder_frame(x_world, z_world, robot_x):
    """Convert a (world x, world z) target to the shoulder's local (x, z).

    The shoulder is at world (robot_x + SHOULDER_X_IN_BASE, SHOULDER_Z_WORLD).
    """
    return (x_world - (robot_x + SHOULDER_X_IN_BASE),
            z_world - SHOULDER_Z_WORLD)


def ik_solve(x, z, phi=0.0, elbow_up=True):
    """Return (shoulder, elbow, wrist) joint angles in radians.

    Args:
      x, z: target end-effector position in the shoulder frame (metres).
      phi:  desired end-effector orientation in radians (angle of the
            last link with the +X axis).  phi=0  -> gripper horizontal
            forward; phi=-pi/2 -> gripper pointing down.
      elbow_up: True for the "elbow above the shoulder-to-wrist line"
                configuration (the natural one for top-down reaching).

    Raises IKError if the target is out of reach.
    """
    # Step 1: subtract the last link to find the wrist joint position.
    wx = x - A3 * math.cos(phi)
    wz = z - A3 * math.sin(phi)

    d2 = wx * wx + wz * wz
    d = math.sqrt(d2)

    if d > A1 + A2 + 1e-6:
        raise IKError(
            f'Target ({x:.3f}, {z:.3f}) phi={phi:.3f} out of reach: '
            f'd={d:.3f} > a1+a2={A1 + A2:.3f}'
        )
    if d < abs(A1 - A2) - 1e-6:
        raise IKError(
            f'Target ({x:.3f}, {z:.3f}) phi={phi:.3f} too close: '
            f'd={d:.3f} < |a1-a2|={abs(A1 - A2):.3f}'
        )

    # Step 2: law-of-cosines for the elbow angle.
    cos_e = (d2 - A1 * A1 - A2 * A2) / (2.0 * A1 * A2)
    cos_e = max(-1.0, min(1.0, cos_e))
    e = math.acos(cos_e)
    if elbow_up:
        e = -e                                            # bend elbow upward

    # Step 3: shoulder angle from the 2-link geometry.
    s = math.atan2(wz, wx) - math.atan2(A2 * math.sin(e), A1 + A2 * math.cos(e))

    # Step 4: wrist absorbs whatever angle is left to satisfy phi.
    w = phi - s - e

    return (s, e, w)


def fk(s, e, w):
    """Forward kinematics — handy for unit-testing / debug.

    Returns the end-effector position (x, z) in the shoulder frame.
    """
    x1, z1 = A1 * math.cos(s),         A1 * math.sin(s)
    x2 = x1 + A2 * math.cos(s + e)
    z2 = z1 + A2 * math.sin(s + e)
    x3 = x2 + A3 * math.cos(s + e + w)
    z3 = z2 + A3 * math.sin(s + e + w)
    return (x3, z3)


if __name__ == '__main__':
    # Quick smoke test: pick a few targets, solve, verify with FK.
    for x, z, phi in [
        (0.40,  0.10, 0.0),
        (0.50,  0.05, 0.0),
        (0.15, -0.20, -math.pi / 2),
        (0.20, -0.10, -math.pi / 2),
    ]:
        s, e, w = ik_solve(x, z, phi)
        x_back, z_back = fk(s, e, w)
        print(f'target=({x:.3f},{z:.3f},phi={phi:+.3f})  '
              f'-> S={s:+.3f} E={e:+.3f} W={w:+.3f}  '
              f'fk=({x_back:+.3f},{z_back:+.3f})')
