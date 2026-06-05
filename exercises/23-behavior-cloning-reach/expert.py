"""Analytical expert that stands in for a human teleoperator.

A human pushing a gamepad to drive the arm toward a target would produce
smooth, target-seeking joint velocities. We synthesise the same thing
using the Jacobian pseudo-inverse and a P controller on the TCP error.
The behavior-cloning model never sees this formula — it only sees the
(state, action) pairs it produces.
"""

from __future__ import annotations

import numpy as np

from arm_2link import ArmState, forward_kinematics, jacobian


MAX_JOINT_SPEED = 2.0  # rad/s; mirrors a typical teleop speed cap
GAIN = 4.0             # P gain on TCP error in m -> rad/s


def expert_action(state: ArmState, target_xy: np.ndarray) -> np.ndarray:
    """Return joint velocities that step the TCP toward target_xy."""
    tcp = forward_kinematics(state)
    error = target_xy - tcp
    j = jacobian(state)
    # Damped least squares pseudo-inverse — survives near-singular poses.
    damping = 1e-3
    jt = j.T
    inv = np.linalg.inv(j @ jt + damping * np.eye(2))
    dq = jt @ inv @ (GAIN * error)
    # Clip per-joint to a sane teleop speed.
    return np.clip(dq, -MAX_JOINT_SPEED, MAX_JOINT_SPEED)
