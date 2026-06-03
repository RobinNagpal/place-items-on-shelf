# Learning Checklist — Small Software Exercises For Arm Robotics

A flat list of small, distinct software exercises that build the skills
needed for an arm-robotics project. Each one is meant to take **a few
hours up to two days**, run **entirely in simulation** (Gazebo, Isaac
Sim, or MuJoCo), and **stand on its own** — you do not have to do them
in order.

> **Scope.** Software only. No hardware design, no wiring, no mechanical
> build. No full end-to-end pick-and-place project — those live in
> [Layer 4](04-integration-and-bring-up/). One fixed arm only — mobile
> bases, humanoids, and drones are not in scope.

Each item lists:

- **Goal** — the one thing you should be able to do at the end.
- **Why it matters** — where this skill plugs into a real arm project.
- **Done when** — a concrete check, so you know to stop.
- **Time** — a rough estimate. Half a day = 3–4 hours of focused work.

## A. Simulation setup & understanding

These are mostly *configure and observe* tasks — no algorithms to
implement.

- [ ] **1. Create a custom Gazebo world**
  - **Goal:** Build a simple SDF world file with a flat table, the arm
    mounted on the table, and 3 coloured cubes spawned on top.
  - **Why it matters:** Every later exercise needs a scene to play in.
    If you cannot edit a world file, you cannot test perception or
    motion changes.
  - **Done when:** `gazebo my_world.sdf` opens and shows the table, the
    arm in its home pose, and 3 cubes you can drag with the mouse.
  - **Time:** 2–4 hours.

- [ ] **2. Read and annotate the arm's URDF (no code)**
  - **Goal:** Open the arm's URDF file, draw the kinematic tree on
    paper, and label which `<link>` is which physical part, which
    `<joint>` rotates around which axis, and what each joint limit is.
  - **Why it matters:** The URDF is the source of truth for the arm.
    Every later tool (MoveIt, RViz, Gazebo) reads it. You cannot debug
    what you do not understand.
  - **Done when:** You can point to any frame in RViz and say what link
    and joint it corresponds to without looking it up.
  - **Time:** 1–2 hours.

## B. Perception — using a camera

Ten distinct ways to use a camera in an arm cell — modern ML, classical
CV, and calibration.

- [ ] **3. Train a tiny YOLO on a custom 5-class dataset**
  - **Goal:** Fine-tune YOLOv8-nano on ~200 labeled images of 5
    household objects (cup, marker, screwdriver, cube, screw).
  - **Why it matters:** Object detection is the most common perception
    block in arm cells.
  - **Done when:** mAP@0.5 on a held-out test set is above 0.7.
  - **Time:** 1 day.

- [ ] **4. Run YOLO live on a Gazebo camera feed**
  - **Goal:** Stream RGB from a virtual camera, run YOLO every frame,
    publish bounding boxes on a ROS 2 topic, and overlay them in RViz.
  - **Why it matters:** Closed-loop perception in sim is the first step
    to sim-to-real.
  - **Done when:** The detection box tracks an object as you drag it in
    Gazebo's GUI.
  - **Time:** 3–6 hours.

- [ ] **5. Score detections automatically against Gazebo ground truth**
  - **Goal:** Use Gazebo's model-state topic as ground truth, compute
    per-frame IoU and a running mAP — no manual labeling.
  - **Why it matters:** You cannot improve a perception model you
    cannot measure.
  - **Done when:** A single script prints IoU per frame and an mAP
    summary at exit.
  - **Time:** 3–6 hours.

- [ ] **6. Tiny classifier quantized for an edge CPU**
  - **Background (plain English):** A "tiny classifier" is a small,
    fast neural network that fits on a low-power computer next to the
    robot (Raspberry Pi, Jetson Nano) instead of a beefy cloud server.
    **MobileNet** is the classic name people use — it is older now
    (2017), so today many people pick **EfficientNet-Lite**,
    **YOLOv8-nano**, or **MobileViT** instead. "Quantized" means we
    convert the model's numbers from 32-bit floats to 8-bit integers.
    That makes the file roughly 4× smaller and 2–3× faster on a CPU,
    with only a tiny drop in accuracy.
  - **Goal:** Train a small classifier (MobileNet, EfficientNet-Lite,
    or YOLOv8-nano) on the same 5 objects, then quantize it to INT8
    with ONNX Runtime or TensorFlow Lite.
  - **Why it matters:** Arm controllers usually run on a Pi-class or
    Jetson-class box where every millisecond and every megabyte
    counts.
  - **Done when:** Inference runs at more than 15 FPS on a single CPU
    core and top-1 accuracy stays within 2% of the full-precision
    model.
  - **Time:** 1 day.

- [ ] **7. Depth-camera point cloud → object centroid**
  - **Goal:** With an RGB-D camera in sim, segment the table plane
    using RANSAC, cluster what's left, and return each cluster's
    centroid in the arm's base frame.
  - **Why it matters:** When object shape/size is known but its
    position is not, point-cloud clustering is faster and simpler than
    deep learning.
  - **Done when:** Centroid agrees with Gazebo ground truth within 1 cm.
  - **Time:** 1 day.

- [ ] **8. ArUco marker 6-DoF pose estimation**
  - **Background (plain English):** ArUco markers are printable square
    black-and-white tags that look like simplified QR codes. Each one
    encodes a unique ID. When a *calibrated* camera sees one, OpenCV
    can compute **exactly where the tag is in 3D space** — both its
    position (x, y, z) and its orientation (roll, pitch, yaw). That
    full position + orientation is what people mean by **6 DoF (six
    degrees of freedom)**. Stick a marker on an object and you instantly
    know where the object is, no machine learning required. Perfect for
    debugging and for tasks where you control what's printed on the
    objects.
  - **Goal:** Render an ArUco tag on a cube face, recover the cube's
    full 6-DoF pose from one camera image using OpenCV's `aruco`
    module.
  - **Why it matters:** The standard "cheat sheet" for precise object
    pose without ML — and the only way to debug whether perception or
    motion is the problem in a real cell.
  - **Done when:** Pose error stays under 5 mm and 2° across 100 random
    object poses.
  - **Time:** 3–6 hours.

- [ ] **9. Camera intrinsics calibration**
  - **Background (plain English):** A camera is not perfect. Its lens
    has a focal length, an image centre that's not quite in the
    middle, and a little barrel or pincushion distortion at the edges.
    **Intrinsics calibration** measures all of these numbers so your
    software can correct for them. You move a printed checkerboard
    around in front of the camera, take ~20 photos of it, and a
    short OpenCV script (`cv2.calibrateCamera`) produces a small
    matrix and a few distortion coefficients. Without this step, any
    later 3D math (point clouds, ArUco pose, hand-eye) will be wrong.
  - **Goal:** Move a virtual checkerboard in front of the sim camera,
    save 20 frames, run `cv2.calibrateCamera`.
  - **Why it matters:** Every downstream geometry calculation needs
    correct intrinsics.
  - **Done when:** Mean reprojection error is below 0.5 px.
  - **Time:** 3–6 hours.

- [ ] **10. Hand-eye calibration (camera ↔ end-effector)**
  - **Background (plain English):** The camera sees the world in *its
    own* coordinate frame. The arm moves in *its own* coordinate
    frame. **Hand-eye calibration** figures out the rigid transform
    that relates the two — i.e. it answers "given an object at point P
    in the camera image, where is it in the arm's frame so I can move
    to it?". The procedure: move the arm to ~20 different poses,
    point the camera at an ArUco marker each time, record both the
    arm's pose and the marker's camera-frame pose, then call OpenCV's
    `calibrateHandEye`. The output is a single 4×4 matrix that you
    plug in everywhere from then on.
  - **Goal:** With the camera mounted on the arm in sim, collect
    20 (arm pose, marker pose) pairs and solve for the camera-to-EE
    transform.
  - **Why it matters:** Without this transform, the arm literally
    cannot move to what the camera sees.
  - **Done when:** Re-projecting a fresh marker detection lands within
    5 mm of the marker's true position.
  - **Time:** 1 day.

- [ ] **11. Classical colour segmentation (no ML)**
  - **Goal:** Find the red cube in a cluttered Gazebo scene using only
    HSV thresholds + connected components.
  - **Why it matters:** When colour is reliable, classical CV is
    faster, simpler, and easier to debug than a neural network.
  - **Done when:** The correct cube is returned under 3 distinct
    lighting setups.
  - **Time:** 2–4 hours.

- [ ] **12. Barcode / QR-code reader on simulated labels**
  - **Goal:** Render QR codes on cube faces in Gazebo, decode them
    with `pyzbar`, and attach each decoded ID to its corresponding
    object in MoveIt's planning scene.
  - **Why it matters:** Identifying *which* of several identical items
    to pick is a common warehouse and lab pattern.
  - **Done when:** 5 cubes with 5 different codes map correctly to
    5 planning-scene objects.
  - **Time:** 3–6 hours.

## C. Other sensors — beyond the camera

The camera is one sensor on the arm. These are the other ones you will
meet in any real cell.

- [ ] **13. Wrist force/torque (F/T) sensor — detect surface contact**
  - **Goal:** Add a 6-axis F/T sensor between the arm's last link and
    its gripper in the URDF. Move the arm down until the published
    z-force exceeds 2 N, then stop.
  - **Why it matters:** F/T sensors are how arms "feel". They detect
    grasps, collisions, surface contact, and pushing forces.
  - **Done when:** The arm stops as soon as it touches the table,
    every time, with no overshoot greater than 5 mm.
  - **Time:** 3–6 hours.

- [ ] **14. Joint effort/current logging during a motion**
  - **Goal:** Subscribe to `/joint_states`, log the `effort` field for
    each joint to a CSV during a 10-second arm motion, plot the result.
  - **Why it matters:** Effort tells you how hard each joint is
    working — the cheapest way to spot collisions, payload limits,
    and unbalanced poses without any extra sensor.
  - **Done when:** A plot shows torque per joint over time, and you
    can point to the spike when the arm picks up a 200 g weight.
  - **Time:** 2–3 hours.

- [ ] **15. Gripper contact sensor — confirm grasp succeeded**
  - **Goal:** Add a Gazebo `contact` sensor to each gripper finger.
    Publish a `grasp_ok` boolean that is true only when both fingers
    report contact with the same object.
  - **Why it matters:** "Did I actually grab it?" is the most common
    failure check in a pick-and-place cell.
  - **Done when:** `grasp_ok` is true 100% of the time on a successful
    grasp and false 100% of the time on an air pinch.
  - **Time:** 3–6 hours.

## D. Motion — task-level commands to MoveIt

The simple idea: **you describe what you want, MoveIt figures out the
joint angles, the trajectory, and the timing.** You do not write IK or
trajectory math yourself.

- [ ] **16. Joint-space "hello world" with MoveIt**
  - **Goal:** Move the arm to a hard-coded joint configuration from a
    20-line Python or C++ script using `MoveGroupInterface`.
  - **Why it matters:** Smallest possible end-to-end test that the
    URDF, controllers, and planner are all working.
  - **Done when:** The arm reaches the goal in sim without warnings.
  - **Time:** 2–4 hours.

- [ ] **17. Cartesian pose goal — let MoveIt do the IK + planning**
  - **Goal:** Ask MoveIt to move the end-effector to a target XYZ +
    orientation (e.g. "10 cm above the red cube, gripper facing
    down"). MoveIt solves the inverse kinematics and plans the
    trajectory; you just hand it the target pose.
  - **Why it matters:** This is the normal way you talk to an arm.
    Almost every higher-level behaviour boils down to a sequence of
    Cartesian pose goals.
  - **Done when:** The end-effector arrives within 5 mm and 2° of the
    requested pose for 10/10 random reachable targets.
  - **Time:** 3–6 hours.

- [ ] **18. Add a table collision object to the planning scene**
  - **Goal:** Insert a static box representing the table into MoveIt's
    planning scene. Verify the planner goes *around* it, not through
    it.
  - **Why it matters:** Real cells always have static obstacles.
    Getting collision objects right is half the planning battle.
  - **Done when:** A goal *under* the table is correctly rejected as
    unreachable.
  - **Time:** 3–6 hours.

- [ ] **19. Hardcoded pick-and-place sequence — instructions only**
  - **Goal:** Write a script with a hard-coded list of 5 poses
    (`home → above_cube → grasp_cube → above_shelf → release_pose`).
    Hand each one to MoveIt in order, open/close the gripper between
    the right pairs, watch the arm execute the whole task.
  - **Why it matters:** Most production cells are built this way:
    *hand-written instructions, MoveIt does the motion*. No learning,
    no planner intelligence above the trajectory level.
  - **Done when:** The arm reliably moves a cube from the table to a
    target spot 30 cm away across 10 consecutive runs.
  - **Time:** 1 day.

## E. Learning — RL, imitation, and LLMs (sim-only)

All four work entirely in simulation. No hardware needed for any of
them.

- [ ] **20. Behavior cloning from one teleop demo**
  - **Goal:** Record a 60-second teleop trajectory (keyboard or
    gamepad → sim arm) for a reach task. Train a small MLP to map
    `(joint state → next action)`. Replay it in sim.
  - **Why it matters:** Imitation learning is the cheapest way to get
    a policy when you cannot easily hand-code one.
  - **Done when:** The policy reaches within 3 cm of the target on
    8/10 fresh runs.
  - **Time:** 1–2 days.

- [ ] **21. PPO reinforcement learning on a reach task**
  - **Goal:** Train a Stable-Baselines3 PPO agent.
    Observation = joint positions + target XYZ.
    Reward = -distance. Episode = 200 steps.
  - **Why it matters:** RL is the bridge between hand-coded motion and
    behaviour that adapts to a moving target.
  - **Done when:** Average episode reward plateaus and success rate is
    above 80%.
  - **Time:** 1–2 days.

- [ ] **22. Tiny VLA inspection (no execution)**
  - **Goal:** Feed a sim image plus an instruction ("pick the red
    cube") to a small VLA model like OpenVLA, log the predicted
    7-DoF action — do **not** execute it on the arm.
  - **Why it matters:** Understand the input/output shape of a VLA
    before trusting it with a motor command.
  - **Done when:** You can explain what each output channel means and
    how it maps to your arm's action space.
  - **Time:** 3–6 hours.

- [ ] **23. LLM-as-router with a human in the loop**
  - **Goal:** Detect objects with YOLO (item 4), hand the JSON to a
    small LLM along with a natural-language instruction ("pick the
    green one"), have the LLM emit the chosen object ID, send that
    ID to MoveIt for execution.
  - **Why it matters:** LLMs make natural-language instructions cheap.
    The engineering work is understanding where they fail.
  - **Done when:** 9/10 natural-language instructions on a 3-object
    scene pick the correct cube.
  - **Time:** 1 day.

## How to use this list

- Treat each item as an **independent exercise**. Pick the skill you
  are weakest in next — not the next number on the list.
- Stick to the time estimate. If an item grows past it, split it.
- After finishing one, write a one-paragraph note: what worked, what
  didn't, what surprised you. That note is more valuable than the
  code.
- These exercises **do not add up to a finished cell**. For that,
  follow the full walkthrough in [`docs/README.md`](README.md).
