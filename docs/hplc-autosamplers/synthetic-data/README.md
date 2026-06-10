# Synthetic data for the HPLC autosampler (ketchup case)

> **Who this is for.** Anyone in robotics who is building, training, or
> testing the software side of the HPLC autosampler ketchup cell and
> wants to know **what kind of fake-but-labelled data the simulator
> should produce** so the perception, motion, and learning code has
> something to chew on. No machine-learning background assumed.

## What "synthetic data" means here

The robot needs to **see and feel** its environment to do its job:
where the beaker is, how high the liquid is, whether the cap is on,
whether the fingers actually closed on the vial, and so on. Each of
those questions is answered by a sensor (camera, depth camera, force
sensor, joint encoders, …) plus a piece of software that turns the
raw sensor reading into a decision ("yes, vial is gripped").

That software needs **training and testing data**. In a real lab a
human would label thousands of camera frames by hand. That is slow
and expensive. **Synthetic data** means the same kind of labelled
data, but generated **inside the simulator** (Gazebo, Isaac Sim) where
the system already knows the truth of every pose, every joint angle,
every contact force — for free.

So a "synthetic dataset" for one step typically looks like:

```
synthetic_<step>/
├── images/        rendered RGB frames (and maybe depth frames)
├── labels/        per-frame ground truth  (boxes, masks, poses, …)
├── traces/        per-trajectory time-series (joints, F/T, contact)
└── metadata.json  what world, what randomisation, what units
```

## Why this folder exists

This project ships [`gazebo_worlds/`](../../../gazebo_worlds/) for
5 of the 8 HPLC workflow steps (the ketchup case: Steps 2, 3, 4, 5,
8 — the other three are skipped or out of scope). Those worlds are
the **stage**. The next question is: *what kind of labelled data
should we ask the simulator to dump while the stage runs?*

This folder answers that question, step by step.

> **Not just YOLO.** A bounding box around a beaker (YOLO-style
> 2D detection) is the most common form of synthetic data, but it
> is the **least interesting** for this cell. The autosampler has
> strong priors (rack and tray in fixed fixtures, vials of a single
> known shape, beaker geometry fixed) so the *valuable* synthetic
> data points elsewhere — fluid level, contact forces, pellet /
> supernatant boundary, etched fill-marks, label OCR, demonstration
> trajectories. See
> [`../perception-design-decisions.md`](../perception-design-decisions.md)
> for the "why simpler than YOLO is fine for v1" argument and
> [`00-types-of-synthetic-data.md`](00-types-of-synthetic-data.md)
> for the full catalogue.

## How to read this folder

Two layers:

- **[`00-types-of-synthetic-data.md`](00-types-of-synthetic-data.md)** —
  a **catalogue** of every kind of synthetic data you might want,
  written once. RGB + boxes, RGB + masks, keypoints, depth, 6-DoF
  poses, force / torque traces, joint-effort logs, OCR / barcode
  renders, fluid-level sequences, demonstration trajectories,
  failure-case sets, calibration sets. The per-step files below
  *refer back to* these by name.
- **`0N-<step-slug>.md`** — one file per HPLC workflow step. Each
  one says: what the robot does in that step, what it has to **see
  or feel** to do it, and which synthetic-data types are useful
  here (with a concrete label format and the algorithm or model
  that consumes them).

| # | File | HPLC step | Project status | Gazebo world |
|---|------|-----------|----------------|--------------|
| 1 | [`01-weighing.md`](01-weighing.md) | Weighing | **Skipped** — pre-weighed paste used instead | none |
| 2 | [`02-dissolution-and-extraction.md`](02-dissolution-and-extraction.md) | Dissolution / extraction | Modelled | [`gazebo_worlds/02-…`](../../../gazebo_worlds/02-dissolution-and-extraction/) |
| 3 | [`03-dilution.md`](03-dilution.md) | Dilution | Modelled | [`gazebo_worlds/03-…`](../../../gazebo_worlds/03-dilution/) |
| 4 | [`04-filtering.md`](04-filtering.md) | Filtering | Modelled | [`gazebo_worlds/04-…`](../../../gazebo_worlds/04-filtering/) |
| 5 | [`05-transfer-to-vial.md`](05-transfer-to-vial.md) | Transfer to vial | Modelled | [`gazebo_worlds/05-…`](../../../gazebo_worlds/05-transfer-to-vial/) |
| 6 | [`06-capping.md`](06-capping.md) | Capping | **Skipped** — too hard to automate with a basic cobot gripper | none |
| 7 | [`07-labeling.md`](07-labeling.md) | Labelling | Out of scope for the current sim worlds | none |
| 8 | [`08-placement-in-autosampler.md`](08-placement-in-autosampler.md) | Placement in autosampler | Modelled (the headline task) | [`gazebo_worlds/08-…`](../../../gazebo_worlds/08-placement-in-autosampler/) |

Steps 1 and 6 are documented for completeness — anyone extending
the project later will hit those questions, and the underlying
workflow doc covers all 8 steps regardless of what this project
chose to model.

## Source workflow

The 8 HPLC workflow steps in the docs below come from the
external research repository:

- [`02-hplc-autosampler/03-hplc-workflow/`](https://github.com/RobinNagpal/robotics-research/tree/main/02-hplc-autosampler/03-hplc-workflow)
- One markdown file per step: `01-weighing.md`, `02-…`, … `08-…`.

Each per-step doc here ends with the source URL for its step.

## What this folder is **not**

- **Not** a list of finished datasets. The datasets do not exist
  yet. This folder is the **specification** for what to generate.
- **Not** a tutorial on how to call Gazebo's APIs. The
  *mechanism* (how to dump a frame, how to randomise lighting,
  how to read `/gazebo/model_states`) is a separate engineering
  exercise and will live in a future `exercises/` folder.
- **Not** a perception-model recommendation. This folder says
  "this kind of label is useful here." The decision *which*
  model consumes it (YOLO vs HSV vs ArUco vs an MLP vs a small
  transformer) belongs in
  [`../perception-design-decisions.md`](../perception-design-decisions.md).
