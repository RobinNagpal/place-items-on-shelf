"""Tiny 2-link planar arm simulator.

Joint angles are radians. Lengths are metres. The arm is anchored at
the origin. Forward kinematics returns the tool-centre point (TCP)
in the (x, y) plane. The Jacobian maps joint velocity to TCP velocity.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


L1 = 0.10  # length of the first link in metres
L2 = 0.10  # length of the second link in metres


@dataclass
class ArmState:
    q1: float
    q2: float

    def as_vec(self) -> np.ndarray:
        return np.array([self.q1, self.q2], dtype=np.float64)


def forward_kinematics(state: ArmState) -> np.ndarray:
    """Return the TCP (x, y) in metres for a joint configuration."""
    x = L1 * np.cos(state.q1) + L2 * np.cos(state.q1 + state.q2)
    y = L1 * np.sin(state.q1) + L2 * np.sin(state.q1 + state.q2)
    return np.array([x, y], dtype=np.float64)


def jacobian(state: ArmState) -> np.ndarray:
    """2x2 Jacobian d(tcp)/d(q) at the given configuration."""
    s1 = np.sin(state.q1)
    c1 = np.cos(state.q1)
    s12 = np.sin(state.q1 + state.q2)
    c12 = np.cos(state.q1 + state.q2)
    return np.array(
        [
            [-L1 * s1 - L2 * s12, -L2 * s12],
            [L1 * c1 + L2 * c12, L2 * c12],
        ],
        dtype=np.float64,
    )


def step(state: ArmState, action: np.ndarray, dt: float = 0.05) -> ArmState:
    """Integrate one timestep. Action is joint velocity (rad/s)."""
    return ArmState(q1=state.q1 + action[0] * dt, q2=state.q2 + action[1] * dt)


def random_reachable_target(rng: np.random.Generator) -> np.ndarray:
    """Sample a target inside the dexterous workspace."""
    # The arm reaches from |L1 - L2| (=0) to L1 + L2 (=0.20). Stay away from
    # the singular extremes so the expert controller behaves nicely.
    r = rng.uniform(0.05, 0.18)
    theta = rng.uniform(-np.pi / 2, np.pi / 2)
    return np.array([r * np.cos(theta), r * np.sin(theta)], dtype=np.float64)


def random_initial_state(rng: np.random.Generator) -> ArmState:
    """Sample a starting joint configuration well inside joint limits."""
    return ArmState(
        q1=float(rng.uniform(-np.pi / 3, np.pi / 3)),
        q2=float(rng.uniform(-2.0 * np.pi / 3, 2.0 * np.pi / 3)),
    )
