# How industry produces synthetic data — methods and platforms

This file is **not Gazebo-specific**. It lists the main ways teams
actually generate synthetic data in 2026, says **which simulation
platform does each one well**, and names who uses it. The point is
to know the landscape so you can decide what is worth adopting if
this project ever moves past learning into production.

We stay on **Gazebo Ignition** in this repo because it is ROS-native,
free, and good enough for teaching. Most of the methods below also
exist in Gazebo at a lower fidelity. The table at the end says where
to go if you outgrow it.

## The methods

### 1. Domain randomization

- **What it is.** Vary lighting, textures, camera pose, object pose,
  and background distractors on every rendered frame. The model
  trains on the variation, so it does not overfit to "what sim looks
  like" and transfers better to the real camera.
- **Best platform.** NVIDIA Isaac Sim with **Replicator** (a Python
  API just for this).
- **Also used on.** Unity Perception Package, Blender + Python.
- **Who uses it.** OpenAI (Dactyl cube), Boston Dynamics, Amazon
  Robotics, Figure, most sim-to-real manipulation teams.

### 2. Procedural scene generation

- **What it is.** Code generates the whole scene every time — random
  objects on random shelves with random clutter. Opposite of one
  hand-built world rendered many ways.
- **Best platform.** NVIDIA Replicator, Google **Kubric**
  (open-source, Blender backend).
- **Who uses it.** Google DeepMind (RT-2 training data), Tortuga
  AgTech, Cognex defect detection.

### 3. Photo-realistic rendering with PBR materials

- **What it is.** Ray-traced images with physically based materials
  — looks close to a real photograph. Important when a sim-trained
  vision model has to run on a real camera.
- **Best platform.** NVIDIA Isaac Sim (RTX path tracer),
  **Unreal Engine 5**, Blender Cycles.
- **Who uses it.** Mercedes-Benz, BMW, every AV company, Foxconn.

### 4. Sensor noise modelling

- **What it is.** Add realistic noise to the perfect sensor reading
  so the model trains on something close to what the real camera or
  depth sensor produces. RealSense has speckle, Kinect has dropout,
  F/T sensors drift.
- **Best platform.** Isaac Sim ships RealSense, Kinect, ZED, and
  Velodyne noise models out of the box.
- **Also used on.** NVIDIA DRIVE Sim (LiDAR), MuJoCo (contact / force
  noise).
- **Who uses it.** Anyone serious about sim-to-real transfer.

### 5. Imitation-learning demonstration sets

- **What it is.** Log `(observation, action)` per timestep while a
  scripted or teleop expert does the task. Hundreds of demos become
  training data for Behaviour Cloning, Diffusion Policy, or ACT.
- **Best platform.** Standard formats are **Robomimic** (HDF5,
  Stanford), **LeRobot** (Parquet, Hugging Face), and **RLDS**
  (TensorFlow Datasets, Google). They run on top of Isaac Lab,
  MuJoCo, or Robosuite.
- **Who uses it.** Stanford ALOHA, Toyota Research Institute,
  Physical Intelligence, Skild AI, every manipulation startup.

### 6. Reinforcement-learning environment data

- **What it is.** Wrap the simulator as a Gym / Gymnasium env with a
  reward function. The data is "rollouts" — sequences of
  `(s, a, r, s')` — generated *during* training, not in advance.
- **Best platform.** **Isaac Lab** (GPU-parallel, thousands of envs
  on one GPU), **MuJoCo** (contact-rich tasks), **Drake** (formal-
  method-friendly).
- **Who uses it.** DeepMind, OpenAI, every academic RL group.

### 7. Scenario / failure-case authoring

- **What it is.** A YAML or Python config that says "perturb the
  scene this way, run the expert, label the outcome." Used to build
  safety / edge-case datasets without hand-collecting failures.
- **Best platform.** **CARLA** scenario runner (AV), **NVIDIA DRIVE
  Sim** (OEMs), **Isaac Lab** scenario authoring (manipulation),
  **Drake** scenario harness.
- **Who uses it.** Waymo (millions of scenarios per night), Cruise,
  Mobileye, Zoox.

### 8. Tactile / contact-rich data

- **What it is.** Force, torque, slip, and tactile-pixel data from
  contact-rich tasks like insertion, threading, peg-in-hole.
- **Best platform.** **MuJoCo** — the contact model is the gold
  standard. **Drake** — second. Isaac Sim — third, improving fast.
- **Who uses it.** Meta AI (DIGIT tactile sensor), TRI, Sanctuary AI,
  MIT CSAIL.

### 9. Synthetic text / barcode / label data

- **What it is.** Pictures of vials, boxes, or screens with
  generated text or codes baked on, used to test OCR and barcode
  pipelines.
- **Best platform.** Isaac Sim **Replicator** has a randomized text
  generator built in (font, glare, perspective, occlusion in one
  config). Otherwise: **Blender + Pillow** to generate textures and
  drop them into any renderer.
- **Who uses it.** Amazon (package label OCR), Walmart (shelf
  labels), pharma robots.

### 10. Camera-calibration sets

- **What it is.** Checkerboard / ChArUco / AprilTag images at known
  poses. Used to verify that `cv2.calibrateCamera` and
  `cv2.calibrateHandEye` recover the truth in sim before the real
  camera is bolted in.
- **Best platform.** **All renderers are equivalent here** — Gazebo,
  Isaac Sim, Unity, Blender. The math doesn't care.
- **Who uses it.** Every camera-arm cell builder.

### 11. Digital-twin rendering

- **What it is.** A near-exact 3D replica of a real factory /
  warehouse / cell, used to train models for that *specific* site.
- **Best platform.** **NVIDIA Omniverse** is the market leader.
  Unity Industrial Insight is the runner-up.
- **Who uses it.** Siemens, BMW, Foxconn, Hyundai.

### 12. 3D-scanned / Gaussian-splat assets

- **What it is.** Use real-world scanned objects (NeRF, Gaussian
  splatting, photogrammetry) as sim assets — far cheaper than CAD
  modelling everything.
- **Best platform.** **NVIDIA Omniverse** (ingests USD + splats),
  **Unreal Engine 5** (Nanite). Capture tools: LumaAI, Polycam,
  KIRI Engine.
- **Who uses it.** Skild AI, Physical Intelligence, Wayve.

## Where Gazebo fits in 2026

Gazebo is the **ROS-native default** and the right tool when:

- You are learning the stack (this repo's case).
- The task is geometric, not visual — pick-and-place with strong
  priors (vials in known slots, racks in known fixtures).
- You need MoveIt 2 / Nav2 / `ros2 control` to work out of the box.
- Budget is zero.

Gazebo is the **wrong tool** when:

- You need photo-realistic RGB — use Isaac Sim or Unreal.
- You need massive parallel RL — use Isaac Lab (≈ 1000× faster).
- You need contact-rich force data — use MuJoCo or Drake.
- You need a digital twin of a real site — use Omniverse.

For this project we stick with Gazebo because the goal is teaching.
If this work later becomes a service offering, the platform
conversation reopens — and the answer in most categories above is
**NVIDIA Isaac Sim**.

## Summary table

| # | Method | Best platform | Gazebo capable? |
|---|--------|---------------|-----------------|
| 1 | Domain randomization | Isaac Sim Replicator | Manual scripts |
| 2 | Procedural scene generation | Replicator, Kubric | Manual scripts |
| 3 | PBR / photo-realistic rendering | Isaac Sim, Unreal 5 | No |
| 4 | Sensor noise modelling | Isaac Sim | Manual post-processing |
| 5 | Imitation-learning demos | Robomimic, LeRobot, RLDS | Yes (custom format) |
| 6 | RL environments | Isaac Lab, MuJoCo | Yes (slow, single-env) |
| 7 | Scenario / failure-case authoring | CARLA, DRIVE Sim, Isaac Lab | Manual scripts |
| 8 | Tactile / contact-rich | MuJoCo, Drake | Weak — contact chatter |
| 9 | Synthetic OCR / barcode | Replicator, Blender | Yes (texture map) |
| 10 | Camera calibration | All equivalent | Yes |
| 11 | Digital-twin rendering | NVIDIA Omniverse | No |
| 12 | 3D-scanned / splat assets | Omniverse, Unreal 5 | No |
