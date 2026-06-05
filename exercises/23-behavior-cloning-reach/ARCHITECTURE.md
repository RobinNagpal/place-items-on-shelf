# 23 — Architecture

## Folder tree

```
23-behavior-cloning-reach/
├── README.md                # high-level overview of behavior cloning
├── ARCHITECTURE.md          # this file
├── IMPLEMENTATION_NOTES.md  # engineering choices and trade-offs
├── HARDWARE.md              # how the same exercise maps to a real arm
├── requirements.txt         # numpy, scikit-learn, matplotlib, joblib
├── arm_2link.py             # the simulator (FK, Jacobian, step)
├── expert.py                # the analytical "teleop" controller
├── record_demo.py           # collect (state, action) dataset
├── train_bc.py              # fit MLPRegressor on the dataset
├── evaluate.py              # rollout the policy on 10 fresh targets
└── demo.py                  # end-to-end: record -> train -> evaluate -> plot
```

`output/` is created at runtime and contains `demo.npz`,
`bc_policy.joblib`, and `rollout.png`. It is `.gitignore`'d.

## File-by-file

### `arm_2link.py` — the simulator

Owns the physics of the world the policy lives in.

- **`L1`, `L2`** — link lengths (0.10 m each). Tied to the rough
  scale of the myCobot's first two links.
- **`ArmState`** — two-float dataclass: `q1`, `q2` in radians.
- **`forward_kinematics(state) -> (x, y)`** — analytic FK.
- **`jacobian(state) -> 2x2`** — analytic Jacobian.
- **`step(state, action, dt) -> ArmState`** — Euler integration of
  joint velocities. No dynamics, no gravity — kinematic only.
- **`random_reachable_target(rng)`** — samples a target in the
  reachable annulus, avoiding the singular extremes.
- **`random_initial_state(rng)`** — samples a starting `(q1, q2)`
  well inside the joint range.

Depended on by `expert.py`, `record_demo.py`, `evaluate.py`,
`demo.py`.

### `expert.py` — the analytical "teleop" controller

Stands in for the human who would normally drive the arm.

- **`MAX_JOINT_SPEED = 2.0 rad/s`** — mirrors a teleop speed cap.
- **`GAIN = 4.0`** — P gain on TCP error.
- **`expert_action(state, target) -> action`** — uses the damped
  Jacobian pseudo-inverse to map TCP error to joint velocity, then
  clips per joint to `MAX_JOINT_SPEED`.

The BC training data is produced by this function, but the BC model
never sees the function — only the resulting `(state, action)` pairs.

### `record_demo.py` — generate the dataset

- **`DT = 0.05`** — 20 Hz control rate.
- **`SAMPLES_PER_DEMO = 1200`** — one 60 s demo at 20 Hz.
- **`NUM_DEMOS = 20`** — 20 random targets so the model sees a spread.
- **`record_one_demo(rng)`** — one rollout of the expert.
- **`record_dataset(seed)`** — stacks all demos into one `(states,
  actions)` array.

When run as a script, saves to `output/demo.npz`.

### `train_bc.py` — fit the MLP

- **`train(states, actions) -> MLPRegressor`** — `MLPRegressor(
  hidden_layer_sizes=(64, 64), activation="tanh", max_iter=400,
  early_stopping=True)`. ~7 k parameters total. Trains in seconds on
  CPU.

When run as a script, loads `demo.npz`, fits, saves
`bc_policy.joblib`.

### `evaluate.py` — rollout on fresh targets

- **`SUCCESS_RADIUS_M = 0.03`** — the 3 cm bar from the checklist.
- **`MAX_STEPS = 200`** — 10 s of simulated time at 20 Hz.
- **`rollout_policy(model, start, target)`** — closed-loop rollout.
  Stops the moment TCP error drops below the success radius.
- **`evaluate(model, num_runs=10, seed=999)`** — runs the rollouts
  on a **different** RNG seed than training data (seed 0 vs 999) so
  the targets are genuinely fresh.

Returns a list of per-run dicts; the script prints a PASS / FAIL
line per run and the final tally.

### `demo.py` — top-level pipeline

Calls each script's library function in order: `record_dataset` ->
`train` -> `evaluate` -> `plot_one_rollout`. Writes everything to
`output/`. This is the only file you run to verify "Done when".

## Data flow

```
arm_2link.py  ◄──── expert.py ◄──── record_demo.py
     ▲                                    │
     │                                    ▼
     │                              output/demo.npz
     │                                    │
     │                                    ▼
     │                              train_bc.py
     │                                    │
     │                                    ▼
     │                              output/bc_policy.joblib
     │                                    │
     └────────  evaluate.py ◄─────────────┘
                       │
                       ▼
                 PASS/FAIL output + output/rollout.png
```

No ROS nodes, topics, services, or message types in this exercise —
it's all in-process Python. That's deliberate: the BC concept doesn't
require ROS, and adding ROS would have buried the algorithm under
glue code. See [`HARDWARE.md`](HARDWARE.md) for the version that runs
on a real ROS-driven arm.
