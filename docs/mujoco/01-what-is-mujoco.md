# What is MuJoCo

A beginner's first read on MuJoCo. Plain English, no robotics
background assumed.

## What MuJoCo is, in one paragraph

MuJoCo is a **physics simulator**. It is a program that pretends to be
the real world inside a computer: gravity pulls things down, two
objects that touch push on each other, a robot arm with motors moves
the way real motors would. You give it a description of a robot and a
scene (the table, the cube, the gripper). You ask it "what happens if
the motor at the elbow turns 5 degrees?" and MuJoCo computes the
answer, many times per second. You can either watch it on screen, or
let a learning program (a neural network) practise inside it without
ever touching real hardware.

The name stands for **Mu**lti-**Jo**int dynamics with **Co**ntact. The
"with contact" part is the headline feature — MuJoCo is famously good
at simulating the moment things touch each other (a finger grabbing a
cup, a foot hitting the floor).

A few facts worth knowing up front:

- **Who made it.** Originally written by Emo Todorov (a researcher at
  the University of Washington). DeepMind bought it in 2021 and made it
  **free and open source in 2022**. Today Google DeepMind maintains it.
- **What it is not.** It is **not** a robot operating system. It is
  **not** a 3D model editor. It is **not** a renderer that produces
  movie-quality images. It is just the physics — the math of how
  things move and collide.
- **How you talk to it.** Python and C++. There are also JAX (GPU)
  and Unity bindings. No drag-and-drop GUI — you describe the scene
  in a file called **MJCF** (a flavour of XML) and load it.

## What MuJoCo is used for

Three big use cases. They overlap a lot.

### 1. Robot learning (the biggest one)

Reinforcement learning (RL) and imitation learning teach a robot a
task by **practising it thousands of times**. You cannot practise
thousands of times on a real arm — you would break it, run out of
batteries, or wait years. So you practise in a simulator. MuJoCo is
**the** simulator most research groups reach for here. Almost every
modern "robot brain" model — RT-X, OpenVLA, Octo, Diffusion Policy,
Physical Intelligence's Pi-Zero — ships with a MuJoCo test bench out
of the box.

If you ever read a robotics research paper from 2022 onwards and it
mentions "we trained in simulation", there is a 60–70% chance the
simulator is MuJoCo (or something built on it, like Robosuite or DM
Control).

### 2. Contact-rich manipulation

"Contact-rich" is a fancy way of saying "the hard parts of touching
stuff": grabbing a sponge, screwing a cap on a bottle, pulling a
zipper, holding an object stable while a second finger moves around
it. Most simulators get the bouncing-block case right but go a bit
wrong when many fingers all touch the same object at the same time.
MuJoCo's contact math (called a **convex optimisation solver**) was
designed exactly for that case. So if your project is **dexterous
hands**, **grasping**, **assembly**, or **in-hand manipulation**,
MuJoCo is usually the right choice.

### 3. Fast, parallel training on a GPU (MJX)

A newer piece called **MJX** ("MuJoCo XLA") is a GPU/TPU version of
MuJoCo, written using a library called JAX. It runs **thousands of
simulated robots at the same time** on a single graphics card. This
matters because RL needs *a lot* of practice — millions of trials. On
a regular CPU, that takes days. On a GPU using MJX, it takes minutes
or hours.

The popular library built on top of MJX is **MuJoCo Playground**,
which won a "best demo" award at the RSS 2025 robotics conference for
making this whole pipeline simple to use.

### Other (smaller) use cases

- **Controls research** — designing the math that decides motor
  commands (Model Predictive Control, whole-body control). MuJoCo is
  the unofficial standard here.
- **Humanoid robots** — most public sim-to-real humanoid demos (Unitree
  G1, Booster T1, Berkeley Humanoid) train in MuJoCo.
- **Biomechanics** — simulating muscles, tendons, joints in animals
  and humans. MuJoCo handles soft tendons better than most engines.

## What MuJoCo is **not** great at

Be honest about this. Two big gaps:

- **Photorealistic images.** MuJoCo can draw the scene, but it looks
  like a plain 3D viewer. If you want camera images that look real
  enough to train a vision model on, you use NVIDIA Isaac Sim instead
  (or Blender, or Unity).
- **ROS 2 plug-and-play.** ROS 2 is the most popular robotics
  middleware. Gazebo plugs into ROS 2 with one command. MuJoCo can be
  used with ROS 2 (via bridge packages like `mujoco_ros2`), but it
  takes more wiring.

## How MuJoCo differs from Gazebo and Isaac Sim

The three are all "robot simulators" but they were each built for a
different job. The simplest way to think about it:

| | **Gazebo** | **NVIDIA Isaac Sim** | **MuJoCo** |
|---|---|---|---|
| **Built for** | ROS 2 robot development | Photoreal images + GPU-scale RL | Physics accuracy + RL research |
| **Made by** | Open Robotics community | NVIDIA | Google DeepMind (open source) |
| **Cost** | Free | Free (open source from 2025) | Free |
| **ROS 2 integration** | Best in class (`ros_gz_bridge`) | Good (Isaac ROS packages) | Possible but DIY |
| **Image realism** | Basic | Photoreal (ray-traced RTX) | Basic |
| **Contact physics** | OK | Good (PhysX) | **Best for grasping / dexterity** |
| **GPU parallel training** | No | Yes (Isaac Lab) | Yes (MJX) |
| **Hardware needed** | Any laptop | NVIDIA RTX GPU recommended | Any laptop; GPU only for MJX |
| **Typical user** | Factory / warehouse / cobot teams | AI research labs, vision teams, humanoid teams | RL researchers, dexterous-hand teams, controls labs |
| **You'd pick it for** | "Plug my ROS 2 stack into a virtual cell" | "Train a vision model with realistic photos" or "train a humanoid with thousands of parallel envs" | "Train a hand to fold a towel" or "compare two controllers on hard contact" |

A useful way to remember it:

- **Gazebo = "the ROS 2 simulator."** Defaults to it when your robot
  already runs on ROS 2 and you want to test the same code as the real
  cell.
- **Isaac Sim = "the eyes and the GPU."** Best when you need either
  realistic camera images or massive parallel training.
- **MuJoCo = "the physics and the brains."** Best when the hard part
  is touching things accurately or teaching a policy to do so.

In real projects, teams **mix** them. A common 2026 recipe: train a
policy in Isaac Sim (because it's fast on GPU and looks real), then
re-check the best version of that policy in MuJoCo (because its
physics is more trustworthy), then deploy to the real robot.

## Why a beginner should learn it

Five honest reasons, in order of importance:

1. **It is the language of modern robot-learning research.** If you
   want to read recent papers, reproduce them, or work on anything
   AI-driven (vision-language-action models, humanoids, dexterous
   hands), you will hit MuJoCo within the first week. Not knowing it
   is like wanting to learn web development without knowing what HTML
   is.
2. **Low setup cost.** MuJoCo runs on any laptop — Windows, Mac,
   Linux. Install with `pip install mujoco` and you have a working
   physics engine in two minutes. Compare with Isaac Sim, which needs
   an NVIDIA RTX GPU and a multi-gigabyte install.
3. **You learn the right mental model.** MuJoCo forces you to think
   about robots as **joints, bodies, contacts, actuators** — the same
   words you'll see in URDF, MJCF, ROS, MoveIt, and every controls
   textbook. That vocabulary transfers to every other simulator.
4. **It teaches you the hard part of robotics.** Most beginners can
   get a robot to move in a straight line. The hard part is making it
   *touch the world* without breaking, slipping, or losing the
   object. MuJoCo's contact model is exactly where that skill lives.
5. **Hiring and jobs.** "MuJoCo" appears in 100+ active robotics job
   listings (Indeed, 2026). DeepMind itself hires dedicated MuJoCo
   engineers. It is a real, marketable skill — not just an academic
   toy.

## What MuJoCo will *not* teach you on its own

Important to flag, so you don't pick the wrong tool first:

- It won't teach you ROS 2 in depth — start with Gazebo for that.
- It won't teach you photorealistic vision pipelines — start with
  Isaac Sim or Blender.
- It won't teach you factory cell programming (UR/FANUC/ABB) — start
  with the vendor's own simulator.

For this project (place-items-on-shelf, myCobot 280), the natural
order is Gazebo first (it's what the repo already uses), then MuJoCo
once you want to start training policies or doing serious dexterous
manipulation work.

## What to read or try next

A short, opinionated list:

- **Official docs:** <https://mujoco.readthedocs.io/> — start at
  "Overview" and "Tutorial".
- **MuJoCo Menagerie:** <https://github.com/google-deepmind/mujoco_menagerie>
  — ready-made high-quality MJCF models for popular robots (Franka,
  Universal Robots, Unitree quadrupeds, dexterous hands). Clone it,
  load a model, look around. No coding required.
- **MuJoCo Playground:** <https://playground.mujoco.org/> — the GPU
  RL framework. Try the "train a quadruped to walk in 5 minutes"
  example.
- **Compare with Gazebo:** see this repo's existing simulation
  overview at
  [`../generic-workflow/03-software-stack/07-simulation.md`](../generic-workflow/03-software-stack/07-simulation.md)
  and Isaac Sim setup notes at
  [`../../isaac-sim-aws-setup.md`](../../isaac-sim-aws-setup.md).

## One-line summary

MuJoCo is the **free, accurate, beginner-installable physics engine**
that the AI-side of robotics has standardised on — pick it up after
Gazebo if you want to do anything involving learning, dexterous
manipulation, or modern humanoids.
