# Setup — From Zero to a Running Demo

The other sections of these docs (concepts, deep-dives, recipes) assume you
already have ROS 2 Jazzy installed and a colcon workspace with all the right
packages built. **This section is the missing prelude** — how to get there from
a clean Ubuntu 24.04 install.

Read these in order. Each doc ends by saying what you should have working before
moving on to the next.

1. **[01-system-prereqs.md](01-system-prereqs.md)** — Ubuntu version, ROS 2 Jazzy
   install pointer, build tools, MoveIt / Gazebo / ros2_control apt packages.
   Output: `ros2 --version` and `gz sim --version` both work.
2. **[02-workspace-and-upstream.md](02-workspace-and-upstream.md)** — Create
   `~/ros2_ws`, clone addison's `mycobot_ros2`, install per-package deps with
   rosdep, run the first `colcon build`, source the workspace.
   Output: the upstream Gazebo + move_group + perception terminals all launch.
3. **[03-our-package.md](03-our-package.md)** — Clone this repo into the same
   workspace, rebuild only our package, verify `ros2 pkg list` finds
   `cobot280_moveit_task`.
4. **[04-first-run.md](04-first-run.md)** — Two options: run our custom MoveIt
   task (three terminals), or jump straight to the four-terminal MTC pick-and-place
   demo.

## Where this section fits in the larger doc set

```
setup/         ← you are here. "How do I get the install working."
concepts/      ← what each piece of the running system does.
deep-dives/    ← the math behind perception and planning.
recipes/       ← operational cheatsheets for tasks that come up often.
reference/    ← glossary of terms and acronyms.
```

If you only want to *understand* the system without running it, you can skip
straight to [`concepts/01-gazebo.md`](../concepts/01-gazebo.md). If you want to
*run* it, start at [01-system-prereqs.md](01-system-prereqs.md).
