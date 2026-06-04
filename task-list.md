# Task List

Short-term plan for working through the
[learning checklist](docs/learning-checklist.md). Each numbered item
below maps directly to the same item number in that file.

## Thursday — 2026-06-04

### Already done

- Simulation setup & understanding — items **1** and **2**.
- Motion via MoveIt — items **18**, **19**, **20**, **21**, **22**.

### To do today — start perception

- [x] **3.** Train a tiny YOLO on a custom 5-class dataset.
- [x] **4.** Run YOLO live on a Gazebo camera feed.
- [x] **5.** Score detections automatically against Gazebo ground truth.
- [ ] **6.** Tiny classifier quantized for an edge CPU.

## Friday — 2026-06-05

### Finish perception

- [x] **7.** Instance segmentation — pixel masks instead of bounding boxes.
- [x] **8.** Depth-camera point cloud → object centroid.
- [ ] **9.** Depth-based grasp-point estimation.
- [ ] **10.** ArUco marker 6-DoF pose estimation.
- [ ] **11.** Camera intrinsics calibration.
- [ ] **12.** Hand-eye calibration (camera ↔ end-effector).
- [ ] **13.** Classical colour segmentation (no ML).
- [ ] **14.** Barcode / QR-code reader on simulated labels.

### Other sensors beyond the camera

- [ ] **15.** Wrist force/torque (F/T) sensor — detect surface contact.
- [ ] **16.** Joint effort/current logging during a motion.
- [ ] **17.** Gripper contact sensor — confirm grasp succeeded.

## Monday — 2026-06-08

### Learning — RL, imitation, and LLMs (sim-only)

Not sure how far we can get on these — some may need extra setup or
hardware-adjacent work. Revisit scope on the day.

- [ ] **23.** Behavior cloning from one teleop demo.
- [ ] **24.** PPO reinforcement learning on a reach task.
- [ ] **25.** Tiny VLA inspection (no execution).
- [ ] **26.** LLM-as-router with a human in the loop.

## After the checklist — dodao.io website update

Once the checklist work is in a good shape, update
[https://dodao.io/](https://dodao.io/) to position the company as a
**robotics services** company first.

- Keep the current design — it is fine as-is.
- Rework the **"Our Services"** section. Today it looks plain and a bit
  odd. It should make clear that **robotics services are the primary
  offering**; the other services stay listed but are secondary.
- Add a **Robotics** section with sub-pages, one per layer of the stack.
  Each sub-page lists the frameworks and libraries we work with at that
  layer (e.g. simulation, perception, motion planning, learning).
- Goal: build credibility as a robotics company. We do not yet have a
  working public simulation to show, so the sub-pages and the stack
  breakdown are how we demonstrate depth in the meantime.
