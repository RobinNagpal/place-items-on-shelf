# myCobot 280 Pi — Concepts in Plain English

These docs explain **what each piece of the simulation does** and **why we need it**, without
diving into code. They're written for someone new to ROS 2 robotics who wants to understand
the whole pick-and-place demo from the ground up.

Read them in order — each one builds on the previous.

## Reading Order

1. **[01-gazebo.md](01-gazebo.md)** — What Gazebo is. The "physics sandbox" where the robot
   lives. Run *just this* and you see a robot you can't move yet.
2. **[02-rviz.md](02-rviz.md)** — What RViz is. A second window that shows you what the
   robot itself *thinks* the world looks like — frames, sensors, plans. Different from
   Gazebo on purpose.
3. **[03-moveit.md](03-moveit.md)** — What MoveIt is. The "brain" that turns a goal
   ("move the hand to point X") into a smooth, collision-free joint motion.
4. **[04-pick-place-task.md](04-pick-place-task.md)** — How the camera, the planning logic,
   and the arm talk to each other to actually pick up the red cylinder and put it down
   somewhere else.
5. **[05-the-four-terminals.md](05-the-four-terminals.md)** — A one-page reference that
   ties all four terminals together: what each one is, what it talks to, in what order
   to launch.
6. **[06-glossary.md](06-glossary.md)** — Short definitions of every acronym and jargon
   word you'll bump into.
7. **[07-viewing-camera-output.md](07-viewing-camera-output.md)** — Two short recipes
   for "I just want to see what the camera is seeing" — via RViz, or via Gazebo's own
   built-in viewer. Plus a bonus section for visualizing the PlanningScene (the green
   shapes perception identifies).
8. **[08-how-perception-works.md](08-how-perception-works.md)** — Plain-English
   explanation of how perception identifies the cylinder without any AI: surface
   normals, clustering, RANSAC shape-fitting. What's actually happening inside the
   `get_planning_scene_server` node.

## The 30-second big picture

Before drilling in, here's the whole system in one paragraph:

> A **simulated robot arm** (myCobot 280) sits in a **virtual world** (Gazebo) that has
> physics, a table, and some objects. A **virtual camera** sees what's on the table. A
> **perception program** turns the camera's image into a list of objects ("there's a
> cylinder at (x, y, z)"). A **motion planner** (MoveIt) figures out how to move the arm
> from "here" to "above the cylinder", then "down to grab it", then "across the table",
> then "down to release it". Finally, a **controller** sends the planned motion to the
> joints so the arm actually moves.

Four programs running in four terminals coordinate all of this. The rest of these docs
walk through each piece in plain English.

## When you're done reading

You should be able to look at any of the four terminals' log output and roughly
understand what stage the system is in and what each line means. You should also be
able to explain to someone else why we need all four pieces — not just MoveIt, not just
the camera, not just Gazebo.
