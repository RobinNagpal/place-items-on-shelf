# Type 9 — Failure-case datasets

## What it is

A dataset where every entry is **deliberately broken** in a
known way, and the label says **which way**. Frames, traces,
or full trajectories that show:

- A vial tipped over on the rack.
- A label stuck on crooked.
- A cap that missed the threads.
- A gripper that closed on air instead of on a vial.
- A barcode that doesn't match the worklist.
- A tray placed at a 5° rotation.

Each entry's label is the **failure mode string**
(`vial_tipped`, `cross_threaded_cap`, `missed_grasp`, …).

This is the **opposite** of every other type in this catalogue.
The other types capture what the cell looks like when things
**work**. This type captures what the cell looks like when
they don't.

## When it is useful

A model that has only ever seen good frames **silently
rubber-stamps a broken scene**. Adding failure data is what
teaches it to raise a flag. Specifically:

- After every pick, the perception code should answer "did the
  pick actually succeed?" — needs an empty-gripper failure
  set.
- After every placement, "is the vial seated upright?" — needs
  a tilted-in-slot failure set.
- After every Step 4 filtration, "did the syringe filter
  actually attach to the Luer tip?" — needs a
  filter-not-attached failure set.
- Before any HPLC run is committed to LIMS, "does the cap
  colour on this vial match the worklist row?" — needs a
  wrong-colour mismatch set.

## Who uses it

A **small CNN classifier**, almost always — much smaller than
YOLO. The input is one frame or one short trace; the output is
one of a handful of class labels.

| Failure space | Model |
|---|---|
| Frame-based (tipped vial, crooked label, missed grasp) | A 5-10 layer CNN, ~50 k parameters. ResNet-8, MobileNetV3-Small, or a hand-rolled net. |
| Trace-based (cross-threaded cap, clogged filter, dropped vial) | A 1D-CNN or LSTM over a 1-2 s F/T window. Reuses the model from type 5. |
| String-based (barcode mismatch) | Not ML — a simple string compare against the worklist. |

For the binary case ("is anything wrong, yes / no?") the model
can be even smaller — a logistic regression on a few hand-rolled
features is often enough.

## How to produce it in Gazebo

The recipe: **take the nominal trajectory generator and inject
one perturbation per failure mode**. The simulator does the
rest.

### 1. Define one perturbation per failure mode

```python
PERTURBATIONS = {
    "vial_tipped":         lambda v: rotate(v, axis="x", deg=85),
    "missed_grasp":        lambda _: shift_target(z=+0.005),  # 5 mm too high
    "tray_rotated":        lambda t: rotate(t, axis="z", deg=5),
    "wrong_cap_colour":    lambda v: recolour(v, "white"),     # tagged as red in worklist
    "filter_not_attached": lambda f: shift(f, x=+0.05),        # bench, not syringe
    ...
}
```

Each perturbation is a small modification to the scene before
the run starts.

### 2. Run the same expert script under each perturbation

Reuse the type 8 scripted expert. The script does **not** know
about the perturbation — that's the point. It tries to do the
nominal task and either succeeds (no failure injected), fails
gracefully, or breaks visibly.

```python
for mode, mutate in PERTURBATIONS.items():
    for traj_idx in range(N_PER_MODE):
        world = reset_world(seed=traj_idx)
        mutate(world)                       # inject the failure
        try:
            run_expert(world)
        except ExecutionError:
            pass
        capture(world, label=mode, traj=traj_idx)
```

### 3. Capture the right thing per failure mode

Different failure modes are visible in different streams:

| Failure mode | Best capture |
|---|---|
| `vial_tipped`, `crooked_label`, `wrong_cap_colour` | Overhead RGB frame |
| `missed_grasp`, `tilted_in_slot` | Wrist-camera RGB or overhead depth |
| `cross_threaded_cap`, `clogged_filter` | F/T trace (type 5) |
| `barcode_mismatch` | Scan-station RGB + the decoded string |

You don't need every stream for every failure — just the one
that *shows* the failure.

### 4. Stay balanced

A 99 / 1 dataset (99 % nominal, 1 % failure) trains a model
that ignores the failure class. Rule of thumb: **30 / 70** is
plenty (30 % failures spread across N failure types, 70 %
nominal). For the binary case, **50 / 50**.

## What you end up with

```
synthetic_<step>_failures/
├── images/
│   ├── tipped_<N>.jpg
│   ├── missed_grasp_<N>.jpg
│   └── ...
├── traces/
│   ├── crossthread_<N>.csv
│   └── clogged_filter_<N>.csv
└── labels/
    └── failure_<N>.json   # {"mode": "tipped", "severity": 0.7,
                          #  "expert_outcome": "stopped_early"}
```

## Why synthetic is the right call

Capturing real failure data is **expensive and slow**. To get
1 000 "tipped vial" frames you have to tip 1 000 vials in a real
lab. To get 100 "cross-threaded cap" traces you have to break
100 caps. In sim each failure is a 5-line config change and
runs overnight.

That advantage **only** holds for failures the simulator can
produce honestly. Failures that depend on fluid dynamics
(filter clog progress, overflowing vial, spilled solvent puddle
shape) are off-limits for this project — Gazebo's physics is
rigid-body. So the failure list above is restricted to
**rigid-body and pose failures**, which is exactly what the v1
spec already cares about.

## Existing project reference

The repo does not yet have a dedicated failure-case exercise.
The closest is the
[`exercises/05-score-detections-vs-gazebo/`](../../../../exercises/05-score-detections-vs-gazebo/)
scorer's TP / FP / FN bookkeeping, which **measures** false
positives but does not **train** a classifier to predict them.
This type of dataset is the next step beyond that.
