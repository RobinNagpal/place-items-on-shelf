# 06-b — Neural Grasp Generation

Models that predict **where the gripper should go** to pick up an
object. Input: a point cloud (and sometimes RGB), a target region, and
a gripper model. Output: one or more 6-DOF grasp poses with
confidence scores.

The detection from [step 1](01-open-vocab-perception.md) tells you
*what* and *where*; grasp generation tells you *how to grab it*.

## Common use cases

- **Bin picking** — random pile of objects, find a stable grasp on
  the topmost one.
- **Novel-object pick-and-place** — the gripper has never seen this
  shape before.
- **AI-included industrial scanners** — Mech-Mind, Photoneo, and
  Zivid bundle scanner + grasp software for production.
- **Grasp scoring for a candidate set** — you have several heuristic
  grasps and want the model to rank them.

## Frameworks / libraries / methods

### GraspNet-1Billion

Large dataset + baseline model trained on a billion grasp annotations
in cluttered scenes.

- **Best for:** parallel-jaw grippers, dense clutter.
- **Use it via:** the official `graspnet-baseline` PyTorch repo.

### ContactGraspNet

Predicts contact points instead of full poses; lower-dimensional
output, often more robust on point clouds with holes.

- **Best for:** noisy depth data, partial occlusion.
- **Use it via:** the NVIDIA `contact_graspnet` repo.

### AnyGrasp / GSNet

Newer single-shot grasp predictor; faster than GraspNet, handles
clutter and articulated objects.

### Dex-Net (2 / 3 / 4)

Older but still cited. Trained on synthetic point clouds with both
parallel-jaw and suction quality metrics.

- **Best for:** baselines and ablations; one of the few open models
  with a serious **suction**-gripper variant (Dex-Net 3).

### Vendor bin-picking software

For production cells with budget, the integrated scanner+software
bundles outperform open models on reliability:

- **Mech-Mind Mech-Vision** — paired with their structured-light
  scanners.
- **Photoneo Bin Picking Studio** — paired with PhoXi scanners.
- **Zivid Vision Engine** — integrates with multiple grasp planners.
- **Pickit3D** — turnkey bin-picking solution.

## How to pick

1. **Research, parallel-jaw, single object?** → ContactGraspNet.
2. **Cluttered pile, parallel-jaw?** → GraspNet-1Billion or AnyGrasp.
3. **Vacuum gripper?** → Dex-Net 3 or vendor.
4. **Production, downtime is expensive?** → Mech-Mind / Photoneo
   bundle.
5. **One known object, top-down grip is fine?** → Skip neural grasp.
   A hand-tuned heuristic on the segmented centroid is enough.

## Where it runs

- **ContactGraspNet, GraspNet baseline** — Jetson Orin AGX at 1–3 Hz,
  desktop GPU at 10+ Hz.
- **AnyGrasp** — desktop GPU recommended.
- **Vendor stacks** — runs on the vendor's own IPC, often a Windows
  box that came with the scanner.

## Common mistakes

1. **Using neural grasp on a fixed object.** Hand-tune the grip pose;
   it's faster and more reliable.
2. **Ignoring gripper geometry.** GraspNet's grasps assume a generic
   parallel jaw. Re-check that the grip fits *your* gripper's width
   and finger length.
3. **No fallback when no grasp is found.** Always have a "try
   different angle" or "ask for help" branch.
4. **Trusting the confidence score blindly.** Score thresholds need
   tuning per scene and per gripper.

## What's next

If demonstrations are available, imitation learning often outperforms
hand-tuned grasp generation for a specific task.

→ Next: [03-imitation-learning.md](03-imitation-learning.md)

← Back to: [Layer 3, AI overview](README.md)
