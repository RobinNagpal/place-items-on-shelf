"""Roll out the trained policy on 10 fresh random targets.

The checklist says: 'Done when the policy reaches within 3 cm of the
target on 8/10 fresh runs.' We use a different RNG seed than training
so the targets really are fresh.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from arm_2link import (
    ArmState,
    forward_kinematics,
    random_initial_state,
    random_reachable_target,
    step,
)


SUCCESS_RADIUS_M = 0.03
MAX_STEPS = 200
DT = 0.05


def rollout_policy(
    model,
    start: ArmState,
    target: np.ndarray,
) -> tuple[float, int]:
    """Run the policy until it converges or hits MAX_STEPS."""
    state = start
    for t in range(MAX_STEPS):
        obs = np.array([state.q1, state.q2, target[0], target[1]]).reshape(1, -1)
        action = model.predict(obs)[0]
        state = step(state, action, DT)
        tcp = forward_kinematics(state)
        err = float(np.linalg.norm(tcp - target))
        if err < SUCCESS_RADIUS_M:
            return err, t + 1
    tcp = forward_kinematics(state)
    return float(np.linalg.norm(tcp - target)), MAX_STEPS


def evaluate(model, num_runs: int = 10, seed: int = 999) -> list[dict]:
    """Run num_runs rollouts and return per-run stats."""
    rng = np.random.default_rng(seed)
    results = []
    for i in range(num_runs):
        start = random_initial_state(rng)
        target = random_reachable_target(rng)
        err, steps = rollout_policy(model, start, target)
        results.append(
            {
                "run": i + 1,
                "target": tuple(np.round(target, 3)),
                "final_err_m": round(err, 4),
                "steps": steps,
                "success": err < SUCCESS_RADIUS_M,
            }
        )
    return results


if __name__ == "__main__":
    here = Path(__file__).parent
    model = joblib.load(here / "output" / "bc_policy.joblib")
    results = evaluate(model)
    successes = sum(r["success"] for r in results)
    for r in results:
        flag = "PASS" if r["success"] else "FAIL"
        print(
            f"[eval] run {r['run']:2d}: target {r['target']}  "
            f"final err {r['final_err_m'] * 1000:5.1f} mm  "
            f"in {r['steps']:3d} steps  [{flag}]"
        )
    print(f"[eval] {successes}/{len(results)} runs within 3 cm")
