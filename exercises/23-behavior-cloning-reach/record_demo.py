"""Record one 60-second 'teleop' demo of the arm reaching a target.

The expert (expert.py) plays the role of the human at the gamepad. We
log (state, action) pairs at 20 Hz for 60 seconds = 1200 samples per
demo. The checklist task says 'one teleop demo' — we record N short
demos with N random targets so the BC model sees a spread of goals.

State  = (q1, q2, target_x, target_y) -- 4D
Action = (dq1, dq2)                   -- 2D
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from arm_2link import (
    ArmState,
    forward_kinematics,
    random_initial_state,
    random_reachable_target,
    step,
)
from expert import expert_action


DT = 0.05               # 20 Hz
DEMO_SECONDS = 60.0
SAMPLES_PER_DEMO = int(DEMO_SECONDS / DT)
NUM_DEMOS = 20          # 20 random targets to cover the workspace


def record_one_demo(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Roll the expert from a random start to a random target."""
    state = random_initial_state(rng)
    target = random_reachable_target(rng)

    states = np.zeros((SAMPLES_PER_DEMO, 4), dtype=np.float64)
    actions = np.zeros((SAMPLES_PER_DEMO, 2), dtype=np.float64)

    for t in range(SAMPLES_PER_DEMO):
        action = expert_action(state, target)
        states[t] = (state.q1, state.q2, target[0], target[1])
        actions[t] = action
        state = step(state, action, DT)

    return states, actions


def record_dataset(seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Stack NUM_DEMOS demos into one training set."""
    rng = np.random.default_rng(seed)
    all_states = []
    all_actions = []
    for i in range(NUM_DEMOS):
        s, a = record_one_demo(rng)
        all_states.append(s)
        all_actions.append(a)
    return np.concatenate(all_states), np.concatenate(all_actions)


if __name__ == "__main__":
    states, actions = record_dataset(seed=0)
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    np.savez(out_dir / "demo.npz", states=states, actions=actions)
    print(f"[record] saved {len(states)} samples to {out_dir / 'demo.npz'}")
