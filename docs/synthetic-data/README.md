# Synthetic Data — DoDAO Robotics Offering

This folder is a plain-English guide to the **synthetic data service**
DoDAO sells to robotics teams. The marketing page is
[dodao.io/robotics](https://dodao.io/robotics) and the one-page summary
is on the printed poster.

Use these docs to:

- **Talk to a prospect.** When an outreach email gets a reply, you
  already know exactly what each feature is, who needs it, and which
  tools we use.
- **Scope a project.** Every feature file lists the inputs we need from
  the customer and the outputs we ship.
- **Pick the right pitch.** Most prospects only need one or two of
  these features. The files help you spot which.

## What we sell, in one paragraph

> Real-world robotics data is **slow and expensive** to collect and
> label. A simulator already knows the truth of every pose, every
> contact force, and every pixel for free. We turn that truth into
> **labelled training data** — images, masks, depth, 6-DoF poses,
> grasp points, sensor traces, expert demonstrations — packaged in
> the format the customer's training code already reads.

## The six features

One file per feature. Each file answers: **what is it**, **who uses
it**, **the tools / libraries / frameworks involved**, **what we ship**,
**how we generate it**, and **what to say in a sales conversation**.

| # | Feature | What the customer trains with it |
|---|---------|-----------------------------------|
| 1 | [Detection images and masks](features/01-detection-images-and-masks.md) | YOLO, Mask R-CNN, YOLOv8-seg, SAM fine-tunes |
| 2 | [Depth, pose, and grasp labels](features/02-depth-pose-and-grasp-labels.md) | GraspNet, ContactGraspNet, AnyGrasp, custom pose estimators |
| 3 | [Demonstration trajectories](features/03-demonstration-trajectories.md) | Behaviour Cloning, ACT, Diffusion Policy, OpenVLA, Pi-0 |
| 4 | [Rare and edge cases](features/04-rare-and-edge-cases.md) | Safety classifiers, anomaly detectors, robustness tests |
| 5 | [Non-camera sensors](features/05-non-camera-sensors.md) | Lidar, thermal, ultrasonic, F/T downstream models |
| 6 | [OCR and barcode renders](features/06-ocr-and-barcode-renders.md) | PaddleOCR, EasyOCR, pyzbar, ZXing |

## How we generate the data (the four methods)

These are the techniques we use *inside* the simulator. They show up
across every feature above. A single project usually combines two or
three. Long-form explanation in
[`how-we-generate-it.md`](how-we-generate-it.md).

- **Domain randomisation** — change lighting, textures, camera angles,
  object poses, and distractors on every frame. Makes the model
  robust enough to survive a real camera.
- **Procedural scenes** — code builds the scene from scratch each
  time (random rack layout, random clutter). Opposite of one
  hand-built world rendered many times.
- **Photo-real rendering** — ray-traced images with physically-based
  materials. Important when the model has to run on a real camera
  with real glare and shadows.
- **Sensor noise modelling** — add realistic noise on top of the
  perfect sensor reading. Real RealSense depth has speckle. Real F/T
  sensors drift. The model has to see noise in training or it falls
  over in production.

## What we ship (the formats)

We hand the customer a project folder in the format their training
code already reads:

| Format | Used by |
|--------|---------|
| **LeRobot** (HF Datasets + video) | Hugging Face LeRobot policies (ACT, Diffusion Policy, Pi-0) |
| **Robomimic** (HDF5) | Stanford Robomimic policies, many academic baselines |
| **RLDS** (TFDS) | Google / DeepMind RT-X family, Octo |
| **COCO JSON** | The de facto detection dataset format (YOLOv8 supports it directly) |
| **YOLO labels** (`.txt` per image) | Ultralytics YOLOv5 / v8 / v11 training |
| **Custom HDF5** | In-house pipelines that already speak HDF5 |
| **MCAP rosbags** | ROS 2 teams that consume data through `ros2 bag` |

If the customer's pipeline reads a format that is not on this list, we
add a small writer for it as part of the project.

## What we use to build it

- **Gazebo** (Ignition / "modern Gazebo") — ROS 2-native, free,
  fast iteration. Default pick for geometric tasks with strong
  priors.
- **Isaac Sim** (NVIDIA Omniverse) — photo-real rendering, GPU
  physics, the **Replicator** Python API for randomisation. Default
  pick when training a vision model that has to ship to a real camera.
- Picked per project. The poster says it plainly: "We pick Gazebo or
  Isaac Sim based on your robot."

## Related reading

- [`industry-methods.md`](industry-methods.md) — long-form view of how
  the industry produces synthetic data in 2026 (Replicator, Kubric,
  Unity Perception, Drake, CARLA, Omniverse, Gaussian splats, …) and
  where Gazebo fits.
- [`../hplc-autosamplers/synthetic-data/`](../hplc-autosamplers/synthetic-data/) —
  the HPLC autosampler case study. Same nine-type catalogue, scoped to
  one specific cell. Useful as a worked example.

## Quick decision tree for a sales call

1. **"We have a YOLO model but it does not work on the real camera."**
   → Feature 1 (detection images + masks) with **photo-real rendering**
   + **domain randomisation**.
2. **"We're building a robot that picks novel objects."**
   → Feature 2 (depth / pose / grasp labels) — feeds GraspNet-style
   models.
3. **"We're training an imitation-learning policy and need more
   demos."** → Feature 3 (demonstration trajectories) in LeRobot or
   Robomimic format.
4. **"Our model fails on damaged / occluded products."**
   → Feature 4 (rare and edge cases).
5. **"We use lidar / thermal / F/T, not just cameras."**
   → Feature 5 (non-camera sensors).
6. **"We have to read codes, barcodes, or labels."**
   → Feature 6 (OCR / barcode renders).
