# 00 — Types of synthetic data

> **Who this is for.** Anyone who needs a short, plain-English
> catalogue of the kinds of synthetic data the simulator can
> produce. The per-step files in this folder refer back to these
> by name — read this once, skim later.

## Why have a catalogue at all

A camera frame is not the only thing you can record from a
simulator. The arm has joint encoders. The wrist (if you add one)
has a force sensor. The gripper has contact sensors. Gazebo itself
knows the true 3D position of every object in the scene at every
millisecond. **Each of those streams is a kind of synthetic data**,
each one good for a different problem.

Picking the wrong type — for example, recording RGB frames with
bounding boxes when what you really needed was a fluid-level
sequence — wastes weeks. This catalogue is the menu.

The dozen entries below cover everything we'll refer to in the
per-step files. They are ordered roughly from "easy to generate,
most common" to "specialist, harder to wire up."

---

## 1. Annotated RGB images (2D bounding boxes)

**What it is.** A picture plus a list of rectangles, each
rectangle tagged with what is inside it: "beaker," "Falcon tube,"
"syringe." Stored as one `.jpg` per frame and one `.txt` per frame
holding the boxes in the well-known YOLO format
(`<class_id> <cx> <cy> <w> <h>` in image-relative coordinates).

**When useful.** When you want to know *whether* something is
present and *roughly* where, in pixels. Standard input to YOLO,
Faster R-CNN, DETR, and friends.

**Already used in.** [`exercises/03-tiny-yolo/`](../../../exercises/03-tiny-yolo/).

**Limit.** The rectangle does not tell you the exact shape, the
3D position, or the orientation. For the autosampler cell this
matters: tightly-packed vials have overlapping rectangles even
though they are clearly separate items.

---

## 2. Per-pixel segmentation masks

**What it is.** Same RGB frame, but the label is a second image
of the same size where each pixel is **coloured by the object it
belongs to**. Two flavours:

- **Semantic** — every "beaker pixel" is colour 1, every "vial
  pixel" is colour 2, no matter how many beakers / vials.
- **Instance** — colour 1 is beaker number 1, colour 2 is beaker
  number 2, …, so you can count and separate touching items.

**When useful.** When you need the **exact silhouette** — to
measure the liquid surface area, to find the boundary between two
adjacent vials, to mask out the background before any other math.
Standard input to YOLOv8-seg, Mask R-CNN, SAM.

**Already used in.** [`exercises/07-instance-segmentation/`](../../../exercises/07-instance-segmentation/).

---

## 3. Keypoint annotations

**What it is.** Same RGB frame, but the label is a small list of
**single pixel coordinates**, each one tagged with what it
represents: "vial mouth centre," "left end of the fill-mark
etched line," "tip of the pipette."

**When useful.** When the question is "where exactly is this
landmark," not "where is the whole object." Examples in this
cell: the 9 mm vial opening centre, the etched 100 mL line on a
volumetric flask, the meniscus surface line.

**Why we care.** Bounding boxes and masks are about objects.
Keypoints are about **features**. Many useful HPLC-cell decisions
boil down to a feature ("did the liquid surface cross this
line?"), and a keypoint label is the most efficient way to teach
that.

---

## 4. Depth images and point clouds

**What it is.** A second "image" alongside the RGB frame where
each pixel stores **how far away** that pixel is from the camera
(in metres). Or, equivalently, a `.ply` / `.npy` file holding a
cloud of `(x, y, z)` points. Gazebo / Isaac can render both with
zero noise (or with simulated RealSense-style noise on top).

**When useful.** Anything where you need a **3D position**
without a marker — picking the cap top, measuring how high the
liquid surface is inside a beaker, finding the rim of a centrifuge
well, sanity-checking a YOLO box against a real 3D location.

**Already used in.** [`exercises/08-depth-to-3d-centroid/`](../../../exercises/08-depth-to-3d-centroid/).

---

## 5. 6-DoF object poses (per-frame, per-object)

**What it is.** A small CSV (or JSON) listing, for each named
object in the scene, its full **(x, y, z, roll, pitch, yaw)** in
the world frame. Gazebo publishes this automatically on
`/gazebo/model_states` — you only have to record it.

**When useful.** Two cases:

- As a **ground truth** to score perception code (exercise 5
  already does this for 2D boxes; the same idea extends to 3D).
- As the **direct label** for training a pose-estimation network
  or for testing an ArUco / AprilTag pipeline.

**Why we care for this cell.** Most of the autosampler decisions
ultimately need an object pose (where is the beaker, where is the
vial, where is the rack corner). 6-DoF pose is the most compact
way to capture it.

---

## 6. Force / torque (F/T) time-series

**What it is.** A time-series file (CSV, one row per timestep)
of `Fx Fy Fz Tx Ty Tz` from a virtual six-axis sensor placed
between the wrist and the gripper. Gazebo has a `force_torque`
sensor plugin that publishes this stream during simulation.

**When useful.** When the question is "did I touch something" or
"how hard am I pushing." For this cell:

- Stop the descent the instant a vial bottom touches a slot
  (Step 8).
- Detect when the syringe filter has clogged (Step 4) — push
  force rises sharply.
- Detect a missed grasp — closing on air gives a zero-force
  trace, closing on a vial gives a small force spike.
- Verify the cap is screwed to the right torque (Step 6, if you
  re-enable it).

**Why we care.** The visual sensors are blind once two objects
touch. Force tells you what happens after that contact.

---

## 7. Joint-state and effort time-series

**What it is.** A CSV with one row per timestep holding every
joint's position, velocity, and **effort** (motor current /
torque). ROS publishes this on `/joint_states`; Gazebo's
`joint_state_publisher` plugin fills it during simulation.

**When useful.**

- Spot **collisions** as effort spikes on a single joint.
- Spot a **payload anomaly** — an unexpectedly empty or full
  beaker has a different lift signature than the calibrated one.
- Record **demonstrations** for behaviour cloning (item 23) —
  every joint position + the operator's intended action at every
  timestep is the standard imitation-learning dataset shape.

---

## 8. Synthetic text and barcode renders

**What it is.** A picture of a label or screen with the
ground-truth content **already known** because we rendered it.
Three sub-types matter here:

- **Printed-label text** — the sticker on a vial saying
  `KETCHUP_A_R1 / 2026-06-10 / DODAO`. OCR ground truth is the
  string we typed when we generated the texture.
- **1D / 2D barcodes** — Code-128, QR. Ground truth is the
  payload string.
- **LCD / 7-segment readings** — the balance display, the
  centrifuge timer, the HPLC status panel. Ground truth is the
  number / state we asked the texture generator to render.

**When useful.** Anywhere the robot needs to read something a
human normally would. Step 7 (label OCR) and Step 8 (barcode
scan) lean on this heavily; Step 1 (balance display) needs the
LCD variant.

---

## 9. Fluid-level and state-transition frame sequences

**What it is.** A *sequence* of RGB frames showing a process
unfolding — liquid rising in a vial as the pipette dispenses,
ketchup blob dissolving in solvent, pellet packing at the bottom
of a Falcon tube as the centrifuge spins. Each frame is tagged
with the **state value** at that moment: `volume_ml`,
`dissolved_fraction`, `pellet_height_mm`, …

**When useful.** When the question is **"have we reached the
target state yet?"** Examples:

- Step 5 — stop the pipette squeeze the instant the vial fill
  reaches 1.5 mL.
- Step 2 — stop swirling when the ketchup blob has fully
  dissolved.
- Step 4 — wait until the supernatant / pellet boundary has
  stabilised before reaching in.

**The Gazebo caveat.** Gazebo's physics is rigid-body. It does
**not** simulate fluid. So fluid frames are *faked* by scripted
visual props (a translucent water cylinder whose height shrinks
on a fake-pour event, for instance). The labels are still real
ground truth because we control the script.

---

## 10. Camera calibration sets

**What it is.** Two flavours that look the same on disk but
serve different ends:

- **Intrinsics** — many synthetic images of a virtual
  checkerboard placed at known random poses in front of the
  camera. Feed to `cv2.calibrateCamera` to get focal length,
  principal point, distortion coefficients.
- **Hand-eye** — sets of `(arm pose, marker-in-camera pose)`
  pairs collected as the arm waves a marker around. Feed to
  `cv2.calibrateHandEye` to get the camera-to-arm transform.

**When useful.** As a **smoke test** that the calibration code
works before you ever run it on the real cell — the sim already
knows the true intrinsics and the true hand-eye transform, so
the output of the calibration script must match.

**Already used in.** [`exercises/12-hand-eye-calibration/`](../../../exercises/12-hand-eye-calibration/).

---

## 11. Demonstration trajectories (state, action pairs)

**What it is.** A long file recording every `(observation,
action)` pair from a **scripted "expert"** running the full
workflow once. Observation = joint state + relevant sensor data;
action = the next desired pose / joint velocity. One file per
demonstration. Hundreds of demonstrations per training run.

**When useful.** Imitation learning. The standard inputs to
behaviour cloning (item 23), Diffusion Policy, ACT, and most
"learning from one demo" methods are exactly this shape.

**Why synthetic is the right call.** A teleoperated human demo
on the real arm is slow (one demo per minute). A scripted
"do-the-task" loop in sim can crank out a thousand demos
overnight, each with a different randomised start state, ready
for the model to imitate.

---

## 12. Failure-case datasets

**What it is.** Frames or trajectories deliberately captured
under **broken** conditions, each tagged with the failure mode:
`vial_tipped_over`, `beaker_overflowing`, `filter_clogged`,
`label_crooked`, `cap_missed_threads`, `wrong_vial_in_slot`.

**When useful.** A perception model trained only on nominal
data **silently rubber-stamps** an unsafe scene. Failure-case
data is what teaches it to raise a flag.

**Why synthetic is the right call.** Capturing a "vial tipped
over" frame in a real lab means actually tipping a vial in a
real lab. In sim you flip an SDF angle. Thousands of failure
frames per failure mode are free.

---

## Quick cheat-sheet

The per-step files below pick a subset of these for each
workflow step. Here is the at-a-glance map:

| Step | Most useful types |
|---|---|
| 1 — Weighing       | 8 (LCD reading), 6 (F/T as scale alternative), 11 (demos for fine pour) |
| 2 — Dissolution    | 9 (mix progress), 5 (pose ground truth), 6 (swirl detection) |
| 3 — Dilution       | 3 (fill-mark keypoint), 9 (meniscus crossing), 5 (flask pose) |
| 4 — Filtering      | 2 (pellet / supernatant mask), 6 (filter clog F/T), 5 (poses) |
| 5 — Transfer       | 3 (vial mouth keypoint), 9 (vial fill level), 6 (drip detection) |
| 6 — Capping        | 6 (torque-to-stop), 5 (cap pose), 12 (mis-thread failures) |
| 7 — Labelling      | 8 (label text OCR), 3 (label edge keypoints), 12 (crooked label) |
| 8 — Placement      | 5 (rack / tray / vial poses), 8 (barcode payloads), 6 (z-force on insert) |

The per-step files explain *why* those types are picked and
what the label format looks like.
