# v1_simple_pick

A small ROS 2 + Gazebo Harmonic pick-and-place demo.

## What these tools are

- ROS 2: the robotics middleware used to run nodes and pass messages between them.
- Gazebo (Harmonic): the physics simulator where the robot and world run.
- URDF/xacro: the robot description format; xacro is a macro system that generates URDF.

## What is in this world

- One shelf (table-like platform).
- One item on top (the model is named "soda_can", shaped as a small box).

## Robot structure

- A differential-drive mobile base.
- A 3-DOF arm mounted on the base.
- A parallel-jaw gripper for grasping.
- A small tray on the base to place the item.

The robot parts (base, arm, gripper, tray) are defined in URDF/xacro and
loaded through ROS 2; Gazebo reads that description to build the robot in
the simulator.

## v1_simple_pick folders

- pos_v1_bringup: launch files, Gazebo world, and bridge/controller configs.
- pos_v1_description: robot URDF/xacro description.
- pos_v1_task: the ROS 2 node that runs the pick-and-place workflow.

## What the robot does (workflow)

1. Drive forward to the shelf.
2. Move the arm to a pre-grasp pose above the item.
3. Lower, close the gripper, and lift the item.
4. Drive back to the tray area.
5. Lower, open the gripper, and place the item on the tray.

This is a scripted, hardcoded sequence with fixed poses and distances.

## Hardcoded pre-instructions (fixed plan)

- The shelf and item positions are fixed in the world setup
	(shelf center around x=2.0, z=0.5; item center around x=1.85, z=0.555).
- The base drives to fixed x targets: approach at x=1.54, then return to x=0.0.
- Drive motion uses fixed limits: speed 0.12 m/s and accel 0.10 m/s^2.
- Arm targets are fixed: pre-grasp z=0.85, approach z=0.65, grasp at the item
	center, lift to item z + 0.15, carry at robot x=0.20, place at z=0.29.
- Gripper commands are fixed: open 0.045 m and grasp 0.012 m (a tight squeeze).
- If the item or shelf moves, the sequence may not succeed.

## How these instructions are used (ROS 2)

- The fixed plan is inside a ROS 2 node that runs the sequence in order.
- The node publishes `cmd_vel` for the base and joint trajectories for the arm
	and gripper; the Gazebo + ros2_control controllers execute them.
- The robot follows the plan because the node keeps sending these commands.
	There is no perception or decision logic in this version.

## Gazebo vs ROS 2 (what is created where)

- ROS 2 defines the robot model (URDF/xacro) and runs the control nodes.
- Gazebo creates the simulated world and renders the robot from that model.

## Shapes in Gazebo

- You can create many shapes (box, cylinder, sphere) and also load meshes.
- Most things are built from basic shapes, but you can use custom models too.
