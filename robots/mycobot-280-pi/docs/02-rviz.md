# 02 — RViz: Seeing What The Robot Thinks

## What is RViz, in one sentence?

**RViz is a 3D viewer that shows you the world from the robot's own point of view** —
all the data the robot's brain is processing, drawn in 3D so you can see it.

## Gazebo vs. RViz — what's the difference?

This trips up a lot of beginners because both look like "a 3D window with a robot in
it". They're actually doing completely different jobs.

| Question                                         | Gazebo                            | RViz                                                      |
|--------------------------------------------------|-----------------------------------|-----------------------------------------------------------|
| What does it show?                               | The "real" simulated world        | What the robot's sensors and software perceive            |
| Does it simulate physics?                        | Yes (gravity, collisions, motors) | No (it just displays)                                     |
| Does it have a "ground truth"?                   | It IS the ground truth            | It only shows what's been published on ROS topics         |
| Can you click to move objects?                   | Yes (drag with mouse)             | No (it's a viewer, not a sandbox)                         |
| Where does the camera image come from?           | Rendered from the simulated scene | Whatever camera topic you subscribed to                   |
| Do you need it for the robot to work?            | Yes (it's the world)              | No (it's just for *you* to debug)                         |

**Analogy:** Gazebo is the real world (or the simulated stand-in for it). RViz is the
window into the robot's head — what it sees, what it's planning, what it thinks the
geometry around it looks like. The two can disagree, and when they do, that's often
where bugs hide.

## Why we keep them separate

You could imagine showing everything in one window. But:

- **Gazebo is heavy.** It's running physics every step. Adding a bunch of debug overlays
  would slow it down.
- **RViz is light and customizable.** You can toggle each layer (camera, point cloud,
  arm pose, planned trajectory, collision boxes) on and off without touching the world.
- **In real robotics, there is no Gazebo** — you only have RViz. So RViz is the tool
  you'll keep using even after you graduate to a real robot.

## What you can display in RViz (the layers)

Each display layer subscribes to a ROS topic and draws it. The common ones:

- **TF** — the chain of coordinate frames (where every link of the robot is, in space).
  Shows up as a tree of little RGB axis crosses.
- **RobotModel** — the actual 3D mesh of the arm, posed using the current `joint_states`
  topic. This is what the robot "is" right now.
- **PointCloud2** — the cloud of 3D dots from the depth camera. This is what
  perception is working with.
- **Image** — a 2D window showing the RGB camera feed.
- **MarkerArray / Trajectory** — visual overlays for things MoveIt computed
  (planned paths, collision objects, grasp candidates).
- **PlanningScene** — the world as MoveIt sees it: the arm, plus all the collision
  boxes the perception step found.

## The role of ros2_control (related, but not RViz)

While we're talking about "the gap between Gazebo and your code", it's worth introducing
a piece that quietly runs alongside Gazebo: **ros2_control**.

ros2_control is the "translation layer" between high-level motion commands and the
actual joints. When MoveIt says "move joint 1 to angle 1.57 over 0.5 seconds",
ros2_control is the thing that:

1. Receives that command on a ROS topic.
2. Tells Gazebo (or a real robot) to drive joint 1 toward that angle.
3. Reports back the actual current joint angles via `/joint_states`.

It comes bundled with two **controllers** that get loaded when Gazebo starts:

- **`arm_controller`** — handles the 6 arm joints, accepts trajectory commands
  (sequences of joint positions over time).
- **`gripper_action_controller`** — handles the gripper, accepts simple open/close
  commands.
- **`joint_state_broadcaster`** — publishes `/joint_states` so everyone knows the
  current pose.

You don't run ros2_control as a separate terminal — it's started by the Gazebo launch
file automatically. But it's important to know it exists, because when "the plan looks
correct in RViz but the arm doesn't move in Gazebo", the most likely culprit is a
controller name mismatch.

## Two ways to launch RViz

**Option A — bundled with the Gazebo launcher.** Drop the `use_rviz:=false` flag and
RViz opens automatically next to Gazebo. Good for casual use, but the RViz config
shipped with `mycobot_gazebo` is generic.

**Option B — standalone, with a custom config.** Run RViz from its own terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run rviz2 rviz2
```

Then add the displays you care about by clicking **Add → By topic**. This is what
you'll do once you want to see the camera feed alongside the planned trajectory or
the perception's point cloud.

## What RViz adds to your understanding

After Step 1 you had a Gazebo world. After Step 2 (adding RViz) you can:

- See the arm's joint pose in two places (Gazebo's "real" view, RViz's "current state"
  view) — they should match.
- See the camera image and point cloud directly, instead of trusting that they're
  flowing through ROS topics in the background.
- Once MoveIt is up, see the planned trajectory ghost-arm before it executes.

## What's still missing

You still can't make the arm move on purpose. Gazebo gives you the world, ros2_control
gives you the joint-control plumbing, but nobody's *deciding* where to move yet. That's
MoveIt's job.

→ Next: [03-moveit.md](03-moveit.md)
