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

## Case study used throughout — HPLC autosampler tray loading

Most items below carry an **Autosampler tie-in** note. It maps the
generic exercise onto this project's medium-term target task:

> **Pick a 2 mL HPLC sample vial from an inbound rack, read its barcode,
> and place it in the correct slot of an HPLC autosampler tray.**

Key facts you will see referenced:

- **Vial:** 12 mm × 32 mm glass cylinder, ~5–10 g, fragile, often with a
  coloured cap.
- **Source:** inbound rack with a ~6×12 grid of vials, sometimes shifted
  slightly on the bench.
- **Destination:** autosampler tray with a fixed grid (54 or 96 slots).
- **Workspace:** ~40 × 40 × 40 cm, bench-mounted arm, humans nearby.
- **Precision needed:** ~2 mm at the slot.
- **Cycle time:** 10–20 s per vial.
- **Logging:** every (barcode → slot) pair written to LIMS.

The full problem statement lives in `docs/hplc-autosamplers/` (added in
a separate PR — link will resolve after both merge).

## How each item is written

- **Goal** — the one thing you should be able to do at the end.
- **Why it matters** — where this skill plugs into a real arm project.
- **Done when** — a concrete check, so you know to stop.
- **Time** — a rough estimate. Half a day = 3–4 hours of focused work.
- **Autosampler tie-in** *(when applicable)* — how to do this exercise
  using the HPLC vial-loading scenario.

## A. Simulation setup & understanding

These are mostly *configure and observe* tasks — no algorithms to
implement.

- [x] **1. Create a custom Gazebo world** — see [`../exercises/01-custom-gazebo-world/`](../exercises/01-custom-gazebo-world/)
  - **Goal:** Build a simple SDF world file with a flat table, the arm
    mounted on the table, and 3 coloured cubes spawned on top.
  - **Why it matters:** Every later exercise needs a scene to play in.
    If you cannot edit a world file, you cannot test perception or
    motion changes.
  - **Done when:** `gazebo my_world.sdf` opens and shows the table, the
    arm in its home pose, and 3 cubes you can drag with the mouse.
  - **Time:** 2–4 hours.
  - **Autosampler tie-in:** model the actual cell — bench, inbound
    6×12 rack, autosampler tray (start with the 54-slot 6×9 variant),
    12 mm × 32 mm vial cylinders with caps, and the bench-mounted
    myCobot. This world is the canvas every later exercise uses.

- [x] **2. Read and annotate the arm's URDF (no code)** — see [`../exercises/02-read-and-annotate-urdf/`](../exercises/02-read-and-annotate-urdf/)
  - **Goal:** Open the arm's URDF file, draw the kinematic tree on
    paper, and label which `<link>` is which physical part, which
    `<joint>` rotates around which axis, and what each joint limit is.
  - **Why it matters:** The URDF is the source of truth for the arm.
    Every later tool (MoveIt, RViz, Gazebo) reads it. You cannot debug
    what you do not understand.
  - **Done when:** You can point to any frame in RViz and say what link
    and joint it corresponds to without looking it up.
  - **Time:** 1–2 hours.
  - **Autosampler tie-in:** confirm the myCobot 280's reach (~280 mm)
    covers the whole 40 × 40 × 40 cm workspace from its bench mount.
    Catch any out-of-reach slot here, before any code exists.

## B. Perception — using a camera

Distinct ways to use a camera in an arm cell — modern ML, classical CV,
and calibration.

- [ ] **3. Train a tiny YOLO on a custom 5-class dataset**
  - **Goal:** Fine-tune YOLOv8-nano on ~200 labeled images of 5
    household objects (cup, marker, screwdriver, cube, screw).
  - **Why it matters:** Object detection is the most common perception
    block in arm cells.
  - **Done when:** mAP@0.5 on a held-out test set is above 0.7.
  - **Time:** 1 day.
  - **Autosampler tie-in:** swap the household-object set for `vial`,
    `empty_slot`, `rack_edge`, `tray_edge`, `cap_red`. That single
    detector tells the script which source slots still have vials,
    which tray slots are free, and roughly where the rack/tray are.

- [ ] **4. Run YOLO live on a Gazebo camera feed**
  - **Goal:** Stream RGB from a virtual camera, run YOLO every frame,
    publish bounding boxes on a ROS 2 topic, and overlay them in RViz.
  - **Why it matters:** Closed-loop perception in sim is the first step
    to sim-to-real.
  - **Done when:** The detection box tracks an object as you drag it in
    Gazebo's GUI.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** point the camera at the simulated rack,
    publish a `vials_in_rack` topic listing each detected vial's
    slot index. The pick-and-place script subscribes to it.

- [ ] **5. Score detections automatically against Gazebo ground truth**
  - **Goal:** Use Gazebo's model-state topic as ground truth, compute
    per-frame IoU and a running mAP — no manual labeling.
  - **Why it matters:** You cannot improve a perception model you
    cannot measure.
  - **Done when:** A single script prints IoU per frame and an mAP
    summary at exit.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** spawn 54 vials in known rack positions,
    measure how often the detector finds them all and how often it
    confuses adjacent vials. Sets the perception bar before going
    near real glass.

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
  - **Autosampler tie-in:** the controller next to the autosampler is
    a Pi 4 or a Jetson Nano. A quantized vial detector keeps every
    frame on-device — important for the GMP audit trail (no images
    leaving the lab network).

- [ ] **7. Instance segmentation — pixel masks instead of bounding boxes**
  - **Background (plain English):** YOLO draws a *rectangle* around an
    object. Most of that rectangle is actually background. **Instance
    segmentation** goes further — it labels every pixel that belongs
    to each object, so you get the object's exact silhouette. Modern
    options: **YOLOv8-seg** (a YOLO variant that outputs masks),
    **Mask R-CNN** (the classic), and **SAM / SAM 2** (Meta's
    foundation segmentation model — works zero-shot but is heavier).
  - **Goal:** Run a pre-trained YOLOv8-seg or SAM on Gazebo frames.
    Publish per-pixel masks for each detected object on a ROS 2
    topic. Visualise in RViz.
  - **Why it matters:** Bounding boxes are useless for irregular
    objects, occluded objects, or anything close to clutter. Pixel
    masks are what point-cloud math, grasp-point estimation, and any
    "exact contour" task actually need.
  - **Done when:** Mask IoU vs Gazebo ground truth is above 0.7 per
    object across 10 random scenes.
  - **Time:** 1 day.
  - **Autosampler tie-in:** vials sit ~14 mm centre-to-centre, so
    their bounding boxes badly overlap. Pixel masks let you tell vial
    #34 from vial #35 reliably, and check "the slot to the right is
    empty" before reaching in.

- [ ] **8. Depth-camera point cloud → object centroid**
  - **Goal:** With an RGB-D camera in sim, segment the table plane
    using RANSAC, cluster what's left, and return each cluster's
    centroid in the arm's base frame.
  - **Why it matters:** When object shape/size is known but its
    position is not, point-cloud clustering is faster and simpler than
    deep learning.
  - **Done when:** Centroid agrees with Gazebo ground truth within 1 cm.
  - **Time:** 1 day.
  - **Autosampler tie-in:** for the inbound rack, RGB-D gives the
    exact (x, y, z) of each vial top — even when a tech bumps the
    rack a few millimetres. Tray slots are fixed; source-rack vials
    often aren't.

- [ ] **9. Depth-based grasp-point estimation**
  - **Background (plain English):** Knowing *where* an object is is
    not enough — pick-and-place needs to know *how* to grip it
    (where the fingers should close, from which direction). The
    simplest version (called an **antipodal grasp**): take the
    object's point cloud, run PCA to find its principal axes, and
    choose a grasp at the centroid, fingers closing along the
    *shortest* axis (perpendicular to the longest one). For more
    complex shapes there are learned methods like **GG-CNN** and
    **Contact-GraspNet** — start with the PCA baseline first.
  - **Goal:** From an RGB-D image of a single cube, compute a 3D
    grasp pose (point + approach direction) using the PCA antipodal
    method. Publish it as a pose for MoveIt to use.
  - **Why it matters:** This is the bridge between "I see the object"
    and "I can pick it up". Every pick-and-place cell needs it.
  - **Done when:** The arm successfully grasps and lifts the cube
    using the proposed grasp pose for 8/10 random cube orientations.
  - **Time:** 1 day.
  - **Autosampler tie-in:** vials are simple vertical cylinders, so
    PCA antipodal collapses to "grip the body at its centroid,
    fingers closing across the diameter". One pattern handles every
    vial type the autosampler accepts.

- [ ] **10. ArUco marker 6-DoF pose estimation**
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
  - **Autosampler tie-in:** stick one ArUco tag on a corner of the
    source rack and another on the autosampler tray. The arm can
    then re-locate both objects after a tech bumps them, without
    re-running hand-eye calibration.

- [ ] **11. Camera intrinsics calibration**
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
  - **Autosampler tie-in:** the ±2 mm placement requirement falls
    apart fast with bad intrinsics — at the typical working distance,
    even 0.5 px reprojection error is roughly 1 mm in the world.
    Always do this first.

- [ ] **12. Hand-eye calibration (camera ↔ end-effector)**
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
  - **Autosampler tie-in:** this is what turns "vial seen at pixel
    (320, 240)" into "vial at slot B5, robot-frame (X, Y, Z)".
    Without it, ±2 mm placement is impossible. Re-run any time the
    camera is bumped.

- [ ] **13. Classical colour segmentation (no ML)**
  - **Goal:** Find the red cube in a cluttered Gazebo scene using only
    HSV thresholds + connected components.
  - **Why it matters:** When colour is reliable, classical CV is
    faster, simpler, and easier to debug than a neural network.
  - **Done when:** The correct cube is returned under 3 distinct
    lighting setups.
  - **Time:** 2–4 hours.
  - **Autosampler tie-in:** labs often colour-code vial caps (blue =
    standards, red = unknowns, green = QC). An HSV threshold picks
    out "all red-cap vials" in one pass — useful when the LIMS asks
    for a specific subset of the rack.

- [ ] **14. Barcode / QR-code reader on simulated labels**
  - **Goal:** Render QR codes on cube faces in Gazebo, decode them
    with `pyzbar`, and attach each decoded ID to its corresponding
    object in MoveIt's planning scene.
  - **Why it matters:** Identifying *which* of several identical items
    to pick is a common warehouse and lab pattern.
  - **Done when:** 5 cubes with 5 different codes map correctly to
    5 planning-scene objects.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** the spec **requires** reading each vial's
    barcode and writing the `(barcode → slot)` pair to LIMS — this
    item *is* that step. Not optional, and tested every run.

## C. Other sensors — beyond the camera

The camera is one sensor on the arm. These are the other ones you will
meet in any real cell.

- [ ] **15. Wrist force/torque (F/T) sensor — detect surface contact**
  - **Goal:** Add a 6-axis F/T sensor between the arm's last link and
    its gripper in the URDF. Move the arm down until the published
    z-force exceeds 2 N, then stop.
  - **Why it matters:** F/T sensors are how arms "feel". They detect
    grasps, collisions, surface contact, and pushing forces.
  - **Done when:** The arm stops as soon as it touches the table,
    every time, with no overshoot greater than 5 mm.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** lowering a vial into a slot is where you
    crush glass. Stop the descent the instant z-force exceeds ~1 N
    — that's the "vial bottom touched the slot" signal. Standard
    glass-handling safeguard.

- [ ] **16. Joint effort/current logging during a motion**
  - **Goal:** Subscribe to `/joint_states`, log the `effort` field for
    each joint to a CSV during a 10-second arm motion, plot the result.
  - **Why it matters:** Effort tells you how hard each joint is
    working — the cheapest way to spot collisions, payload limits,
    and unbalanced poses without any extra sensor.
  - **Done when:** A plot shows torque per joint over time, and you
    can point to the spike when the arm picks up a 200 g weight.
  - **Time:** 2–3 hours.
  - **Autosampler tie-in:** log effort across a full 96-vial run. If a
    particular slot consistently shows a torque spike, the arm is
    grazing something there — catch a slightly misaligned tray
    before a vial breaks.

- [ ] **17. Gripper contact sensor — confirm grasp succeeded**
  - **Goal:** Add a Gazebo `contact` sensor to each gripper finger.
    Publish a `grasp_ok` boolean that is true only when both fingers
    report contact with the same object.
  - **Why it matters:** "Did I actually grab it?" is the most common
    failure check in a pick-and-place cell.
  - **Done when:** `grasp_ok` is true 100% of the time on a successful
    grasp and false 100% of the time on an air pinch.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** `grasp_ok` must be true before the arm
    lifts away from the rack. A vial that looks gripped but isn't is
    the most expensive failure in this cell — a 0.5 m drop onto a
    tile floor.

## D. Motion — task-level commands to MoveIt

The simple idea: **you describe what you want, MoveIt figures out the
joint angles, the trajectory, and the timing.** You do not write IK or
trajectory math yourself.

- [x] **18. Joint-space "hello world" with MoveIt** — see [`../exercises/18-joint-space-hello-moveit/`](../exercises/18-joint-space-hello-moveit/)
  - **Goal:** Move the arm to a hard-coded joint configuration from a
    20-line Python or C++ script using `MoveGroupInterface`.
  - **Why it matters:** Smallest possible end-to-end test that the
    URDF, controllers, and planner are all working.
  - **Done when:** The arm reaches the goal in sim without warnings.
  - **Time:** 2–4 hours.
  - **Autosampler tie-in:** use it to define and reach a "park / safe"
    pose between trays, where the arm is fully out of the
    autosampler drawer's path so a tech can swap trays.

- [ ] **19. Cartesian pose goal — MoveIt as the IK solver**
  - **Goal:** Ask MoveIt to move the end-effector to a target XYZ +
    orientation (e.g. "10 cm above the red cube, gripper facing
    down"). MoveIt solves the inverse kinematics (target pose →
    joint angles) and plans the trajectory; you only hand it the
    target pose.
  - **Why it matters:** This is **the** standard way to do inverse
    kinematics in practice — let MoveIt's KDL/TracIK solver do it
    instead of writing the math yourself. Almost every higher-level
    behaviour boils down to a sequence of Cartesian pose goals.
  - **Done when:** The end-effector arrives within 5 mm and 2° of the
    requested pose for 10/10 random reachable targets.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** the whole workflow reduces to about 6
    Cartesian goals per vial — `above_source → grasp → lift →
    above_dest → lower → release`. MoveIt solves the IK at each
    step; you only supply the poses.

- [ ] **20. Collision avoidance — add a table to the planning scene**
  - **Goal:** Insert a static box representing the table into MoveIt's
    planning scene. Verify the planner goes *around* it, not through
    it. Repeat with a second box representing a wall.
  - **Why it matters:** Real cells always have static obstacles.
    Collision objects in the planning scene are how the arm knows to
    avoid them — no extra logic required.
  - **Done when:** A goal *under* the table is correctly rejected as
    unreachable. Adding the wall changes the planned path visibly.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** add the autosampler housing, the open
    drawer rails, the inbound rack, and a "no-fly volume" above each
    already-loaded slot. The planner then refuses to lower the arm
    onto an occupied slot.

- [ ] **21. Hardcoded pick-and-place sequence — instructions only**
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
  - **Autosampler tie-in:** **this is the v1 implementation of the
    autosampler task.** Take a CSV of
    `(source_slot, dest_slot, barcode)` rows, generate the pose pairs
    from the rack and tray geometry, execute in order. No learning,
    only barcode reading on top.

## E. Learning — RL, imitation, and LLMs (sim-only)

All four work entirely in simulation. No hardware needed for any of
them.

- [ ] **22. Behavior cloning from one teleop demo**
  - **Goal:** Record a 60-second teleop trajectory (keyboard or
    gamepad → sim arm) for a reach task. Train a small MLP to map
    `(joint state → next action)`. Replay it in sim.
  - **Why it matters:** Imitation learning is the cheapest way to get
    a policy when you cannot easily hand-code one.
  - **Done when:** The policy reaches within 3 cm of the target on
    8/10 fresh runs.
  - **Time:** 1–2 days.
  - **Autosampler tie-in:** useful for the tricky last centimetre —
    teleoperate 20 demos of lowering a vial into a slot, train a
    small policy that handles slight tray misalignment more
    smoothly than the hard-coded version.

- [ ] **23. PPO reinforcement learning on a reach task**
  - **Goal:** Train a Stable-Baselines3 PPO agent.
    Observation = joint positions + target XYZ.
    Reward = -distance. Episode = 200 steps.
  - **Why it matters:** RL is the bridge between hand-coded motion and
    behaviour that adapts to a moving target.
  - **Done when:** Average episode reward plateaus and success rate is
    above 80%.
  - **Time:** 1–2 days.
  - **Autosampler tie-in:** not for v1 — vials are too precious to
    crash during training. Later use: train *in sim* to handle "the
    rack is rotated 3°" or "one slot is broken", then deploy the
    learned policy once it is reliable.

- [ ] **24. Tiny VLA inspection (no execution)**
  - **Goal:** Feed a sim image plus an instruction ("pick the red
    cube") to a small VLA model like OpenVLA, log the predicted
    7-DoF action — do **not** execute it on the arm.
  - **Why it matters:** Understand the input/output shape of a VLA
    before trusting it with a motor command.
  - **Done when:** You can explain what each output channel means and
    how it maps to your arm's action space.
  - **Time:** 3–6 hours.
  - **Autosampler tie-in:** show the model an image of the rack with
    the prompt "pick the vial in row 2, column 5". Check whether the
    predicted action lands anywhere near that vial — sets your
    expectations before considering a VLA for a real lab cell.

- [ ] **25. LLM-as-router with a human in the loop**
  - **Goal:** Detect objects with YOLO (item 4), hand the JSON to a
    small LLM along with a natural-language instruction ("pick the
    green one"), have the LLM emit the chosen object ID, send that
    ID to MoveIt for execution.
  - **Why it matters:** LLMs make natural-language instructions cheap.
    The engineering work is understanding where they fail.
  - **Done when:** 9/10 natural-language instructions on a 3-object
    scene pick the correct cube.
  - **Time:** 1 day.
  - **Autosampler tie-in:** natural lab UX — the tech says "load the
    next 12 samples into A1–B6". The LLM expands that into
    `(source_slot, dest_slot)` pairs and hands them to the hardcoded
    pick-place script from item 21.

## How to use this list

- Treat each item as an **independent exercise**. Pick the skill you
  are weakest in next — not the next number on the list.
- Stick to the time estimate. If an item grows past it, split it.
- After finishing one, write a one-paragraph note: what worked, what
  didn't, what surprised you. That note is more valuable than the
  code.
- These exercises **do not add up to a finished cell**. For that,
  follow the full walkthrough in [`docs/README.md`](README.md). For
  the worked HPLC autosampler case study, see the
  `docs/hplc-autosamplers/` folder once it lands on main.
