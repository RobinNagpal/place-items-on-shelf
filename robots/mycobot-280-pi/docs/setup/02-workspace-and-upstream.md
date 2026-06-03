# 02 — Workspace + Upstream Packages

You now have ROS 2 Jazzy and the apt dependencies in place
([previous doc](01-system-prereqs.md)). This step:

1. Creates a **colcon workspace** to hold all the source-built packages.
2. Clones the **upstream `mycobot_ros2`** repos that our work sits on top of.
3. Builds them once so the simulation, the move_group launch, and the perception
   demo all become runnable.

After this you will have a runnable pick-and-place demo using only upstream code —
nothing from this repo yet. The next doc adds our `cobot280_moveit_task` package.

## Why a separate workspace at all?

ROS 2 ships built packages in `/opt/ros/jazzy`, but those are read-only system
installs. Anything you build from source — addison's `mycobot_ros2`, our
`cobot280_moveit_task`, any custom code — has to live in a writable **colcon
workspace**. The workspace is just a folder with a `src/` subdirectory; `colcon
build` populates `build/`, `install/`, and `log/` next to it.

The conventional location (used throughout these docs) is `~/ros2_ws`. Nothing
prevents you from putting it elsewhere — just substitute your path consistently.

## Create the workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

That's it — `src/` is the only directory you create manually. `colcon build` will
generate the rest the first time you build.

## Clone addison's `mycobot_ros2`

This is the simulation-focused upstream that gives us:

- `mycobot_description` — URDF + meshes for the myCobot 280 arm.
- `mycobot_gazebo` — the Gazebo world and launch files (the "Terminal 1" piece).
- `mycobot_moveit_config` — SRDF, kinematics, joint limits, `move_group` launch.
- `mycobot_mtc_pick_place_demo` — the perception node and the MTC task node
  (Terminals 3 and 4 in [`recipes/the-four-terminals.md`](../recipes/the-four-terminals.md)).

```bash
cd ~/ros2_ws/src
git clone https://github.com/automaticaddison/mycobot_ros2.git
```

> **Heads up:** the docs in this repo reference a couple of small **local edits**
> to addison's code (the brown table model added to the world, the
> `gripper_action_controller` rename in `mtc_node_params.yaml`, and the
> `execute: true` flip). See
> [`concepts/04-pick-place-task.md`](../concepts/04-pick-place-task.md) for the
> rationale on each. None of those are mandatory just to *build* upstream — they
> only matter when you actually want the MTC demo to pick up the cylinder
> end-to-end. Build first, patch later.

## Install per-package dependencies

`rosdep` reads each package's `package.xml` and installs whatever ROS-side
dependencies aren't already on your system.

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

Re-run this whenever you add a new package to `src/` or change a `package.xml`.

## First build

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

`--symlink-install` makes the installed copies of YAML / launch files symlinks back
into `src/`, so you can edit those without rebuilding. C++ code still requires a
rebuild after changes.

Expect this first build to take several minutes — there are a lot of upstream
packages.

## Source the workspace

Every new terminal that uses ROS needs **both** environments sourced. The order
matters: workspace last, so its built packages override the base install if there
are name collisions.

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

If you want to skip typing this in every terminal, add the two lines to your
`~/.bashrc` (or `~/.zshrc`). Some people prefer to keep ROS out of their shell
default and source it on demand — either is fine.

## Smoke-test the upstream

Before adding our own package, confirm the upstream demo at least launches. In
three separate terminals, each with both sources active:

```bash
# Terminal A
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
  world_file:=pick_and_place_demo.world use_camera:=true use_rviz:=false

# Terminal B
ros2 launch mycobot_moveit_config move_group.launch.py use_rviz:=false

# Terminal C
ros2 launch mycobot_mtc_pick_place_demo get_planning_scene_server.launch.py
```

You should see a Gazebo window with the arm, a `[move_group]: You can start
planning now!` line in Terminal B, and a `Get planning scene service created`
line in Terminal C.

If any of those fail, that's an upstream / install issue — fix it before moving
on, because adding our package on top won't help.

## What's next

You now have:

- ROS 2 Jazzy + apt deps (previous doc).
- A `~/ros2_ws` colcon workspace.
- Addison's `mycobot_ros2` cloned and built into it.
- A verified Gazebo launch.

Next: clone *this* repo, add `cobot280_moveit_task` to the same workspace, and
rebuild.

→ Next: [03-our-package.md](03-our-package.md)
