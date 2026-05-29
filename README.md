# place-items-on-shelf

A project for placing items on shelves.

## What this is (v1_simple_pick)

A scripted, open-loop pick-and-place demo in Gazebo Harmonic. **No perception, no SLAM, no nav stack** — the robot runs a hardcoded `STAGE 1 → STAGE 10` sequence with baked-in poses (shelf at x=2.0, can at x=1.88), a timed `/cmd_vel` drive, analytical IK from a fixed grasp pose, and a friction-based gripper. Move the can off its spawn point and the demo fails: there is no brain, only choreography.

It exists as the **mechanical baseline**: prove the URDF, ros2_control + gz_ros2_control + joint_trajectory_controller, gz-sim DiffDrive, gripper friction, and the world physics all line up before layering anything intelligent on top.

The real-world path on top of this baseline, roughly in order:

1. **Perception** — RGB-D camera, detect the can, publish a pose instead of hardcoding one.
2. **Localisation + navigation** — `nav2` with a map so "go to the shelf" becomes a goal pose, not "drive forward 1.5 m".
3. **Closed-loop manipulation** — IK targets the *perceived* can pose; MoveIt for collision-aware planning.
4. **Behaviour tree / state machine** — replace the linear script with `BehaviorTree.CPP` or `py_trees` so the robot can recover, retry, replan.
5. **Grasp feedback** — force/tactile on the fingers instead of "PID saturated, must be holding it".

When v2 (perception + nav) breaks, v1 is the known-good fallback that confirms the sim/hardware chain still works.

## Status

This repository is in its early stages. Tooling, build setup, and project structure will be added in future commits.
