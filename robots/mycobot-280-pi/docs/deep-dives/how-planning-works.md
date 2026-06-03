# How Planning Works (Hardcoded Recipe + Live Motion Math)

Companion to [how-perception-works.md](how-perception-works.md). That doc explained
how the robot identifies the cylinder. This one explains what happens *after* — how
the arm actually moves to pick it up.

## Short answer: there are two levels

| Level | What it is | Who decides it |
|-------|------------|----------------|
| **The recipe** (the sequence of stages: approach → grasp → close → lift → carry → lower → open → retreat) | Hardcoded by the developer (addison) in C++ (`mtc_node.cpp`) and parameterised in `mtc_node_params.yaml`. | The developer (you can tune parameters without recompiling) |
| **The actual joint motions** (which joint angles, in what order, taking what path through space) | Computed fresh every run by MoveIt's OMPL planner. Not hardcoded. Not AI either — classical randomised search. | An algorithm, at runtime |

So when you watch the arm pick up the cylinder, roughly 70% of what you're watching
is **computed live** and 30% is **hardcoded structure**. The hardcoded part is the
smaller — the impressive part is the math doing real work in real time.

## The cooking analogy

Imagine a recipe book that says:

> 1. Chop the onions.
> 2. Heat oil in a pan.
> 3. Sauté the onions for 3 minutes.
> 4. Add the rice.
> 5. Stir occasionally for 10 minutes.

The **recipe** (the sequence of steps in that order) is fixed. The recipe book author
wrote it once. You don't get to skip the heat-oil step.

But **how you actually chop**? That's improvised. You hold the knife however feels
right, you chop at whatever speed your hand wants, you adjust if the onion rolls
away. The recipe doesn't dictate the angle of your wrist.

MoveIt + MTC works exactly the same way:

- **The recipe** = the task graph in `mtc_node.cpp`. addison hardcoded the stages.
- **The actual joint motions** = computed by MoveIt at runtime, freshly each run.

## Where each piece of knowledge lives

| What                                                                            | Where it lives                                | Editable without rebuild? |
|---------------------------------------------------------------------------------|-----------------------------------------------|---------------------------|
| The sequence (approach → grasp → close → …)                                     | `mtc_node.cpp` (C++ code)                     | No (recompile)            |
| Each stage's specific goal (target dimensions, place pose, approach distance)   | `mtc_node_params.yaml`                        | Yes (just restart)        |
| The actual joint angles and trajectory                                          | Computed live by MoveIt's OMPL planner        | N/A (recomputed always)   |
| The robot's body (which joints connect where, link lengths, joint limits)       | URDF file (robot description)                 | Yes (but unusual)         |
| Joint groups (e.g. "arm" = 6 joints) and named poses ("home", "open", "closed") | SRDF file                                     | Yes                       |
| Inverse kinematics (given a gripper xyz pose, what joint angles?)               | MoveIt's KDL plugin                           | N/A (algorithm)           |
| Gripper open/close (single joint, no path planning needed)                      | `gripper_action_controller`                   | N/A                       |

## Walk through one stage — "approach object"

Let's make this concrete with the "approach object" stage, where the arm moves down
to position the gripper above the cylinder before closing.

### What's hardcoded for this stage

In `mtc_node.cpp`, addison wrote (paraphrased):

> "Move the gripper DOWN by 'between 1.5 mm and 30 cm' along the Z axis, starting
> from wherever it is now."

That's the **goal description**. It's hardcoded:
- Direction = Z axis (down)
- Min distance = 0.0015 m
- Max distance = 0.3 m

These specific numbers come from `mtc_node_params.yaml`:

```yaml
approach_object_min_dist: 0.0015
approach_object_max_dist: 0.3
approach_object_direction_z: 1.0   # 1.0 = down in the world frame
```

So the *intent* is hardcoded. The *exact distance* and *exact joint angles* are NOT.

### What MoveIt computes at runtime

Given that goal, MoveIt has to figure out:

1. **Start state** — what are the arm's current joint angles? It reads them from
   `/joint_states` (which Gazebo publishes continuously).
2. **The actual path** — a sequence of joint angles, sampled over time, that moves
   the gripper down by some amount between 1.5 mm and 30 cm without:
   - Colliding with the table (perception's `support_surface` collision object).
   - Colliding with other objects (the cardboard box, mustard bottle, etc.).
   - Colliding with the arm's own links (`link1` shouldn't pass through `link3`).
   - Exceeding joint speed/torque limits.
3. **The end state** — the joint angles that put the gripper at the final position.

That computation happens inside MoveIt's OMPL planner. It's an algorithm that runs
many random tries (similar to perception's RANSAC but in joint space) and returns
the first path that satisfies all the constraints. **Different runs can produce
different paths** — OMPL is non-deterministic by design.

## The four inputs we give MoveIt per stage

For every stage, MoveIt needs four things:

1. **Where the arm currently is** — read live from `/joint_states`.
2. **Where you want it to go** — provided by the stage's code. Could be:
   - "These specific joint angles" (used for `home`, `ready`).
   - "Put the gripper at this xyz position with this orientation" (used for grasp,
     place). MoveIt then runs **inverse kinematics** to figure out joint angles that
     achieve that gripper pose.
   - "Move the gripper in this direction by this distance" (used for approach, lift,
     retreat — these are called Cartesian moves).
3. **Constraints** — things to keep true throughout the motion. Examples:
   - "Keep the gripper level while moving" (so the cylinder doesn't tip when
     carried).
   - "Don't go above 30% of max speed" (so motions are gentle).
4. **The current planning scene** — what collision objects exist (table, other YCB
   items, even the cylinder once it's attached to the gripper).

Given those inputs, MoveIt's planner does its random-sampling search and returns a
trajectory: "joint 1 should be at angle A at time 0, angle B at time 0.5s, …, angle
Z at time 2s". That trajectory then gets sent to `arm_controller`, which moves the
actual joints in Gazebo (or on a real robot).

## What about the gripper open/close?

Much simpler. The gripper is a single joint that goes from "open" (some angle) to
"closed" (some other angle). There's no planning needed — no path to figure out, no
collisions to avoid mid-motion (the planning scene logic handles "allow the gripper
to touch the object you're about to grasp" with the `allow collision` stages in the
task graph).

When MTC's stage says "close gripper", it just sends one command to
`gripper_action_controller`: "go from current angle to 'half_closed' angle". The
controller does it. Done.

The "open" and "closed" angles themselves are named poses defined in the **SRDF**
file (`mycobot_280.srdf`), e.g.:

```xml
<group_state name="open" group="gripper">
  <joint name="gripper_controller" value="0.0"/>
</group_state>
<group_state name="closed" group="gripper">
  <joint name="gripper_controller" value="-0.7"/>
</group_state>
```

So even the gripper angles are config-driven, not magic numbers in code.

## Is anything "hardcoded" in the bad sense?

Not really. The task **structure** (which stages, in what order) is in code, which
is what we'd call hardcoded — but that's expected and necessary. You can't write a
"pick something" program that doesn't say "first approach, then grasp, then lift"
somewhere.

The actual **numbers** are all in:

- `mtc_node_params.yaml` (task parameters: target dimensions, approach distances,
  place pose, gripper poses)
- `mycobot_280.srdf` (named poses: "home", "ready", "open", "closed")
- `mycobot_280.urdf` (robot geometry: link lengths, joint limits)

You can tune any of these without recompiling. Change "approach by max 30 cm" to
"by max 10 cm" in the YAML, restart Terminal 4, the arm now approaches with smaller
distances.

The actual **motions** (which exact joint trajectory takes the gripper from start
to goal) are computed fresh every run by OMPL — that's what "motion planning"
means. This is the same OMPL that powers most modern industrial robot software.

## Is MoveIt "intelligent"? Is THIS AI?

Same answer as perception: no, not in the modern "neural network" sense.

OMPL is a randomised search algorithm. It doesn't learn from past runs. It doesn't
have a model of "what makes a good motion" trained on millions of examples. It just
tries random joint configurations between start and goal, checks each for collisions
and joint-limit violations, and assembles a valid sequence.

The "intelligence" is purely in the math:

- How to randomly sample joint angles efficiently.
- How to check collisions fast (using approximated collision shapes).
- How to interpolate smoothly between sampled poses.

Some newer MoveIt extensions DO use neural networks (e.g. "learning to predict good
seed poses for IK"), but they're optional. addison's setup uses the classical OMPL
backend.

## The full data-flow picture

Here's everything from "perception identified the cylinder" to "arm picks it up":

```
PERCEPTION                                    PLANNING & EXECUTION
──────────                                    ────────────────────
Camera → 3D dots → cluster → fit cylinder    For each stage in the task graph:
       → similarity → "cylinder_1 wins"
                                              1. Read current joint angles from
                                                 /joint_states
        |                                     2. Read goal from stage's code
        | "target = cylinder_1"                  + parameters
        | "support_surface = table"           3. Read planning scene
        v                                        (collision objects)
                                              4. OMPL runs: random samples,
MoveIt's planning scene = {                      collision checks, returns
  robot's URDF +                                 trajectory
  cylinder_1 (collision object) +              5. Send trajectory to
  table (support_surface) +                       arm_controller (or
  other YCB obstacles                             gripper_action_controller
}                                                 for grip stages)
                                              6. Gazebo's joints move
                                              7. Wait for trajectory to finish
                                              8. Move to next stage
```

Everything to the left of the arrow is perception
([how-perception-works.md](how-perception-works.md)). Everything to the
right is what this doc covered.

## TL;DR

- **The recipe (sequence of stages) is hardcoded** by the developer in
  `mtc_node.cpp` and parameterised in `mtc_node_params.yaml`. You can tune the
  parameters without recompiling.
- **The actual joint trajectories are computed fresh every run** by MoveIt's OMPL
  planner. It's a randomised search algorithm — no AI, no learning, just classical
  motion-planning math.
- **What you give MoveIt per stage**: where the arm is now, where you want it to go,
  what to avoid (collisions), and any constraints. MoveIt figures out the rest.
- **The gripper** is trivial: one joint, one command, no planning needed.
- **The robot's body** (joint locations, link lengths) lives in URDF; the named
  poses (home, ready, open, closed) and joint groups live in SRDF. Both are config
  files, not code.

So perception + planning together = classical robotics. Each piece is decades-old
math. The "magic" is in how cleanly the pieces fit together, not in any one of them
being clever.

→ Next: [../recipes/the-four-terminals.md](../recipes/the-four-terminals.md) — a
one-page cheatsheet for the full launch sequence.
