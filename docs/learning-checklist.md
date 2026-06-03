# Learning Checklist — Small Software Exercises For Arm Robotics

A flat list of small, distinct software exercises that build the skills
needed for an arm-robotics project. Each one is meant to take **a day or
two**, run **entirely in simulation** (Gazebo, Isaac Sim, or MuJoCo), and
**stand on its own** — you do not have to do them in order.

> **Scope.** Software only. No hardware design, no wiring, no mechanical
> build. No full end-to-end pick-and-place project — those live in
> [Layer 4](04-integration-and-bring-up/). One fixed arm only — mobile
> bases, humanoids, and drones are not in scope.

Each item lists:

- **Goal** — the one thing you should be able to do at the end.
- **Why it matters** — where this skill plugs into a real arm project.
- **Done when** — a concrete check, so you know to stop.

## Perception — different ways to use a camera

- [ ] **1. Train a tiny YOLO on a custom 5-class dataset**
  - **Goal:** Fine-tune YOLOv8-nano on ~200 labeled images of 5 household
    objects.
  - **Why it matters:** Object detection is the most common perception
    block in arm cells.
  - **Done when:** mAP@0.5 on a held-out test set is > 0.7.

- [ ] **2. Run YOLO live on a Gazebo camera feed**
  - **Goal:** Stream RGB from a virtual camera, run YOLO every frame,
    publish bounding boxes on a ROS 2 topic, and overlay them in RViz.
  - **Why it matters:** Closed-loop perception in sim is the first step to
    sim-to-real.
  - **Done when:** The detection box tracks an object as you drag it in
    Gazebo's GUI.

- [ ] **3. Score detections automatically against Gazebo ground truth**
  - **Goal:** Use Gazebo's model-state topic as ground truth, compute
    per-frame IoU and a running mAP — no manual labeling.
  - **Why it matters:** You cannot improve a perception model you cannot
    measure.
  - **Done when:** A single script prints IoU per frame and an mAP summary
    at exit.

- [ ] **4. MobileNet-SSD classifier quantized for edge CPUs**
  - **Goal:** Train MobileNet to classify the same 5 objects, then
    quantize to INT8 with ONNX Runtime.
  - **Why it matters:** Arm controllers often run on Pi-class or
    Jetson-class hardware where every millisecond matters.
  - **Done when:** Inference runs at > 15 FPS on a single CPU core.

- [ ] **5. Depth-camera point cloud → object centroid**
  - **Goal:** With an RGB-D camera in sim, segment the table plane with
    RANSAC, cluster what's left, and return each cluster's centroid in
    the arm's base frame.
  - **Why it matters:** When object shape/size is known but pose is not,
    point-cloud clustering is faster and simpler than deep learning.
  - **Done when:** Centroid agrees with Gazebo ground truth within 1 cm.

- [ ] **6. ArUco marker 6-DoF pose estimation**
  - **Goal:** Render an ArUco tag on a cube, recover the full 6-DoF pose
    from one camera image with OpenCV.
  - **Why it matters:** The standard cheat-sheet for precise object pose
    without ML.
  - **Done when:** Pose error stays under 5 mm and 2° across 100 random
    object poses.

- [ ] **7. Camera intrinsics calibration**
  - **Goal:** Move a virtual checkerboard in front of the sim camera, save
    20 frames, run `cv2.calibrateCamera`.
  - **Why it matters:** Every downstream geometry calculation (PnP, point
    cloud, hand-eye) needs intrinsics.
  - **Done when:** Reprojection error is below 0.5 px.

- [ ] **8. Hand-eye calibration (camera ↔ end-effector)**
  - **Goal:** With the camera mounted on the arm, record N robot poses
    and N marker poses, solve `T_camera_to_ee` with OpenCV's
    `calibrateHandEye`.
  - **Why it matters:** Without this transform, the arm cannot move *to*
    what the camera sees.
  - **Done when:** Re-projecting a fresh marker detection lands within
    5 mm of the true cube position.

- [ ] **9. Classical color/shape segmentation**
  - **Goal:** Find the red cube in a cluttered Gazebo scene using only
    HSV thresholds + connected components — no neural network.
  - **Why it matters:** When color is reliable, classical CV is faster,
    simpler, and easier to debug than YOLO.
  - **Done when:** The correct cube is returned under 3 distinct lighting
    setups.

- [ ] **10. Barcode / QR-code reader on simulated labels**
  - **Goal:** Render QR codes on cube faces in Gazebo, decode them with
    `pyzbar`, and attach each decoded ID to its corresponding object in
    MoveIt's planning scene.
  - **Why it matters:** Identifying *which* of several identical items to
    pick is a common warehouse pattern.
  - **Done when:** 5 cubes with 5 different codes map correctly to 5
    planning-scene objects.

## Motion — small experiments with the arm

- [ ] **11. Joint-space "hello world" with MoveGroupInterface**
  - **Goal:** Move the arm to a hard-coded joint configuration from a
    20-line Python or C++ script.
  - **Why it matters:** The smallest end-to-end test that the URDF,
    controllers, and planner all work.
  - **Done when:** The arm reaches the goal in sim without warnings.

- [ ] **12. Add a table collision object to the planning scene**
  - **Goal:** Insert a static box for the table into MoveIt's planning
    scene; verify the planner goes *around* it, not through it.
  - **Why it matters:** Real cells always have static obstacles; getting
    collision objects right is half the planning battle.
  - **Done when:** A goal *under* the table is correctly rejected as
    unreachable.

- [ ] **13. Forward kinematics from the URDF, by hand**
  - **Goal:** Parse the URDF, multiply joint transforms, compare your
    end-effector pose to `/tf`.
  - **Why it matters:** You do not really understand a robot until you
    can compute its FK yourself.
  - **Done when:** Your script agrees with `/tf` to within 1e-4 m and
    1e-4 rad on 100 random joint configurations.

- [ ] **14. Numerical inverse kinematics with KDL or ikpy**
  - **Goal:** Given a target end-effector pose, solve for joint angles
    with a numerical IK library; handle the no-solution case.
  - **Why it matters:** Every Cartesian-goal motion is an IK call under
    the hood.
  - **Done when:** Round-trip (random reachable pose → IK → FK) error
    stays under 1 mm for 100 targets.

- [ ] **15. Trajectory smoothing and time parameterization**
  - **Goal:** Take a list of waypoints and produce a velocity /
    acceleration profile that respects joint limits, using iterative
    parabolic time parameterization.
  - **Why it matters:** Raw planner output is geometric — smoothing is
    what makes motion safe and executable.
  - **Done when:** The result respects joint velocity limits at every
    sample and is C1-continuous.

## Learning — RL, imitation, and LLMs in the loop

- [ ] **16. Behavior cloning from one teleop demo**
  - **Goal:** Record a 60-second teleop trajectory of a reach task,
    train a small MLP to map `(joint state → next action)`, replay it
    in sim.
  - **Why it matters:** Imitation learning is the cheapest way to get a
    policy when you cannot easily hand-code one.
  - **Done when:** The policy reaches within 3 cm of the target on 8/10
    fresh runs.

- [ ] **17. PPO reinforcement learning on a reach task**
  - **Goal:** Train a Stable-Baselines3 PPO agent. Observation = joint
    positions + target XYZ. Reward = -distance. Episode = 200 steps.
  - **Why it matters:** RL is the bridge between hand-coded motion and
    behavior that adapts to a moving target.
  - **Done when:** Average episode reward plateaus and success rate is
    above 80%.

- [ ] **18. Tiny VLA inspection (no execution)**
  - **Goal:** Feed a sim image plus an instruction ("pick the red cube")
    to a small VLA like OpenVLA, log the predicted 7-DoF action — do
    **not** execute it on the arm.
  - **Why it matters:** Understand the input/output shape of a VLA
    before trusting it with a motor command.
  - **Done when:** You can explain what each output channel means and
    how it maps to your arm's action space.

- [ ] **19. LLM-as-router with a human in the loop**
  - **Goal:** Detect objects with YOLO, hand the JSON to a small LLM
    along with a user instruction ("pick the green one"), have the LLM
    emit the chosen object ID, send that ID to MoveIt.
  - **Why it matters:** LLMs make natural-language instructions cheap;
    the engineering work is understanding where they fail.
  - **Done when:** 9/10 natural-language instructions on a 3-object
    scene pick the correct cube.

- [ ] **20. Domain-randomization A/B test**
  - **Goal:** Train two YOLO models on the same task — one with fixed
    lighting/textures, one with randomized lighting, table textures, and
    camera angle. Compare both on a held-out "weird lighting" set.
  - **Why it matters:** Domain randomization is the cheapest sim-to-real
    trick that actually works.
  - **Done when:** The randomized-trained model degrades less than the
    baseline on the weird-lighting set.

## How to use this list

- Treat each item as an **independent exercise**. Pick the skill you are
  weakest in next — not the next number on the list.
- Keep each one to **1–2 days**. If an item grows past that, split it.
- After finishing one, write a one-paragraph note: what worked, what
  didn't, what surprised you. That note is more valuable than the code.
- These exercises **do not add up to a finished cell**. For that, follow
  the full walkthrough in [`docs/README.md`](README.md).
