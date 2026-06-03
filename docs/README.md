# Learning Robotic Arms — Step By Step

A walkthrough of how to think about a robotic-arm project from scratch.
Written for people who are new to robotics and want to learn the field one
step at a time. Plain English. No code in these docs.

We focus on **robotic arms** (also called manipulators). Mobile robots and
drones are not in scope. Humanoids appear briefly in the reference snapshot
at the end, because the line between "arm" and "humanoid arm" is blurring
fast.

## How this is organised

Two layers so far, each in its own subfolder:

- **[`01-finalize-requirements/`](01-finalize-requirements/)** — Figure
  out what the robot has to do. Just thinking and writing — no shopping,
  no code.
- **[`02-hardware-selection/`](02-hardware-selection/)** — Pick all the
  hardware. One file per piece (arm, gripper, sensors, mount, power,
  control hardware, network, cables, safety, operator interface). Each
  file lists the common / popular options and what each is best for.

Read the subfolder READMEs for the order inside each layer.

A later layer (to be written) will cover the **software side** — what
software you run on top of the hardware list you finish with.

## Reference (not a numbered layer)

- **[latest-robots.md](latest-robots.md)** — A dated snapshot of newer
  hardware. Humanoids actually shipping (Figure, Tesla Optimus, 1X NEO,
  Apptronik Apollo, Unitree G1, Agility Digit), "AI-included"
  manipulation platforms (Physical Intelligence, Covariant, Dexterity,
  Mech-Mind), and the foundation-model "robot brains" that are starting
  to drive hardware choices. Useful when the established hardware in
  Layer 2 can't do your task and you need to look at the bleeding edge.

## How each doc is written

Every doc in the series follows roughly this shape:

1. **What this is** — in one paragraph.
2. **Why it matters** — in plain English.
3. **The main options** — the categories or types you'll choose between.
4. **The popular / common options on the market** — names you'll keep
   seeing, with a short note on what each is best for.
5. **What to check before deciding** — a checklist.
6. **Output** — what to write down before moving on.
7. **Common mistakes** — what beginners get wrong.
8. **What's next** — the next file in the reading order.

## What this series is not

- **Not a tutorial for one specific robot.** The myCobot-280-Pi-specific
  recipes live under [`../robots/mycobot-280-pi/docs/`](../robots/mycobot-280-pi/docs/).
- **Not a code reference.** We stay at the concept and workflow level.
- **Not exhaustive.** We aim for the *most useful 80%* of each topic.

If you want depth on a specific topic after reading the relevant layer
here, follow the links to the robot-specific docs or to external
resources at the end of each chapter.
