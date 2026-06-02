# 04 — The Pick-and-Place Task: Perception + MTC

This is the document that ties everything together. By the end of it, you should
understand exactly what happens in the seconds between you running the last terminal
command and the arm picking up the red cylinder.

## Two more programs we need

To get from "MoveIt is alive but knows nothing about the world" to "arm picks up the
cylinder", we add two more pieces:

1. **A perception program** — `get_planning_scene_server`. Turns the camera image into
   a list of collision objects.
2. **A task program** — `mtc_node`. Uses MoveIt Task Constructor to plan and execute
   the full pick → transport → place sequence.

These are Terminals 3 and 4 in your 4-terminal sequence.

## Terminal 3 — Perception (`get_planning_scene_server`)

### What it does, in one paragraph

It subscribes to the overhead RGBD camera. Every time it receives a point cloud,
it asks: "Of all these 3D dots, which group of them form a flat horizontal surface
(the table)? And of the remaining dots, which clusters above the table look like
discrete objects?" It turns each object into a simple shape (box or cylinder) with a
position and size, then makes the whole thing available as a service that MoveIt-like
clients can call.

### The pipeline (high-level)

The point cloud goes through a sequence of steps:

1. **Transform** — the camera publishes points in its own coordinate frame
   (`camera_head_link`). We convert them into the robot's base frame (`base_link`) so
   the numbers are useful for MoveIt.
2. **Crop** — discard anything outside a box-shaped region of interest. We don't care
   about points way behind the robot or above the ceiling.
3. **Compute normals** — for each point, estimate which way the local surface is
   facing. Horizontal surfaces have a normal pointing "up".
4. **Find the table** — group points by their normals + position. The biggest flat
   horizontal patch at roughly base_link height is the table.
5. **Cluster the rest** — points above the table get grouped into spatial clusters.
   Each cluster is treated as one object.
6. **Fit shapes** — for each cluster, try fitting a cylinder and a box. Pick whichever
   fits better, with the right dimensions.
7. **Pick the target** — among all detected objects, find the one most similar to what
   the task is looking for (a cylinder of size 0.35 m × 0.0125 m radius).
8. **Build a planning scene** — assemble the table + all object shapes into a service
   response that MoveIt can consume.

### The "no table = nothing works" gotcha

The pipeline only succeeds if step 4 (find the table) finds a horizontal plane at
roughly the same height as the robot's `base_link`. The default world that addison
shipped didn't include a table model, so every horizontal patch the camera saw
was either the ground plane (too low) or floating object tops (wrong shape). We
fixed this by adding a 80 × 80 × 5 cm `brown_table` model to the world.

### The terminal command

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_mtc_pick_place_demo get_planning_scene_server.launch.py
```

Look for:
```
[get_planning_scene_server]: Get planning scene service created and ready to serve requests.
```

It then waits silently — nothing happens until Terminal 4 calls it.

## Terminal 4 — The MTC Task (`mtc_node`)

### What MTC is, plain English

**MoveIt Task Constructor (MTC) is a library for stitching together many small motion
plans into one big "task".** Picking up an object isn't a single motion — it's a
sequence:

> approach the object from above → close the gripper → lift up → carry across the table
> → lower down at the new spot → open the gripper → back off

Each step is its own little planning problem with its own constraints. MTC's job is to
plan all of them in order, and crucially, *to backtrack if a later step is impossible*.
For example, if the grasp pose it picked makes the lift-off step infeasible, MTC will
try a different grasp pose, replan the grasp, and retry the lift.

### The task graph

When you launch `mtc_node`, it builds a graph that looks roughly like this:

```
pick_place_task
├── current state
├── open gripper
├── move to pick
└── pick object
    ├── approach object       (cartesian move down toward grasp pose)
    ├── grasp pose IK         (compute joint angles that put the gripper there)
    │   └── generate grasp pose
    ├── allow collision (gripper, object)
    ├── close gripper
    ├── allow collision (object, support_surface)
    ├── attach object         (treat object as part of the gripper for future planning)
    ├── lift object           (cartesian move up)
    └── forbid collision (object, support_surface)
├── move to place
└── place object
    ├── lower object
    ├── place pose IK
    │   └── generate place pose
    ├── open gripper
    ├── forbid collision (gripper, object)
    ├── detach object
    └── retreat after place
└── move home
```

You'll see exactly these stage names print in the Terminal 4 log when MTC runs. Each
one calls OMPL (inside move_group) to plan its tiny motion. The leaves of the tree are
"generator" stages — they produce many candidate solutions (e.g. all the rotations around
the object that the gripper could approach from), and MTC picks the one that lets the
rest of the tree succeed.

### How perception and MTC talk

The flow when you launch Terminal 4 is:

1. `mtc_node` starts up and connects to `move_group` (Terminal 2).
2. `mtc_node` calls `get_planning_scene_server` (Terminal 3) and asks: "what's in
   the scene?".
3. Perception runs its pipeline once (using the most recent camera frame), returns
   the table + all detected objects.
4. `mtc_node` adds these collision objects to MoveIt's planning scene.
5. `mtc_node` builds the task graph above and asks MoveIt to plan each stage.
6. If `execute: true` in the config, `mtc_node` sends the resulting trajectories to
   `arm_controller` and `gripper_action_controller` (via move_group's
   `ExecuteTaskSolutionCapability`).
7. The arm physically moves in Gazebo. Cylinder gets picked up, carried, dropped at
   the place pose, and the arm goes back home.

### The `execute: true` gotcha

There's a parameter `execute` in `mtc_node_params.yaml` that defaults to `false`. With
that default, MTC plans everything successfully and *only visualises the result* — the
arm does not move. The fix is to set `execute: true`.

Also: the same config file has a typo in the gripper controller name
(`grip_action_controller` should be `gripper_action_controller`). Without that fix, the
arm part moves but the gripper command fails silently because the named controller
doesn't exist.

### The terminal command

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_demo.launch.py
```

### What success looks like

Toward the bottom of the log you'll see (eventually) lines like:

```
[mtc_node]: Task planning succeeded
[mtc_node]: Published solution for visualization
[mtc_node]: Executing task solution     ← only if execute: true
...
[mtc_node]: Task execution completed.
```

And in the Gazebo window: the arm moves, the gripper closes around the red cylinder,
lifts it, swings to a new location, lowers it, releases it, and goes home. 🎉

## "Why does the second run do nothing?" — a common gotcha

You noticed: after the arm successfully picks and places once, re-running
`ros2 launch mycobot_mtc_pick_place_demo pick_place_demo.launch.py` does nothing.

Two likely reasons:

1. **The previous `mtc_node` is still alive.** Look at the bottom of the first run's
   log: it says `Keeping node alive for visualization. Press Ctrl+C to exit.` That node
   is still running. When you start a second one with the same name, ROS 2 may either
   reject it or silently let it idle. **Fix:** Press Ctrl+C in Terminal 4 to kill the
   first `mtc_node` *before* re-launching.

2. **The world state is now different.** After a successful run:
   - The arm is back at home (good).
   - The red cylinder is now at the *place* position, not its original position.
   - The gripper is open.
   - The planning scene that `move_group` holds may still have the old "attached object"
     entry from when the cylinder was being carried.

   The second run's perception step will find the cylinder at its new location (or it
   may have rolled off the table — small upright cylinders are very unstable when the
   gripper opens). MTC will then try to plan a new pick, but the start/goal poses are
   different and the cylinder might be unreachable.

   **Fix:** If the cylinder is still on the table, kill Terminal 4 (Ctrl+C) and re-launch
   it — that usually works. If the cylinder fell off the table, restart Terminal 1
   (Gazebo) too, which respawns the world fresh.

A cleaner long-term fix is to make the task itself reset the scene at the end (e.g.
teleport the cylinder back to its starting pose). That's a feature to add later when
we're authoring our own task instead of running addison's.

## How to see what the camera sees while all this is happening

In a 5th terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run rqt_image_view rqt_image_view
```

Pick `/camera_head/color/image_raw` from the dropdown for the RGB view, or
`/camera_head/depth/image_rect_raw` for the depth view.

Or open RViz (also in its own terminal), add an Image display, point it at the same
topic. RViz has the advantage that you can also see the point cloud, the planned
trajectory, and the perception's collision objects all in the same 3D view.

## What's next, once this all works

A few directions the project could go from here, each with its own follow-up doc:

- **Make the task pick a *different* object** — change `object_type` in the config
  from "cylinder" to "box" and watch perception pick a different YCB item.
- **Replace the world with one of our own** — instead of YCB objects on a table,
  put a small HPLC autosampler model with vial racks. The robot's job becomes
  "load vial into rack". This is the medium-term goal of the project.
- **Replace addison's task graph with a custom MTC task** — write our own `mtc_node`
  for a different sequence, e.g. "pick vial, scan barcode, place in correct rack slot".
- **Run on real hardware** — swap `mycobot_gazebo` for the elephantrobotics driver
  package and the same task should run on a physical myCobot 280 Pi.

→ Next: [05-the-four-terminals.md](05-the-four-terminals.md) — one-page reference for the
full launch sequence.
