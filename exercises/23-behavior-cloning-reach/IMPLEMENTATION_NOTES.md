# 23 — Implementation notes

## Why a 2-link planar arm, not the myCobot

The checklist task is *about* behavior cloning. Putting the BC
algorithm on the myCobot would have meant 6 joint angles, 7 link
transforms, joint limits, a 3D Jacobian, a URDF, and either Gazebo
or PyBullet to step it. All of that is real-arm work — important,
but a different exercise (cf. 18–22 for the MoveIt side).

A 2-link planar arm has the same *shape* of problem (state ->
action with non-linear FK) but is small enough that the entire
workspace fits on one matplotlib plot. Concepts that scale to 6-DoF:

- The expert is a Jacobian-pinv controller — exactly what you'd use
  on a 6-DoF arm too.
- The dataset is `(state, action)` pairs — same in 6-DoF.
- The model is an MLP with `state_dim` in / `action_dim` out — same.
- The success bar is "TCP within 3 cm of the target" — same.

Going to 6-DoF means bigger state (8 instead of 4), bigger action
(6 instead of 2), more demos, slightly bigger network. No new ideas.

## Why scikit-learn instead of PyTorch

The model has ~7 000 parameters. Training takes seconds on CPU. For
a model that size, `sklearn.neural_network.MLPRegressor` gives you:

- `model.fit(X, y)` — one line.
- `model.predict(X)` — one line.
- `joblib.dump(model, path)` — saves the entire model.
- Early stopping baked in.

PyTorch would be ~80 lines for the same thing and pull in a 600 MB
dependency. The point of this exercise is BC, not deep-learning
plumbing. We'd reach for PyTorch the moment we wanted larger nets,
GPUs, or convolutional inputs — none of which apply here.

## Why an analytical expert instead of human teleop

The checklist literally says "human teleop with keyboard or
gamepad". We replaced that with an analytical controller in
`expert.py` for three reasons:

1. **Reproducibility.** Two readers of the exercise will get
   bit-identical training data and bit-identical results. A human
   demo would drift.
2. **Speed.** The whole pipeline runs in seconds. A 60-second human
   demo plus setup is 5+ minutes per attempt.
3. **No hardware.** This exercise has no GUI, no joystick driver,
   no live arm. See [`HARDWARE.md`](HARDWARE.md) for the version
   with a real gamepad.

The expert is a vanilla resolved-rate (Jacobian pseudo-inverse)
controller with a P term on TCP error. It produces smooth,
target-seeking motion — exactly the qualitative shape of a human
teleop trajectory.

## Why the BC model still beats the expert on one metric (and loses on another)

The BC model is faster than the expert *at inference* (one MLP
forward pass vs a 2x2 matrix inversion), and that scales — at 6-DoF
the expert needs a 6x6 damped pseudo-inverse, the BC model still
needs one forward pass.

The BC model is *worse* than the expert at extrapolation. If you
give it a starting state the expert never visited, or a target far
from any training target, it does not reason its way back to the
right action — it interpolates from nearest neighbours in feature
space, which can mean nonsense. This is exactly why BC is
infrastructure-cheap but brittle, and exactly why exercise 24 (RL)
exists in the curriculum.

## How the success threshold interacts with the rollout loop

`evaluate.rollout_policy` breaks out of the loop the moment TCP
error falls below `SUCCESS_RADIUS_M = 0.03 m`. That's why every
PASS shows a final error very close to 30 mm, not 0 mm — the policy
*could* get closer, but the success check fires first.

If you raise `SUCCESS_RADIUS_M` to e.g. 0.005, expect the average
final error to fall and the step count to rise. That's the tightness
/ time trade-off you'd tune for a real task.

## Why one run usually fails (run 10 in the seeded demo)

With seed 999, run 10's target is `(0.046, -0.078)` — close to the
inner reach boundary, in the negative-y half of the workspace. The
expert visits the negative-y half only when its random starting
state happens to land there, so coverage near that target is thin.
The BC model interpolates badly there and stalls.

Two ways to fix it if you ever need 10/10:

- Cover the workspace more uniformly during demo collection (sample
  more targets, or grid-sample instead of random).
- Use **DAgger** (Dataset Aggregation): after a failed rollout, ask
  the expert what *it* would have done from each visited state, add
  those `(state, action)` pairs to the dataset, retrain. Standard
  follow-up to plain BC.

We leave it at 9/10 to make the failure mode visible — it's a
teachable BC behaviour, not a bug.

## Assumptions and failure modes

| Assumption | What breaks if it's wrong |
|---|---|
| Kinematic-only sim (no gravity, no friction) | a real arm has dynamics; BC trained on a kinematic sim transfers poorly |
| Targets sampled from the same distribution at eval time | targets outside the training distribution fail (see run 10) |
| 20 Hz control rate | a slower rate makes the action have more effect per step and the BC model has to be retrained for it |
| 2-link planar geometry | doesn't capture wrist orientation, gripper opening, or obstacles |

For autosampler v1, the takeaway is: BC is the right tool *if* you
have a fast simulator with the same dynamics as the real arm, *and*
you collect enough demos to cover the relevant slot positions.
That's a lot of "ifs" — which is why exercise 21 (hard-coded
pick-and-place) remains v1.

## Debugging tips

- **Training loss never drops** -> check that `actions` is the
  *next* action, not the current one. A common BC bug is shifting
  the alignment off by one timestep.
- **Policy always returns the same action** -> bias-only solution.
  Usually means the state input wasn't scaled and one feature
  dominates. (Not an issue here: all four inputs are in similar
  ranges.)
- **Policy converges to wrong target** -> the model is treating the
  target as a "weak hint" and falling back to whatever the average
  expert trajectory looked like. Add more demos with varied targets.
- **Policy oscillates near the target** -> the expert's gain is too
  high and the model copied that. Lower `expert.GAIN` or add a
  proportional gain in the policy output as a smoothing layer.
