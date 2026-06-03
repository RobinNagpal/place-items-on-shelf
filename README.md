# place-items-on-shelf

A project for picking and placing objects with a small 6-DOF robot arm in simulation
(and, eventually, on real hardware). Currently focused on the **myCobot 280 Pi**.

## The 30-second big picture

> A **simulated robot arm** (myCobot 280) sits in a **virtual world** (Gazebo) that has
> physics, a table, and some objects. A **virtual camera** sees what's on the table. A
> **perception program** turns the camera's image into a list of objects ("there's a
> cylinder at (x, y, z)"). A **motion planner** (MoveIt) figures out how to move the arm
> from "here" to "above the cylinder", then "down to grab it", then "across the table",
> then "down to release it". Finally, a **controller** sends the planned motion to the
> joints so the arm actually moves.

Four programs running in four terminals coordinate all of this.

## Docs

The plain-English walkthrough lives in
[`robots/mycobot-280-pi/docs/`](robots/mycobot-280-pi/docs/). Start with
[`docs/README.md`](robots/mycobot-280-pi/docs/README.md) for the reading order
(concepts → deep-dives → recipes → reference).

## Source

- [`robots/mycobot-280-pi/cobot280_moveit_task/`](robots/mycobot-280-pi/cobot280_moveit_task/) —
  our minimal custom MoveIt 2 task package (the "hello world" path that uses
  `MoveGroupInterface` directly).
