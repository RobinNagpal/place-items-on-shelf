# 06-g — Datasets and Pretraining

You rarely train a robot policy from a blank weight matrix. You start
from a **pretrained foundation model** or a **dataset** somebody else
already collected, and fine-tune on your task.

This file is about where those checkpoints and datasets come from.

## Common use cases

- **Fine-tuning a pretrained policy** on 50–200 of your own demos.
- **Benchmarking** a new policy architecture against a fixed test set.
- **Pretraining a custom foundation model** for a specific embodiment
  (rare; expensive).
- **Synthetic data augmentation** when real demos are scarce.

## Frameworks / libraries / methods

### LeRobot (Hugging Face) — the on-ramp

The default starting point in 2025–2026. Three things in one:

1. A standard **dataset format** (HF Datasets + video) for
   teleoperation demos.
2. Pretrained **policies** you can fine-tune: ACT, Diffusion Policy,
   VQ-BeT, Pi-0 / Pi-0.5 checkpoints.
3. **Drivers and configs** for cheap arms (SO-100, Koch, Moss,
   ALOHA), so you can record demos and train end-to-end on hardware
   you can actually afford.

**Best for:** anyone starting in robot learning today without a
research budget.

### Large open datasets

| Dataset | Size | What it is |
|---------|------|-----------|
| **Open X-Embodiment (RT-X)** | 1M+ trajectories | Demos across 22 robot embodiments, contributed by 20+ labs. The largest open robot dataset. Used to pretrain RT-2-X, OpenVLA, Octo. |
| **DROID** | 76k+ demos | Standardised Franka rig. Higher per-demo quality than Open X. |
| **BridgeData V2** | 60k+ demos | Low-cost WidowX arms. Pre-VLA workhorse dataset. |
| **RoboMimic** | ~700 demos × multiple tasks | Smaller, curated benchmark. Great for ablations. |
| **ManiSkill / ManiSkill 2** | Sim-based | Procedural manipulation benchmarks. |
| **RoboHive, RoboNet** | Older benchmarks | Still cited for baselines. |
| **HuggingFace LeRobot Hub** | Growing | Community-uploaded SO-100 / ALOHA datasets. |

### Synthetic data generation

When real demos are scarce, you grow the dataset in sim:

- **DexMimicGen, MimicGen** — take 10 human demos, expand to 1000 via
  sim augmentation and per-step perturbation.
- **RoboCasa, Behaviour-1k** — procedurally generated household
  scenes.
- **NVIDIA Isaac Lab / Isaac Sim domain randomisation** — randomise
  textures, lighting, friction to create training variation.

### Pretrained checkpoints worth knowing

- **OpenVLA / OpenVLA-OFT** — 7B-parameter open VLA, trained on
  Open X.
- **Octo (small / base / xlarge)** — Berkeley's open VLA family.
- **LeRobot policy zoo** — ACT / Diffusion Policy / VQ-BeT
  checkpoints across many tasks.
- **Pi-0 / Pi-0.5** — commercial, available via Physical Intelligence
  partnerships.

## A pragmatic data plan

1. **Start from a pretrained policy** that already saw many robots
   (OpenVLA, Pi-0, ACT trained on Open X-Embodiment).
2. **Collect 50–200 of your own demos** on your robot with LeRobot
   or ALOHA-style teleop. See
   [03-imitation-learning.md](03-imitation-learning.md) for the
   teleop rigs.
3. **Fine-tune** for one or two days on a desktop GPU.
4. **Evaluate** on a held-out scene.
5. **If accuracy is short**, add 50 more demos targeting the failure
   cases. Repeat.

## How to pick a starting point

1. **Single arm, parallel jaw, common gripper?** → ACT or Diffusion
   Policy from the LeRobot zoo.
2. **Bimanual ALOHA-style?** → ACT on the Mobile ALOHA checkpoint.
3. **Want VLA generalisation?** → OpenVLA or Octo.
4. **Commercial production?** → Pi-0 or a Mech-Mind / Photoneo
   bundle.
5. **Demos are scarce, sim is good?** → MimicGen / DexMimicGen on top
   of 10 seed demos.

## Common mistakes

1. **Training from scratch.** Always start from a pretrained
   checkpoint. Random init wastes weeks.
2. **Mismatched embodiment.** Fine-tuning an Open-X-trained policy on
   your robot still requires *your* robot's data; you can't skip it.
3. **No held-out split.** "Eval on training scenes" gives meaningless
   numbers.
4. **Dataset rot.** Schemas, robot URDFs, gripper geometries change
   across HF uploads. Pin a version.
5. **Treating sim demos as real demos.** They aren't — they need
   domain randomisation or a real fine-tune on top.

## What's next

You have a model. Where does it physically run?

→ Next: [08-where-models-run.md](08-where-models-run.md)

← Back to: [Layer 3, AI overview](README.md)
