# 03 — MoveIt: The Motion-Planning Brain

## What is MoveIt, in one sentence?

**MoveIt is the software that figures out how to move the arm from where it is now to
where you want it to be — smoothly, safely, and without bumping into anything.**

It is not a controller (that's ros2_control). It is not a perception system (that's a
separate program we'll meet in the next doc). MoveIt sits in the middle: you give it a
*goal*, it gives you a *trajectory* (a timed sequence of joint angles) that gets the arm
from start to goal.

## Why planning is hard

It sounds simple — "just move the hand here". But:

- The arm has 6 joints. Each joint angle is one dimension, so the space of all possible
  arm poses is 6-dimensional. You can't just visualize it.
- There are usually many joint combinations that put the hand in the same place
  (the famous "elbow up vs. elbow down" trade-off). MoveIt has to pick one.
- Some paths between two poses pass through self-collisions (arm hits itself), or
  through obstacles (arm hits the table, the cylinder, the cardboard box).
- Some paths are *physically possible* but would require the joints to spin
  unreasonably fast or violate torque limits.

MoveIt uses a family of algorithms called **motion planners** to search this 6-D space
for a valid path. The most common one for us is **OMPL** (Open Motion Planning Library),
and specifically a planner called **RRTConnect** — a randomized algorithm that tries
many possible paths and returns the first valid one it finds.

## The three things MoveIt needs

1. **A model of the robot** — what links are connected by what joints, joint limits,
   collision shapes, kinematics (forward and inverse). This comes from the URDF/SRDF
   files in `mycobot_description` and `mycobot_moveit_config`.
2. **A model of the world** — also called the **planning scene**. Everything that's
   *not* the robot but that the arm might collide with: the table, the objects on the
   table, the camera tripod. We get this from the perception step (next doc).
3. **A goal** — usually "place the gripper at this pose" or "move every joint to these
   specific angles". You pass this in via code or a service call.

## What `move_group` actually is

**`move_group` is the central MoveIt program.** It's the one you run in Terminal 2 of
the 4-terminal sequence. When it starts:

- It loads the robot model.
- It loads the planning configuration (which planners are available, what their default
  parameters are).
- It hooks into `ros2_control` so it knows which controllers to send trajectories to.
- It advertises a set of **services** and **actions** that other programs can call.

The most important things it advertises:

- **`/get_planning_scene` (service)** — "give me the current world state". The
  perception program also advertises a service with the *exact same name* but a
  different namespace, which is why the previous troubleshooting got confusing.
- **`/move_action` (action)** — "plan a motion to this goal and execute it". The simple
  one-shot interface.
- **`/execute_trajectory` (action)** — "I already have a trajectory; please run it".
  Used by more advanced clients that plan elsewhere and only ask move_group for execution.

## Two ways to talk to MoveIt

**Way 1 — `MoveGroupInterface`.** A simple C++ (or Python) client library. You construct
an interface object, call `setNamedTarget("ready")` or `setJointValueTarget({0.5, ...})`,
call `plan()`, then `execute()`. This is what our custom `cobot280_moveit_task` package
uses — it's the "hello world" path.

**Way 2 — `MoveIt Task Constructor` (MTC).** A higher-level library for stitching
together many planning stages into one big task graph: "approach the object", "close
the gripper", "lift", "transport", "lower", "open gripper", "retreat". Each stage is
its own planning problem, and MTC handles the dependencies between them. This is what
the pick-and-place demo uses, and what the next doc covers.

The difference matters because: with `MoveGroupInterface`, *you* write the sequence in
code. With MTC, you describe the *task structure* and let it figure out the sequence,
including backtracking if one stage fails to find a plan.

## The planning scene in detail

This is the concept that took the longest to wire up correctly, so it gets its own
section.

The **planning scene** is the world model that MoveIt uses for collision checking. It
includes:

- The robot itself (with its current joint configuration).
- Any **collision objects** that have been added — things the arm should avoid hitting.
- Any **attached objects** — things currently held by the gripper (treated as part of
  the arm for collision purposes).

You can populate the planning scene in two ways:

- **By hand in code** — call `scene.addCollisionObjects([...])` with a list of boxes
  and cylinders at known positions. Simple but you have to know exactly where everything
  is. This is fine for a fixed scene like a static obstacle course.
- **From perception** — let a camera detect the objects and publish them as collision
  objects automatically. More flexible because the robot can react to a scene it didn't
  know about beforehand. This is what the pick-and-place demo does.

When `move_group` starts up, the planning scene is essentially empty (just the robot).
The perception node then adds the table and the YCB objects on top.

## The terminal command (Step 3)

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_moveit_config move_group.launch.py use_rviz:=false
```

`use_rviz:=false` because we don't want a second RViz window.

## What success looks like

The terminal scrolls through a long startup log loading planners, plugins, and
controllers. The crucial last line is:

```
[move_group]: You can start planning now!
```

You should also see, in the list of "MoveGroup using:" capabilities printed shortly
before that:

- `move_action`
- `execute_trajectory_action`
- `get_planning_scene_service`
- `apply_planning_scene_service`
- ... and most importantly for MTC, `ExecuteTaskSolutionCapability` (only present if
  you `apt install`ed `ros-jazzy-moveit-task-constructor-capabilities`).

## What's still missing

`move_group` is now alive and waiting. It can plan motions, but only against an empty
world — it has no idea there's a table or a cylinder in front of it. And nobody is
asking it to plan anything yet. The pick-and-place task adds both pieces.

→ Next: [04-pick-place-task.md](04-pick-place-task.md)
