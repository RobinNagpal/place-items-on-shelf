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

## Getting started

- **Brand-new install, want to actually run things?** Start at
  [`robots/mycobot-280-pi/docs/setup/`](robots/mycobot-280-pi/docs/setup/) — four
  ordered docs that take a fresh Ubuntu 24.04 to a running pick-and-place demo.
- **Want to understand the system without running it?** Skip setup and read
  [`robots/mycobot-280-pi/docs/concepts/01-gazebo.md`](robots/mycobot-280-pi/docs/concepts/01-gazebo.md)
  first.

## Docs

The plain-English walkthrough lives in
[`robots/mycobot-280-pi/docs/`](robots/mycobot-280-pi/docs/). Start with
[`docs/README.md`](robots/mycobot-280-pi/docs/README.md) for the reading order
(setup → concepts → deep-dives → recipes → reference).

## Source

- [`robots/mycobot-280-pi/`](robots/mycobot-280-pi/) — everything specific to
  the myCobot 280 Pi. See its
  [`README.md`](robots/mycobot-280-pi/README.md) for the per-robot overview.
- [`robots/mycobot-280-pi/cobot280_moveit_task/`](robots/mycobot-280-pi/cobot280_moveit_task/) —
  our minimal custom MoveIt 2 task package (the "hello world" path that uses
  `MoveGroupInterface` directly).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the branch / PR workflow, code
conventions, and documentation conventions. AI agents working in this repo
should start at [`CLAUDE.md`](CLAUDE.md).
