# Feature 3 — Demonstration Trajectories

> **Poster wording.** "Full observation and action logs of a
> teleoperated expert doing the task. The training set for behaviour
> cloning, diffusion policy, and VLA models."

## What it is, in simple words

A **demonstration** is a recording of one full attempt at the task —
the gripper picks up the part, moves it across the cell, places it,
and lets go. We record, at every step (say, every 33 ms):

- **Observation** — what the robot would have *seen* and *felt* at
  that moment: camera frame(s), joint angles, gripper state, optional
  F/T reading.
- **Action** — what the robot *did* at that moment: target joint
  positions, target gripper open/close.

A **dataset** is a folder of hundreds of these recordings. Each one
is a successful run, ideally with a slightly different starting
condition (object in a different place, different colour, different
clutter around it).

```
demos_<project>/
├── episode_000/
│   ├── observations.parquet   (camera, joints, gripper, F/T per step)
│   └── actions.parquet        (target pose / joints per step)
├── episode_001/
└── …
```

## Who will use it

The customer's **policy-learning team** — the people training a model
that turns "what the robot sees" directly into "what the robot does
next." This is the **imitation learning** / **behaviour cloning** /
**VLA** crowd.

Job titles: *ML Research Engineer*, *Policy Learning Engineer*,
*Robot Learning Engineer*, *Applied Scientist (Imitation /
Reinforcement Learning)*.

## What models the customer trains with it

- **Behaviour Cloning (BC)** — the classical baseline; a small MLP or
  CNN copies the demos.
- **ACT** (Action Chunking with Transformers) — Stanford ALOHA-style.
- **Diffusion Policy** — strong generative policy from Columbia /
  Toyota Research Institute.
- **VQ-BeT** — quantised behaviour transformer.
- **OpenVLA, Octo, Pi-0** — Vision-Language-Action foundation
  models; the customer **fine-tunes** these on the synthetic demos.
- **DexMimicGen, MimicGen** — these can also *expand* a small set of
  human demos into a big one. We use them as part of the pipeline.

## Libraries and frameworks involved

**On our side:**

- **Gazebo** or **Isaac Sim** as the playback environment.
- **MoveIt 2** running a scripted expert that does the task
  successfully (the "teleoperator" the poster mentions can be either
  a human at a teleop rig in sim, or a scripted expert).
- **MimicGen / DexMimicGen** — to expand 10 seed demos into 1 000 by
  perturbing object positions.
- **LeRobot** — the dataset writer.

**On the customer's side:**

- **Hugging Face LeRobot** — the standard imitation-learning library.
- **Robomimic** — the Stanford alternative, also widely used.
- **PyTorch** — underlying framework.
- **Weights & Biases / TensorBoard** — to track the training run.

## What we ship (the formats)

| Format | When |
|--------|------|
| **LeRobot** (HF Datasets + MP4 videos) | Default. Works with ACT, Diffusion Policy, Pi-0 fine-tuning. |
| **Robomimic** (HDF5) | When the customer's training code already speaks Robomimic. |
| **RLDS** (TensorFlow Datasets) | When they use the Google / DeepMind stack (RT-X family, Octo). |
| **Raw rosbag / MCAP** | When they want to replay or filter the demos in ROS 2 first. |

The customer typically asks for **one** of LeRobot / Robomimic / RLDS.
We pick at the start of the project.

## How we generate it (the methods)

- **Scripted expert.** We write a small ROS 2 node that does the
  task perfectly using `MoveIt 2` + a scripted state machine. The
  simulator runs the node thousands of times with slightly different
  starting conditions, and we record every step.
- **Domain randomisation.** Each demo runs in a slightly randomised
  scene (different lighting, different texture, object shifted by a
  cm or two). The model trains on variation, not memorisation.
- **MimicGen-style perturbation.** Take ~10 seed demos, then for each
  one, sample many perturbed initial states and let the scripted
  expert re-do the task. Cheap way to scale to 1 000 demos.
- **Teleop in sim (optional).** When the task is hard to script (free
  motion, deformable objects), we record a human teleoperator using
  a SpaceMouse, a VR controller, or a leader-follower rig in sim.

## Pain points this solves

- **"Collecting real teleop demos is killing our team."** A real demo
  takes a human ~30 s + a few minutes of setup. A sim demo takes
  about 1 s of wall-clock time once the script is written.
- **"We need 1 000 demos but only have 10."** MimicGen expansion in
  sim is the cheapest way to get there.
- **"Our VLA fine-tune is starved for data."** OpenVLA / Pi-0 need
  hundreds to thousands of demos to fine-tune well. Sim is the only
  way to hit that count without a real teleop budget.

## What to say in a sales conversation

- "What policy architecture do you plan to train?" *ACT, Diffusion
  Policy, OpenVLA fine-tune? Picks the dataset format.*
- "Do you already have any teleop demos on real hardware?" *Even 10
  is enough to seed a MimicGen expansion. None is also fine — we use
  a scripted expert.*
- "What does the observation look like — RGB, RGB-D, multi-camera,
  joint state, F/T?" *Drives how many channels we record per step.*
- "How long is the task?" *We chunk by 1–3 s segments; very long
  tasks need hierarchical demos.*

## Typical scope and delivery

- **Inputs we need:** the URDF of the customer's arm (or one we
  build), the task description, the gripper, and any teleop demos
  they already have.
- **What we ship:** 500–5 000 demos in their chosen format, a
  `metadata.json` describing the action / observation spaces, and a
  short notebook showing the customer's policy training a baseline
  on the data.
- **Typical timeline:** 4–6 weeks (longest of the six features).
