# v2 (scaffold)

Scaffolding for the next iteration of the place-items-on-shelf demo.
Nothing here is implemented yet — only the ROS 2 package skeletons exist
so that `colcon build` recognises the workspace.

## Packages

- `pos_v2_bringup` — will hold launch files, the Gazebo world, and bridge/controller configs.
- `pos_v2_description` — will hold the robot URDF/xacro.
- `pos_v2_task` — will hold the ROS 2 node(s) that drive the v2 behaviour.

Mirrors the layout of `v1_simple_pick/` so the two versions can coexist in
the same workspace. What v2 actually *does* differently from v1 is still
TBD; fill in the concrete goals before adding code.
