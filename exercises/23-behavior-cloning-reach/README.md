# 23 — Behavior cloning from one teleop demo

Implements checklist item **23** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What this exercise does, in plain English

So far every exercise has *told* the arm what to do — give MoveIt a
pose, or hard-code a sequence of poses (exercise 21). This exercise
flips that around: a tiny neural network **learns** what to do by
watching one person drive the arm to a target.

The recipe is the textbook one for **behavior cloning (BC)**:

1. **Record** a person teleoperating the arm toward a target —
   60 seconds of `(state, action)` samples (state = "where am I and
   where do I want to go", action = "the next joint velocity").
2. **Train** a tiny MLP to predict the action given the state, with
   plain supervised learning.
3. **Deploy** the network as the controller — feed it the current
   state, follow whatever action it predicts.

If you do this right, the network has effectively *imitated the human*
— it produces the same kind of smooth, target-seeking motion the
teleop demo showed.

Because we have no human and no gamepad in this exercise, we **stand
in for the teleop operator** with an analytical Jacobian controller
(`expert.py`). It produces the same smooth target-seeking joint
velocities a person would — and the BC model never gets to see the
formula, only the `(state, action)` pairs it produces. That's the
whole point of imitation learning.

```
   "human at the gamepad"           dataset                   trained policy
   (simulated by expert.py)         (state -> action)         (MLPRegressor)
            │                            │                          │
            │  60 s @ 20 Hz              │  64x64 MLP, ~7 k params  │
            ▼                            ▼                          ▼
   1200 (state, action) pairs  ────►  fit weights  ─────────────►  rollout in sim
            x 20 random targets         (no reward, no RL)          on 10 fresh targets
                                                                    pass if 8/10 within 3 cm
```

## Quick answers (read this first)

**Why a 2-link planar arm, not the myCobot?**
The myCobot is 6-DoF — useful for the real autosampler, but it buries
the BC concept under six joints' worth of math. A 2-link arm in the
(x, y) plane has the **same shape** of problem (state → action, with
forward kinematics, with reach limits), but small enough that you can
plot the whole workspace and watch a single rollout converge. Once
you understand BC here, scaling to 6-DoF is mechanical (bigger
network, more data, no new ideas).

**Where does the "teleop demo" come from if there's no human?**
[`expert.py`](expert.py) plays the role of a teleoperator. It looks
at the current TCP, the target, and uses the Jacobian pseudo-inverse
to compute a joint-velocity step that moves the TCP toward the
target. A human at a gamepad would produce smooth, similar-looking
velocities — but slower and noisier. We use the analytic version
because it's reproducible. The BC model never sees the formula, only
the `(state, action)` pairs.

**What does the BC model actually learn?**
A function `f(q1, q2, target_x, target_y) -> (dq1, dq2)`. Given the
two joint angles and the target the gripper should reach, predict
the next joint velocity step. That's it.

**Is it actually intelligent?**
No. It's a glorified interpolation table over 24 000 training
samples. It works *only inside the distribution* the expert showed
it. Targets the expert never visited — or unusual joint starts —
make it fail. See run 10 in the demo output for an example.

**How does this tie into the autosampler?**
For v1 of the autosampler the right approach is item 21 (hand-coded
pick-and-place) — vials are too precious to crash. BC is the
*upgrade* you'd consider for the tricky last centimetre: teleop 20
demos of lowering a vial into a slightly misaligned slot, train a
tiny BC policy that handles those final mm more smoothly than a
hard-coded approach. Same idea as this exercise, harder data.

## What is the workflow

`demo.py` runs the whole pipeline:

```
record_demo.py          20 demos x 60 s x 20 Hz
                        ────────────────────────►   output/demo.npz
                                                    (24 000 (state, action) pairs)
                                                              │
train_bc.py             MLPRegressor(64, 64) tanh             │
                        early-stopping, adam                  ▼
                                                    output/bc_policy.joblib
                                                              │
evaluate.py             10 fresh random targets               │
                        rollout for 200 steps                 │
                        success if final err < 3 cm           ▼
                                                    PASS / FAIL line per run
                                                              │
demo.py final plot      one rollout traced in (x, y)          ▼
                                                    output/rollout.png
```

Each of the three numbered scripts is also runnable on its own.

## What the libraries are doing

- **`numpy`** — the simulator. 2-link arm FK + Jacobian + Euler step.
  Nothing fancy.
- **`scikit-learn`** (`MLPRegressor`) — the neural network. Two
  hidden layers of 64 units, tanh activation, adam optimiser, with
  early stopping on a held-out 10% of the training data. Chosen over
  PyTorch because the model is tiny and sklearn fits / saves /
  loads in one line each. **No GPU required.**
- **`joblib`** — saves the trained model to disk so `evaluate.py`
  can load it without re-training.
- **`matplotlib`** — plots one rollout (TCP path, start, target,
  reach circle) as a sanity check.

## Inputs and outputs

| | Format | Example |
|---|---|---|
| **Input** to the policy (state) | `np.array([q1, q2, tx, ty])` | `[0.20, -0.30, 0.10, 0.05]` |
| **Output** of the policy (action) | `np.array([dq1, dq2])` rad/s | `[0.6, -0.2]` |
| **Reward** | (none — pure supervised learning) | — |
| **Files written** | `output/demo.npz`, `output/bc_policy.joblib`, `output/rollout.png` | |

## Example run

```bash
# 1. install deps
pip install -r requirements.txt

# 2. run the full pipeline
python demo.py

# expected (numbers will vary slightly with sklearn version):
# [demo] 1) recording 20 teleop demos (60 s each, 20 Hz) ...
# [demo]    -> 24000 (state, action) pairs
# [demo] 2) training a 64x64 MLP via behavior cloning ...
# [demo]    -> training loss 0.000550 after ~250 epochs
# [demo] 3) evaluating on 10 fresh random targets ...
# [demo]    run  1: target (0.101, 0.101)  final err 28.6 mm  in  9 steps  [PASS]
# [demo]    ...
# [demo]    run 10: target (0.046, -0.078) final err 63.6 mm  in 200 steps [FAIL]
# [demo] 9/10 runs within 3 cm
# [demo] PASS - checklist 'done when' is 8/10 within 3 cm. got 9/10.
```

Then open `output/rollout.png` to see the TCP path of one converged
rollout (blue line from green dot to blue square, with the red X
marking the target).

## How this ties into other exercises

- **Exercise 18 / 19 (MoveIt joint and pose goals)** — the analytical
  alternative. You tell MoveIt the goal pose; it plans. BC tries to
  *learn* the same kind of behaviour from data.
- **Exercise 21 (hard-coded pick-and-place)** — what we actually use
  for autosampler v1. BC is the upgrade path, not the v1 path.
- **Exercise 24 (PPO reinforcement learning)** — the next step on the
  learning ladder. Same problem (reach a target), but **without** an
  expert demo: the policy learns from trial and error using a reward.
  RL is more general; BC is cheaper.
- **Exercise 25 (VLA inspection)** — a giant, pre-trained imitation
  model. Same supervised-learning idea, but trained by Google /
  Stanford / Anthropic on millions of demos across many robots.

## What "Done when" means here

The checklist asks for **8/10 fresh runs reaching within 3 cm of the
target**. `demo.py` covers it — we always get **9/10 or 10/10** with
the seeded RNG. The single run that fails is a pedagogical feature,
not a bug — it shows the failure mode BC is famous for (a target the
expert rarely visited).

## What this exercise is **not**

| Need | Where it is solved |
|------|--------------------|
| Trial-and-error learning (RL) | exercise 24 (PPO) |
| Natural-language interface | exercise 26 (LLM-as-router) |
| Real arm geometry (6-DoF, joint limits) | exercises 18–22 (MoveIt on myCobot) |
| Picking up a real vial | exercise 21 (hard-coded pick-and-place) |
| Hardware teleop with a gamepad | [`HARDWARE.md`](HARDWARE.md) — what changes when you do this for real |

## What's next

- [`HARDWARE.md`](HARDWARE.md) — the same exercise on a real arm:
  gamepad input, ROS bag recording, deploying the policy as a
  controller node, safety bounds.
- Exercise 24 (RL via PPO) — same reach task, no expert needed.
- Once BC works in 2D, scale it to the myCobot's 6 DoF and try the
  "drop a vial into a misaligned slot" task.
