# 03 — Adding This Repo's Package

You have a working `~/ros2_ws` with addison's `mycobot_ros2` built and the demo
launching ([previous doc](02-workspace-and-upstream.md)). Now layer **this repo's**
`cobot280_moveit_task` package on top so the custom MoveIt 2 sequence in
[`cobot280_moveit_task/README.md`](../../cobot280_moveit_task/README.md) becomes
runnable.

## Why a colcon overlay (not a fork)

addison's repo is the *upstream*. We treat it as read-only — pull updates, apply
small local fixes (see [`concepts/04-pick-place-task.md`](../concepts/04-pick-place-task.md)),
but don't fork it long-term. Anything new we author lives in **this** repo
(`place-items-on-shelf`) and is checked into its own folder under
`robots/<model>/`. Both sit side-by-side in the same colcon workspace; colcon
builds them together.

This pattern (a colcon workspace with an upstream repo *and* an in-house overlay
repo) is the standard ROS 2 way of "we depend on someone else's packages but we
ship our own code".

## Clone this repo into the workspace

```bash
cd ~/ros2_ws/src
git clone https://github.com/RobinNagpal/place-items-on-shelf.git
```

After cloning, the workspace tree looks like:

```
~/ros2_ws/
├── src/
│   ├── mycobot_ros2/                    ← addison's upstream
│   │   ├── mycobot_description/
│   │   ├── mycobot_gazebo/
│   │   ├── mycobot_moveit_config/
│   │   └── mycobot_mtc_pick_place_demo/
│   └── place-items-on-shelf/            ← this repo
│       └── robots/
│           └── mycobot-280-pi/
│               └── cobot280_moveit_task/   ← the package colcon will build
├── build/
├── install/
└── log/
```

colcon recursively scans `src/` for any directory with a `package.xml`, so the
nesting under `robots/mycobot-280-pi/` doesn't need any special configuration.

## Install any new dependencies

In case `package.xml` lists a dependency you don't already have:

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

For `cobot280_moveit_task` specifically the deps (`rclcpp`,
`moveit_ros_planning_interface`, runtime-only `mycobot_*`) are already pulled
in by upstream apt installs, so this should be a quick no-op. Running it
anyway costs nothing and protects against surprise.

## Build only our package (faster than rebuilding everything)

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select cobot280_moveit_task --symlink-install
```

`--packages-select` tells colcon to skip the upstream packages you've already
built. Use this whenever you're iterating on `move_to_named_pose.cpp` or the
launch file — it cuts the rebuild from minutes to seconds.

If you change something across multiple packages, drop `--packages-select` and
let colcon rebuild whatever's stale.

## Source the workspace and verify

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 pkg list | grep cobot280
# should print:  cobot280_moveit_task
```

If the grep is empty, the build either failed or didn't finish — check the colcon
log under `~/ros2_ws/log/latest_build/cobot280_moveit_task/` for the actual error.

## What's next

The package is installed and discoverable. The next doc walks the *first run*:
which terminals to launch, in what order, and what you should see in each.

→ Next: [04-first-run.md](04-first-run.md)
