# myCobot 280 Pi — Documentation

These docs explain **how to set up, run, and understand** the myCobot 280 Pi
simulation pipeline. They're written for someone new to ROS 2 robotics who
wants the whole pick-and-place demo from the ground up — not just "the
commands" but *what each piece does* and *why we need it*.

The docs are grouped by purpose, not by date added:

- **Setup** — get from a clean Ubuntu install to a running demo. Skip if your
  workspace is already built.
- **Concepts** — read these once setup is done. They build a mental model of the
  four programs that make the demo work.
- **Deep dives** — once you've read the concepts, these explain *how* perception and planning
  actually work under the hood. Skip them if you only care about running the demo.
- **Recipes** — short "how to do X" guides. Use as needed.
- **Reference** — glossary you can flip to whenever a term confuses you.

## Reading order

### Setup (start here if nothing is installed yet)

0. **[setup/README.md](setup/README.md)** — section index. Walks four ordered
   docs covering system prerequisites, workspace + upstream, this repo's
   package, and the first run. Output: you can launch
   `ros2 launch cobot280_moveit_task move_to_named_pose.launch.py` and watch the
   arm move.

### Concepts (start here if your install already works)

1. **[concepts/01-gazebo.md](concepts/01-gazebo.md)** — Gazebo, the "physics sandbox"
   where the robot lives. Run *just this* and you see a robot you can't move yet.
2. **[concepts/02-rviz.md](concepts/02-rviz.md)** — RViz, a second window that shows
   what the robot itself *thinks* the world looks like. Different from Gazebo on
   purpose.
3. **[concepts/03-moveit.md](concepts/03-moveit.md)** — MoveIt, the "brain" that turns
   a goal ("move the hand to point X") into a smooth, collision-free joint motion.
   Also introduces the **ros2_control** layer that sits beneath it.
4. **[concepts/04-pick-place-task.md](concepts/04-pick-place-task.md)** — How the
   camera, the planning logic, and the arm talk to each other to actually pick up the
   red cylinder and put it down somewhere else.

### Deep dives (the math behind concepts 3 and 4)

5. **[deep-dives/how-perception-works.md](deep-dives/how-perception-works.md)** —
   Plain-English explanation of how perception identifies the cylinder without any AI:
   surface normals, clustering, RANSAC shape-fitting. What's actually happening inside
   the `get_planning_scene_server` node.
6. **[deep-dives/how-planning-works.md](deep-dives/how-planning-works.md)** — Companion
   to the perception deep-dive. How the arm decides which joint angles to use: the
   hardcoded task "recipe" (in `mtc_node.cpp`) vs. the live joint-trajectory math
   (OMPL randomised search). No AI here either.

### Recipes (operational)

7. **[recipes/the-four-terminals.md](recipes/the-four-terminals.md)** — A one-page
   cheatsheet that ties all four terminals together: what each one is, what it talks
   to, in what order to launch. Intentionally redundant with the concept docs so you
   can keep just this one open while running the demo.
8. **[recipes/viewing-camera-output.md](recipes/viewing-camera-output.md)** — Two
   short recipes for "I just want to see what the camera is seeing" — via RViz, or via
   Gazebo's own built-in viewer. Plus a bonus section for visualising the
   PlanningScene (the green shapes perception identifies).

### Reference

9. **[reference/glossary.md](reference/glossary.md)** — Short definitions of every
   acronym and jargon word you'll bump into.

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
