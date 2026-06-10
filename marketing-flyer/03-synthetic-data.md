# Page 3 — Synthetic Data

**Goal of the page.** Explain what synthetic data is, what we
produce, the methods we use, and the formats we ship in. The reader
should finish the page knowing which of their machine-learning
pipelines our datasets can feed.

**Source.** Content distilled from
[`../docs/hplc-autosamplers/synthetic-data/industry-methods.md`](../docs/hplc-autosamplers/synthetic-data/industry-methods.md),
which lists twelve industry methods. The flyer covers the six that
matter most to a small robotics team.

---

## Content

### Page title

> Synthetic Data

### One-sentence intro

> Real-world data is slow and expensive to label. Synthetic data is
> rendered inside the simulator, where the system already knows the
> ground truth of every pose, every contact force, and every pixel.

### Section 1 — What we produce

Six bullets, each one a category of labelled data we generate.

**Section heading**

> What We Produce

**Bullet 1 — RGB images with boxes**

> Rendered camera frames with 2D bounding boxes around every
> object. The standard input for an object detector such as YOLO.

**Bullet 2 — Segmentation masks**

> Per-pixel labels saying which class — or which instance — each
> pixel belongs to. The input for a segmentation model.

**Bullet 3 — Depth maps and 6-DoF poses**

> Per-pixel depth plus the exact position and orientation of every
> object in the scene. The input for grasp planners and pose-based
> policies.

**Bullet 4 — Force and torque traces**

> Time-series of forces and torques at the gripper and the joints,
> recorded during contact-rich tasks. The input for insertion,
> threading, and peg-in-hole policies.

**Bullet 5 — Demonstration trajectories**

> The full `(observation, action)` log of an expert (scripted or
> teleoperated) doing the task. The input for behaviour cloning,
> diffusion policy, and ACT.

**Bullet 6 — OCR and barcode renders**

> Camera frames with generated text, codes, and labels baked on,
> at random fonts, perspectives, and lighting. The input for an
> OCR or barcode pipeline.

### Section 2 — Methods we use

Six bullets, each one an industry technique we apply.

**Section heading**

> Methods We Use

**Bullet 1 — Domain randomization**

> Lighting, textures, camera pose, object pose, and background
> distractors change on every frame, so the model learns the
> variation instead of overfitting to one rendered look.

**Bullet 2 — Procedural scene generation**

> Code generates the whole scene each time — random objects on
> random shelves with random clutter — so the dataset covers
> situations we did not hand-pick.

**Bullet 3 — Photo-realistic rendering**

> Ray-traced images with physically based materials, so a vision
> model trained in sim has a chance of working on the real camera.

**Bullet 4 — Sensor noise modelling**

> RealSense speckle, Kinect dropout, and force-sensor drift added
> on top of the perfect simulator reading, so the model trains on
> something close to what the real sensor produces.

**Bullet 5 — Imitation-learning demonstrations**

> A scripted or teleoperated expert runs the task hundreds of
> times in sim; the logs become the training set for a policy.

**Bullet 6 — Failure-case authoring**

> A config says "perturb the scene this way, run the expert, label
> the outcome" — so the dataset includes the edge cases that
> would never appear by accident.

### Section 3 — Standard formats

Three bullets — the dataset formats we ship in.

**Section heading**

> Standard Formats

**Bullet 1 — LeRobot (Parquet, Hugging Face)**

> Plays nicely with the Hugging Face training stack and the
> LeRobot policy zoo.

**Bullet 2 — Robomimic (HDF5, Stanford)**

> Plays nicely with behaviour cloning baselines from Stanford and
> with the Robosuite environments.

**Bullet 3 — RLDS (TensorFlow Datasets, Google)**

> Plays nicely with the RT-2 family and other Google-stack
> imitation-learning code.

If a different format is needed (custom HDF5, MCAP rosbags,
COCO JSON, …) we ship in it. The three above are the defaults.

### Section 4 — What you get

A short statement, no bullets.

**Section heading**

> What You Get

**Body**

> A dataset in a standard format, the script that generated it,
> and a README that documents what every label means. You can
> rerun the script with new parameters whenever the task changes.

### Footer

> For more information, visit https://dodao.io     Page 3 of 4

---

## Layout

```
+-----------------------------------------+
|                              [DoDAO ▢] |
|                                         |
|  ▎Synthetic Data                        |
|                                         |
|  Real-world data is slow and expensive  |
|  to label. Synthetic data is rendered … |
|                                         |
|  ▎What We Produce                       |  ← Section 1
|  • RGB images with boxes                |
|  • Segmentation masks                   |
|  • Depth maps and 6-DoF poses           |
|  • Force and torque traces              |
|  • Demonstration trajectories           |
|  • OCR and barcode renders              |
|                                         |
|  ▎Methods We Use                        |  ← Section 2
|  • Domain randomization                 |
|  • Procedural scene generation          |
|  • Photo-realistic rendering            |
|  • Sensor noise modelling               |
|  • Imitation-learning demonstrations    |
|  • Failure-case authoring               |
|                                         |
|  ▎Standard Formats                      |  ← Section 3
|  • LeRobot                              |
|  • Robomimic                            |
|  • RLDS                                 |
|                                         |
|  ▎What You Get                          |  ← Section 4
|  A dataset in a standard format, …      |
|                                         |
|  For more information, visit            |
|  https://dodao.io        Page 3 of 4    |
+-----------------------------------------+
```

**Block-by-block placement**

| # | Block | Position | Notes |
|---|-------|----------|-------|
| 1 | DoDAO logo | Top-right | Same as Page 1. |
| 2 | Page title | Top-left, 36 pt | Accent bar on the left. |
| 3 | Intro | Under title | 2 lines max. |
| 4 | "What We Produce" | Below intro | 6 bullets. Consider a 2-column grid (3 bullets per column) to save vertical space. |
| 5 | "Methods We Use" | Below Section 1 | 6 bullets. Same option for 2-column grid. |
| 6 | "Standard Formats" | Below Section 2 | 3 bullets, compact. |
| 7 | "What You Get" | Below Section 3 | One short paragraph. |
| 8 | Footer | Bottom | URL left, page number right. |

**Two-column option for Sections 1 and 2.** This page has more
content than Pages 1, 2, and 4. If the single-column layout
overflows, lay out the six bullets of Sections 1 and 2 in a
**2 × 3 grid** (two columns of three bullets). Keep Sections 3
and 4 single-column.

If even the grid is tight, cut "OCR and barcode renders" from
Section 1 (the rarest of the six) and "Failure-case authoring"
from Section 2 (the most niche of the six).
