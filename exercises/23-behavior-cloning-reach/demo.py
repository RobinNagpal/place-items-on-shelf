"""End-to-end: record demos -> train BC policy -> evaluate -> plot.

Run with `python demo.py`. The whole pipeline takes ~10 seconds.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # write to PNG, no GUI required
import matplotlib.pyplot as plt
import numpy as np

from arm_2link import L1, L2, ArmState, forward_kinematics, random_initial_state, random_reachable_target, step
from evaluate import MAX_STEPS, SUCCESS_RADIUS_M, evaluate
from record_demo import record_dataset
from train_bc import train


def plot_one_rollout(model, out_path: Path) -> None:
    """Show the arm reaching one fresh target — visual sanity check."""
    rng = np.random.default_rng(42)
    start = random_initial_state(rng)
    target = random_reachable_target(rng)

    xs, ys = [], []
    state = start
    for _ in range(MAX_STEPS):
        tcp = forward_kinematics(state)
        xs.append(tcp[0])
        ys.append(tcp[1])
        obs = np.array([state.q1, state.q2, target[0], target[1]]).reshape(1, -1)
        action = model.predict(obs)[0]
        state = step(state, action, 0.05)
        if np.linalg.norm(tcp - target) < SUCCESS_RADIUS_M:
            break

    fig, ax = plt.subplots(figsize=(5, 5))
    circle = plt.Circle((0, 0), L1 + L2, fill=False, linestyle="--", color="gray")
    ax.add_patch(circle)
    ax.plot(xs, ys, "b-", label="TCP path")
    ax.plot(xs[0], ys[0], "go", markersize=10, label="start")
    ax.plot(target[0], target[1], "rx", markersize=12, mew=3, label="target")
    ax.plot(xs[-1], ys[-1], "bs", markersize=10, label="reached")
    ax.set_xlim(-0.22, 0.22)
    ax.set_ylim(-0.22, 0.22)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title("BC policy rollout (1 of 10)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def main() -> None:
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    print("[demo] 1) recording 20 teleop demos (60 s each, 20 Hz) ...")
    states, actions = record_dataset(seed=0)
    np.savez(out_dir / "demo.npz", states=states, actions=actions)
    print(f"[demo]    -> {len(states)} (state, action) pairs")

    print("[demo] 2) training a 64x64 MLP via behavior cloning ...")
    model = train(states, actions)
    joblib.dump(model, out_dir / "bc_policy.joblib")
    print(f"[demo]    -> training loss {model.loss_:.6f} after {model.n_iter_} epochs")

    print("[demo] 3) evaluating on 10 fresh random targets ...")
    results = evaluate(model)
    successes = sum(r["success"] for r in results)
    for r in results:
        flag = "PASS" if r["success"] else "FAIL"
        print(
            f"[demo]    run {r['run']:2d}: target {r['target']}  "
            f"final err {r['final_err_m'] * 1000:5.1f} mm  "
            f"in {r['steps']:3d} steps  [{flag}]"
        )
    print(f"[demo] {successes}/{len(results)} runs within 3 cm")

    print("[demo] 4) plotting one rollout to output/rollout.png ...")
    plot_one_rollout(model, out_dir / "rollout.png")

    bar = "PASS" if successes >= 8 else "FAIL"
    print(f"[demo] {bar} - checklist 'done when' is 8/10 within 3 cm. got {successes}/10.")


if __name__ == "__main__":
    main()
