# Learning Robotic Arms — Step By Step

A beginner-friendly walkthrough of how to think about a robotic-arm problem
*from scratch*. Written for people who are new to robotics and want to learn
the field one layer at a time, in plain English, without diving into code.

We focus on **robotic arms** (sometimes called manipulators). Mobile robots
and drones are out of scope; humanoids are off the main reading path but
covered briefly in the reference section below because the line between
"arm" and "humanoid arm" is genuinely blurring in 2026.

The series is built so each doc adds one layer on top of the previous ones.
Read them in order.

## Pattern of each doc

Every doc in this series follows the same shape:

1. **Why this layer matters** — the role this layer plays in the whole stack.
2. **The key questions / steps** — what you actually do at this layer.
3. **A checklist** — copy-paste it for any new problem.
4. **Common mistakes** — what beginners get wrong.
5. **Libraries / frameworks** — what tools exist for this layer, if any.
6. **What's next** — the layer that builds on top of this one.

## Reading order

1. **[01-understanding-the-problem.md](01-understanding-the-problem.md)** —
   The first step for any robotic-arm task: defining the problem before you
   touch any hardware or library. The 7 questions to ask, the checklist to
   fill in, and what to hand off to the next layer.
2. **[02-choosing-arm-and-gripper.md](02-choosing-arm-and-gripper.md)** —
   Turning the Layer-1 spec into a hardware shortlist. Criteria for picking
   an arm (DOF, payload, reach, repeatability, safety, SDK, AI-included), a
   market map of the common / popular arms (hobby, mid-range cobot,
   industrial) and grippers (parallel, vacuum, soft, etc.), and why the
   software/AI question must be considered *in parallel* with the hardware
   choice rather than after it.
3. **[03-sensors.md](03-sensors.md)** — The rest of the hardware side:
   sensors. Which sensor families matter for arm-mounted use (2D RGB, RGBD
   depth cameras, force/torque, tactile, proximity, safety scanners),
   where they mount (eye-in-hand vs eye-to-hand vs gripper-integrated),
   the common / popular names in each family (Intel RealSense, Orbbec,
   Photoneo, Zivid, ATI, Robotiq FT, SICK, ...), and the practical
   considerations (payload weight, FOV, working range, ROS 2 driver
   availability) that turn "looks good" into "actually mountable".

*(More layers will be added one at a time. This series is intentionally being
written slowly — each layer thoroughly before the next. Layer 04 will cover
the software / AI stack that pairs with the finished hardware spec.)*

## Reference docs (not numbered layers)

These sit alongside the layered series and are meant to be skimmed on demand
rather than read in order:

- **[latest-robots.md](latest-robots.md)** — A dated snapshot of newer robot
  hardware: humanoids actually shipping or in production pilots, "AI-included"
  manipulation platforms, and the foundation-model "robot brains" that are
  starting to drive hardware choices. Intentionally broader than "just arms"
  because in 2026 that line is genuinely blurring. Has an explicit freshness
  warning at the top — re-check before relying on it.

## What this series is **not**

- It is not a tutorial for one specific robot. The mycobot-280-pi specific
  recipes live under
  [`../robots/mycobot-280-pi/docs/`](../robots/mycobot-280-pi/docs/) and assume
  you already know roughly what you're doing.
- It is not a code reference. We stay at the concept and workflow level.
- It is not exhaustive — we aim for the **most useful 80%** of each topic,
  not every academic detail.

If you want depth on a specific topic after reading the relevant layer here,
follow the links to the robot-specific docs or to external resources at the
end of each chapter.
