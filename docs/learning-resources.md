# Learning Resources — Courses And Open-Source Projects

Outside material that teaches the skills this repo assumes: ROS 2, robotic
arms, MoveIt 2, Gazebo, and vision-language-action (VLA) models.

Use it like this: the [`docs/`](README.md) walkthrough tells you *what to
decide*, the [exercises](../exercises/) make you *build* it, and the items
below teach you *the tool* when a step is unclear.

> **Snapshot date: September 2026.** Ratings, review counts, and star
> counts move. Treat the numbers as "roughly this popular", not as
> today's exact figure. Prices and coupon codes are not listed here
> because they expire.

## Courses we are following

These two are the ones we picked up first.

### 1. ROS 2 Robotic Arm Mastery: MoveIt2, Gazebo & VLA Models

- **Link:** <https://www.udemy.com/course/ros-2-robotic-arm-mastery-moveit2-gazebo-vla-models/>
- **Instructor:** Ferbin Richard
- **Published:** August 2026
- **Rating:** too new to have one. Nobody has reviewed it in volume yet.

Why we picked it: it is the only course we found that puts **MoveIt 2,
Gazebo, and VLA models in one syllabus**. Everything else teaches motion
planning or robot learning, not both. That combination is exactly the
span of this repo — classical planning in
[`04-motion-planning`](generic-workflow/03-software-stack/04-motion-planning.md)
plus the model stack in
[`06-ai-and-foundation-models`](generic-workflow/03-software-stack/06-ai-and-foundation-models/).

Caveat: a brand-new course with no review history is a bet. If you want a
proven course for the MoveIt 2 half, use item 2 or 3 in the next section
and take this one only for the VLA chapters.

### 2. ROS2 Ultimate Guide for Custom Robotic Arms and Panda 7 DOF

- **Link:** <https://www.udemy.com/course/robotics-with-ros-build-robotic-arm-in-gazebo-and-moveit/>
- **Instructor:** Muhammad Luqman
- **Rating:** 4.1 / 5 from 326 ratings, ~1,690 students
- **Length:** 6 h 41 m
- **Code:** <https://github.com/noshluk2/ROS2-Ultimate-guide-for-Custom-Robotic-Arms-and-Panda-7-DOF>

Note the title changed. The URL still says
`robotics-with-ros-build-robotic-arm-in-gazebo-and-moveit`, but the course
is now listed as *ROS2 Ultimate guide for Custom Robotic Arms and Panda 7
DOF*. Same course.

Why we picked it: it builds a custom arm ("BAZU") from a URDF up — links
and joints, then `ros2_control` position / effort / joint-trajectory
controllers, then a DH table for forward and inverse kinematics using
Peter Corke's Robotics Toolbox — before switching to the Franka Emika
Panda 7-DOF. That is the same path as
[exercise 02](../exercises/02-read-and-annotate-urdf/), so it is a good
second opinion on our own URDF work.

Caveat: 4.1 / 5 is good, not great. Reviews complain about pace and
Ubuntu-version drift. Check which distro the current recording targets
before you follow along.

## 15 more, best first

Seven courses, then eight open-source projects.

### Courses

#### 1. Modern Robotics — free video lectures (Northwestern)

- **Videos:** <https://modernrobotics.northwestern.edu/nu-gm-book-resource/introduction-autoplay/>
- **Authors:** Kevin M. Lynch and Frank C. Park, Northwestern University
- **Cost:** free. The videos are a public YouTube playlist
- **Also free:** the [code library](https://github.com/NxRLab/ModernRobotics)
  (~2.9k stars) in Python, MATLAB, and Mathematica
- **Structured version:** the [Coursera specialization](https://www.coursera.org/specializations/modernrobotics),
  ~4.7–4.9 / 5 across its six courses, thousands of reviews, free to audit

**Start here.** This is the single best item on the page and the only one
that is both free and university-grade.

Thirteen chapters of short videos, following the Lynch and Park textbook:
configuration space, rigid-body motions, forward kinematics, velocity
kinematics and statics, inverse kinematics, closed chains, dynamics of
open chains, trajectory generation, motion planning, robot control,
grasping and manipulation, and wheeled mobile robots.

Every other course on this page teaches you to *drive* a tool. This one
teaches you what the tool is doing. When MoveIt returns a plan you did
not expect, or an IK call fails with no obvious reason, the answer is
almost always in one of these chapters — chapter 6 for IK, chapter 5 for
Jacobians and singularities, chapter 9 for trajectory generation.

Practical note: watch it *alongside* the ROS 2 courses, not before them.
The chapters are short and self-contained, so pull up the one that
matches whatever is confusing you that week. Chapters 2–6 and 9 cover
almost everything a fixed arm needs; 12 and 13 are out of scope here.

#### The rest

| # | Resource | Rating | Covers | Cost |
|---|---|---|---|---|
| 2 | [Robotics and ROS 2 — Learn by Doing! Manipulators](https://www.udemy.com/course/robotics-and-ros-2-learn-by-doing-manipulators/) (Antonio Brandi) | 4.5 / 5, 812 ratings, ~7,500 students, 21 h | URDF, Gazebo, `ros2_control`, kinematics, MoveIt 2, then the same code on a 3D-printed Arduino arm | Paid |
| 3 | [ROS 2 MoveIt 2 — Control a Robotic Arm](https://www.udemy.com/course/ros2-moveit2/) (Edouard Renard) | Consistently strong reviews; the most-recommended MoveIt 2 course | Configuring a 6-axis arm for MoveIt 2 from scratch, gripper, Setup Assistant, MoveIt–ROS 2 bridge | Paid |
| 4 | [ROS 2 for Beginners Level 2 — TF, URDF, RViz, Gazebo](https://www.udemy.com/course/ros2-tf-urdf-rviz-gazebo/) (Edouard Renard) | 4.7 / 5, 1,218 ratings | TF trees, writing URDF/xacro by hand, RViz, Gazebo worlds. The prerequisite for the two above | Paid |
| 5 | [The Construct — ROS 2 Manipulation Basics](https://www.theconstruct.ai/robotigniteacademy_learnros/ros-courses-library/ros2-manipulation-basics/) and [Manipulation & Perception](https://www.theconstruct.ai/robotigniteacademy_learnros/ros-courses-library/ros2-manipulation-perception-online-course/) | Long-running, widely used in industry training | MoveIt 2 packages, Python and C++ planning, then perception-driven pick-and-place on a UR3e + gripper + 3D sensor | Subscription; runs in the browser, no local install |
| 6 | [MoveIt 2 official tutorials](https://moveit.picknik.ai/) ([repo](https://github.com/moveit/moveit2_tutorials), ~370 stars) | Reference-grade | Every MoveIt 2 concept with runnable code: `MoveGroupInterface`, planning scene, Servo, Task Constructor, Setup Assistant | Free |
| 7 | [Automatic Addison — ROS 2 arm series](https://automaticaddison.com/how-to-control-a-robotic-arm-using-ros-2-control-and-gazebo/) | Widely linked in the ROS 2 community | Written, copy-pasteable walkthroughs: [`ros2_control` + Gazebo](https://automaticaddison.com/how-to-control-a-robotic-arm-using-ros-2-control-and-gazebo/), then [MoveIt 2 config for a simulated arm](https://automaticaddison.com/configure-moveit-2-for-a-simulated-robot-arm-ros-2-jazzy/) | Free |

### Open-source projects

| # | Repo | Stars | Why read it |
|---|---|---|---|
| 8 | [moveit/moveit2](https://github.com/moveit/moveit2) | ~2.0k | The planner itself. Read `moveit_ros/planning_interface` when you need to know what `MoveGroupInterface` actually does. Supports Humble, Jazzy, Rolling |
| 9 | [moveit/moveit_task_constructor](https://github.com/moveit/moveit_task_constructor) | ~284 | The replacement for MoveIt's old pick-and-place pipeline. Splits a task into planning stages you can inspect one by one — the right tool once a hard-coded sequence stops scaling |
| 10 | [ros-controls/ros2_control_demos](https://github.com/ros-controls/ros2_control_demos) | ~844 | 17 self-contained examples of `ros2_control`. Example 7 is a 6-DOF arm; example 9 is Gazebo integration. The fastest way to understand hardware interfaces and controller chaining |
| 11 | [IFRA-Cranfield/ros2_RobotSimulation](https://github.com/IFRA-Cranfield/ros2_RobotSimulation) | ~323 | Ready-to-run Gazebo + MoveIt 2 packages for Panda, UR3/5/10, ABB IRB-120/1200/6640, Fanuc CR35-iA, and KUKA LBR-IIWA. Good reference for how a complete arm package is laid out |
| 12 | [UniversalRobots/Universal_Robots_ROS2_Driver](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver) | ~820 | A production vendor driver. Shows what a real `ros2_control` hardware interface, a calibration tool, and a shipped `ur_moveit_config` look like — the sim-to-real gap made concrete |
| 13 | [huggingface/lerobot](https://github.com/huggingface/lerobot) | ~27k | The most active open robot-learning library. Imitation learning (ACT, Diffusion Policy, VQ-BeT), RL (HIL-SERL, TD-MPC), and VLAs (π0, SmolVLA, GR00T) behind one interface, plus a standard dataset format. Start here for [exercise 23](../exercises/23-behavior-cloning-reach/) |
| 14 | [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | ~13.6k | Open weights and code for π0, π0-FAST, and π0.5 — currently the strongest openly available VLAs. JAX and PyTorch. Fine-tune by converting your data to LeRobot format |
| 15 | [openvla/openvla](https://github.com/openvla/openvla) | ~7.0k | The 7B VLA trained on ~970k Open X-Embodiment trajectories. The clearest codebase for *how a VLA is actually built*: a vision encoder (DINOv2 + SigLIP) bolted to an LLM, actions as tokens. LoRA and full fine-tuning included |

## Also relevant, outside the 15

Narrower, but directly useful for this repo:

- [elephantrobotics/mycobot_ros2](https://github.com/elephantrobotics/mycobot_ros2) (~129 stars) —
  the vendor ROS 2 packages for our arm, the
  [myCobot 280 Pi](../robots/mycobot-280-pi/docs/README.md).
- [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) (~8.0k) —
  GPU-parallel RL and imitation learning, 30+ ready environments. Relevant
  once Gazebo is too slow to train in.
- [google-deepmind/mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie) (~3.9k) —
  tuned MuJoCo models for Panda, UR5e/UR10e, iiwa 14, Kinova Gen3, xArm7
  and ~15 more arms. Saves days of contact-parameter guesswork.
- [petercorke/robotics-toolbox-python](https://github.com/petercorke/robotics-toolbox-python) (~3.5k) —
  forward kinematics, Jacobians, and numerical IK in microseconds, over 50
  robot models. The tool the Panda course above uses for its DH work.
- [NVlabs/contact_graspnet](https://github.com/NVlabs/contact_graspnet) (~527) —
  6-DoF grasp poses straight from a point cloud. The learned alternative
  to a hand-written grasp heuristic.

## How to sequence these

If you are starting from zero:

1. **ROS 2 basics and URDF** — course 4, or the free tutorials in item 7.
2. **Motion planning** — course 3, then the official tutorials (item 6)
   as the reference you keep open.
3. **A full arm project** — course 2, or our
   [exercises 18–22](../exercises/).
4. **Learned policies and VLAs** — LeRobot (item 13) first, because it
   runs on a laptop, then openpi (14) and OpenVLA (15).

Run **item 1, Modern Robotics, across all four steps** rather than as a
step of its own. It is the theory the others assume.

Courses 2–5 overlap heavily. Pick one, not all four.

## Adding to this list

Keep the bar high. An entry earns its place only if it has **either** a
real rating with enough reviews to mean something (roughly 4.3+ / 5 over
200+ ratings), **or** clear community adoption (stars, active commits,
people citing it). Always record what could not be verified — a missing
rating is a fact, not a gap to fill with a guess.
