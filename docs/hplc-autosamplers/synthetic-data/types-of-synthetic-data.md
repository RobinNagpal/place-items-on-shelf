# 00 — Types of synthetic data

> **Who this is for.** Anyone who needs a short, plain-English
> menu of the kinds of synthetic data the Gazebo simulator can
> dump for the HPLC-autosampler ketchup cell.

## Why have a catalogue at all

A camera frame is not the only thing you can record from a
simulator. The arm has joint encoders. The wrist can carry a
force sensor. Gazebo itself knows the true 3D pose of every
object in the scene at every millisecond. Each of those streams
is a **kind of synthetic data**, and each one is the right input
for a different decision in the cell.

This file is the menu. Each entry has its own deeper file under
[`types/`](types/) explaining what it is, when it is useful,
**who consumes it (which ML model or which non-ML pipeline)**,
and **how to produce it in Gazebo**.

## What was trimmed and why

The first draft of this catalogue had twelve types. After
review three were dropped:

| Dropped type | Reason |
|---|---|
| **Keypoint annotations** | The rack and the autosampler tray are in fixed fixtures and the ArUco-marker pipeline already gives sub-cm pose. Keypoints add no new signal for this cell. |
| **Joint-state / effort traces** | Not a standalone training target. The useful uses (imitation learning, collision threshold) live inside other types — joint logs ride along with **demonstration trajectories** (type 8). |
| **Fluid-level / liquid-level sequences** | Gazebo's physics engine is rigid-body. It does **not** simulate liquids pouring or transferring. Faking levels with shrinking visual props gives data the underlying simulator cannot validate, so the training value is low. We avoid it. |

So the cell focuses on **9 types** that the simulator can produce
honestly and that each have a named consumer.

## The 9 types

Split into two buckets by what consumes them.

### Bucket A — trainable datasets (an ML model learns from these)

| # | Type | Model that consumes it | Detail |
|---|---|---|---|
| 1 | **RGB images + 2D bounding boxes** | YOLOv8 (object detector) | [`types/01-rgb-boxes.md`](types/01-rgb-boxes.md) |
| 2 | **Per-pixel segmentation masks** | YOLOv8-seg, SAM, Mask R-CNN | [`types/02-segmentation-masks.md`](types/02-segmentation-masks.md) |
| 8 | **Demonstration trajectories** | Behaviour Cloning MLP, Diffusion Policy, ACT | [`types/08-demonstration-trajectories.md`](types/08-demonstration-trajectories.md) |
| 9 | **Failure-case datasets** | Small CNN classifier (anomaly flag) | [`types/09-failure-cases.md`](types/09-failure-cases.md) |

### Bucket B — pipeline inputs and smoke-test sets (no model, but real code reads them)

| # | Type | What actually uses it | Detail |
|---|---|---|---|
| 3 | **Depth images and point clouds** | `cv2.projectPoints` math, RGB-D fusion code | [`types/03-depth-and-point-clouds.md`](types/03-depth-and-point-clouds.md) |
| 4 | **6-DoF object poses (per-frame)** | Scorer for every other perception type — ground truth | [`types/04-6dof-object-poses.md`](types/04-6dof-object-poses.md) |
| 5 | **Force / torque time-series** | Threshold rule (`if Fz > 1 N: stop`) or a small 1D-CNN | [`types/05-force-torque-traces.md`](types/05-force-torque-traces.md) |
| 6 | **Synthetic text / barcode renders** | `paddleocr`, `pyzbar` — pre-trained off-the-shelf | [`types/06-text-and-barcode-renders.md`](types/06-text-and-barcode-renders.md) |
| 7 | **Camera calibration sets** | `cv2.calibrateCamera`, `cv2.calibrateHandEye` — no ML | [`types/07-camera-calibration-sets.md`](types/07-camera-calibration-sets.md) |

## How to use this catalogue

For any given step of the HPLC workflow (Steps 2 / 3 / 4 / 5 / 8
have Gazebo worlds in [`../../../gazebo_worlds/`](../../../gazebo_worlds/)):

1. Read the per-step file in this folder (e.g. `02-dissolution-and-extraction.md`).
2. The "Useful synthetic-data types" table in that file refers
   to the types below by number — **1, 2, 3, …, 9** as numbered
   here. Click through to the per-type file for the recipe.
3. Each per-type file ends with **"How to produce it in
   Gazebo"** — the actual commands, sensors, and plugins you
   wire up.

## Same answer in one sentence

For this cell the simulator should dump: **RGB+boxes**,
**segmentation masks**, **depth**, **6-DoF poses**,
**force/torque traces**, **synthetic text/barcode textures**,
**calibration image sets**, **scripted-expert demonstrations**,
and **failure-case captures**. Nothing else.

> **Heads-up on the per-step files.** The per-step files
> (`01-weighing.md` … `08-placement-in-autosampler.md`) were
> written against the original 12-type list and still refer to
> the **old** numbering plus the dropped types (keypoints,
> joint-state, fluid-level). They need a follow-up sweep to
> match this trimmed catalogue. Read the per-type files in
> [`types/`](types/) as the source of truth in the meantime.
