# Layer 3 — Software Stack

You finished Layer 2 with a list of hardware. Now you decide **what software
runs on top of it**.

A robot is not just metal. The arm cannot do anything until something tells
it where to go. That "something" is usually a stack of programs running on
your control hardware — an operating system, a middleware that lets
programs talk to each other, a motion planner that decides paths, perception
code that turns camera pixels into object positions, an AI model that
decides what to grab, and a small orchestrator that runs the whole sequence.

You can write all of this yourself. You almost never should. **Most of it
already exists** as open libraries (ROS 2, MoveIt, OpenCV, Gazebo) or as
vendor SDKs (UR RTDE, Franka FCI, FANUC PCDK). Your real job is to decide,
per layer, what to **inherit**, what to **buy**, and what little glue you
have to **write yourself**.

Skip any of these layers and the system breaks. So **Layer 3 is one file
per piece**, in the order you'd usually decide them.

## Read these in order

1. **[01-operating-system-and-runtime.md](01-operating-system-and-runtime.md)** —
   Ubuntu, real-time kernels, Windows, vendor RTOS. The base your other
   software sits on.
2. **[02-robotics-middleware.md](02-robotics-middleware.md)** — ROS 2,
   ROS 1, vendor middleware. How programs find each other and exchange
   messages. Pick this early; everything later assumes one.
3. **[03-vendor-sdks-and-drivers.md](03-vendor-sdks-and-drivers.md)** —
   How you actually talk to the arm. UR RTDE, Franka FCI, FANUC PCDK,
   ROS 2 hardware drivers.
4. **[04-motion-planning.md](04-motion-planning.md)** — MoveIt 2, OMPL,
   trajectory tracking, inverse kinematics. The brain that turns
   "go to pose X" into joint angles over time.
5. **[05-perception-software.md](05-perception-software.md)** — OpenCV,
   PCL, depth pipelines, pose estimation. Turning camera pixels into
   "there's a cylinder at (x, y, z)."
6. **[06-ai-and-foundation-models/](06-ai-and-foundation-models/README.md)** —
   The AI layer overview: when you actually need a foundation model,
   the scripted vs. imitation-learning vs. RL split, and the output
   AI-plan template. Detail lives in **eight sub-files in the
   folder**, one per technique, each listing use cases and
   frameworks:
   - **[01](06-ai-and-foundation-models/01-open-vocab-perception.md)** Open-vocab perception
     (CLIP, SAM, Grounding DINO, OWL-ViT).
   - **[02](06-ai-and-foundation-models/02-neural-grasp-generation.md)** Neural grasp
     generation (GraspNet, ContactGraspNet, AnyGrasp).
   - **[03](06-ai-and-foundation-models/03-imitation-learning.md)** Imitation learning
     (BC, ACT, Diffusion Policy) + teleop rigs (ALOHA, GELLO, SO-100).
   - **[04](06-ai-and-foundation-models/04-reinforcement-learning.md)** Reinforcement learning
     (PPO, SAC, Isaac Lab, MuJoCo MJX) + sim-to-real bridge.
   - **[05](06-ai-and-foundation-models/05-vision-language-action.md)** Vision-Language-Action
     models (RT-1/2, OpenVLA, Pi-0, GR00T, Octo).
   - **[06](06-ai-and-foundation-models/06-llms-in-the-loop.md)** LLMs in the loop
     (Code-as-Policies, SayCan, Function Calling).
   - **[07](06-ai-and-foundation-models/07-datasets-and-pretraining.md)** Datasets and
     pretraining (LeRobot, Open X-Embodiment, DROID, BridgeData V2).
   - **[08](06-ai-and-foundation-models/08-where-models-run.md)** Where the models run
     (Jetson Orin vs desktop GPU vs cloud, quantisation, edge/cloud
     split).
7. **[07-simulation.md](07-simulation.md)** — Gazebo, Isaac Sim, MuJoCo,
   PyBullet. Where you test before touching real hardware.
8. **[08-task-orchestration.md](08-task-orchestration.md)** — Behaviour
   trees, state machines, ROS 2 actions. How the high-level "pick the
   red cup" decomposes into a sequence of moves and reactions.
9. **[09-data-logging-and-observability.md](09-data-logging-and-observability.md)** —
   rosbag, MCAP, Foxglove, Grafana. Recording what happened so you can
   debug it later.
10. **[10-build-deploy-and-maintenance.md](10-build-deploy-and-maintenance.md)** —
    Containers, OTA updates, CI for robots. How the software gets onto
    the robot and stays current.

## What you leave this layer with

A **software bill of materials** — a list, paralleling Layer 2's hardware
list, of every piece of software the system runs. Each entry says:

- What it does.
- Where it came from (open library / vendor SDK / written in-house).
- What version is pinned.
- Who maintains it.

Together with the Layer-1 task spec and the Layer-2 hardware list, this
gives you the *complete* picture of the system: what it must do, what
metal does it, and what programs run on that metal.

You also have a clear **build-vs-buy table**. For each capability
(perception, planning, control, UI, logging), you've decided whether you
inherit it, buy it, or write it yourself — and you've written down *why*.

## Build vs. buy vs. inherit — a one-screen guide

Before you read any of the individual files, internalise this:

| If the capability is… | Do this | Why |
|------------------------|---------|-----|
| Standard and unchanging (motion planning, IK, transforms) | **Inherit** an open library (MoveIt, ROS 2 tf2). | Years of testing. Free. |
| Vendor-specific (arm driver, controller protocol) | **Inherit** the vendor SDK or its ROS 2 wrapper. | Nobody outside the vendor writes a better one. |
| Generic AI (object detection, segmentation) | **Inherit** a pretrained model. Fine-tune if needed. | Training from scratch is wasted effort. |
| Your specific task logic | **Write** it yourself. | Nobody else knows your problem. |
| Critical safety / certification | **Buy** a certified product. | DIY safety code is unacceptable for ISO 10218. |
| AI for novel manipulation | **Buy** a platform (Mech-Mind, Covariant, …) *or* take a foundation-model bet. | Both are real options; pick once and commit. |

Re-read this table after each file. The whole point of Layer 3 is to make
these decisions deliberately, not by accident.

## What this layer is not

- **Not a programming tutorial.** We name the libraries and what each is
  best for; we do not teach Python or C++.
- **Not exhaustive about every alternative.** We list the names you'll
  keep seeing in 2025–2026 robotics work. Bleeding-edge research tools
  belong in [`../02-hardware-selection/latest-robots.md`](../02-hardware-selection/latest-robots.md).
- **Not a substitute for the per-robot docs.** Once you've picked an arm,
  read the vendor docs and (if you're using the myCobot 280 Pi from this
  repo) the docs under
  [`../../robots/mycobot-280-pi/docs/`](../../robots/mycobot-280-pi/docs/).

## What's next

Layer 4 — [`../04-integration-and-bring-up/`](../04-integration-and-bring-up/) —
covers the **workflow** of going from "all the pieces work alone" to
"the cell runs unattended for a week and we trust it":
simulation-first development, the sim-to-real bridge, the
imitation-learning workflow with leader-follower demos, bring-up
checklist, pilot deployment, acceptance tests, safety validation,
operator runbooks, and Day-2 monitoring.
