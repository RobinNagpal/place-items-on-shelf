# Task Orchestration

A pick is not one motion. It's many: detect the object, plan above
it, descend, close the gripper, check the grasp, lift, plan to the bin,
release, retreat. Each step depends on the last and any of them can
fail.

The orchestrator is the **software that runs that sequence and decides
what to do when something breaks.** If the gripper closes on nothing,
do you retry, give up, or call a human? That answer lives here.

This file is just about which orchestration framework to use.

## What you check, before anything else

- **How many distinct tasks does the robot do?** One task with five
  steps is fine in a simple state machine. Twenty tasks sharing
  primitives need a behaviour tree or a planner.
- **How often does it fail, and how do you want to react?** "Re-plan
  on detection failure" is one branch; "stop and ask the operator" is
  another.
- **Is the sequence fixed (pick from this conveyor, drop here) or
  dynamic (decide based on what's in the bin)?**
- **Who edits the task definition?** A robotics engineer? A factory
  technician? The answer shapes how visual / textual the framework
  needs to be.

## The main options

### Behaviour Trees (BTs)

A behaviour tree is a hierarchical, reactive control structure. Each
tick walks the tree from the root; nodes return `Success`, `Failure`,
or `Running`. Composition nodes (`Sequence`, `Fallback`, `Parallel`)
combine children; leaf nodes do the actual work.

Behaviour trees are the modern default for robotics orchestration.
They're easier to extend than monolithic state machines and naturally
encode "try X, on failure try Y."

- **BehaviorTree.CPP (BT.CPP)** — the standard C++ behaviour-tree
  library in ROS 2. Has a graphical editor (Groot 2 / Groot 3) for
  visual editing.
- **`py_trees` + `py_trees_ros`** — Python behaviour-tree library
  popular in research.

**Best for:** any pick-and-place stack with more than one task, any
system that needs robust failure handling, anything you want a
non-coder to edit visually.

### State machines

A finite state machine: states, transitions, events. Older but still
fine for simple systems.

- **SMACH** — the ROS 1 standard, now ported to ROS 2 as `yasmin`
  and others.
- **YASMIN** — ROS 2 state-machine library, Python and C++.
- **State Machine pattern in plain code** — for the simplest
  sequences, sometimes you don't need a framework at all.

**Best for:** linear sequences with few branches. Don't push them past
~10 states before you regret it.

### Task / motion planning frameworks

Higher-level than BTs and FSMs: describe the *goal*, let the framework
decide the steps.

- **MoveIt Task Constructor (MTC)** — ROS 2 framework for stacking
  motion-planning stages (approach, grasp, retreat) and reasoning about
  the whole pipeline. Pair with MoveIt 2.
- **Skiros2** — skill-based task planner from research, integrates
  with ROS 2.
- **ROSPlan / PlanSys2** — classical PDDL task planning glued into
  ROS 2.

**Best for:** assembly-style tasks where the steps aren't fixed; the
robot reasons about pre- and post-conditions.

### LLM-driven orchestrators

A newer category: an LLM picks the sequence of skills.

- **Code-as-Policies** — pattern: LLM writes Python that calls your
  motion / perception APIs.
- **SayCan, Inner Monologue, ProgPrompt** — research patterns for
  grounding LLM plans.
- **Bespoke setups** combining a frontier LLM with a small ROS 2
  skill library.

**Best for:** demos and research where the operator describes the task
in English. Not yet a fit for repeatable production cycle times.

### Vendor task languages

Inside the cobot controller itself.

- **UR PolyScope** — drag-and-drop programs on the teach pendant.
- **FANUC TPP / KAREL** — controller scripting.
- **ABB RAPID, KUKA KRL, Yaskawa INFORM** — same for each big four.
- **Techman TMflow** — visual flow editor.

**Best for:** production cells where the *robot vendor* is the system.
ROS 2 orchestration runs on the side IPC; the vendor language runs the
actual motion.

## Action vs. service vs. topic — the ROS 2 building blocks

Within ROS 2, orchestrators are built on three primitives:

- **Topics** — broadcast streams ("here's the current joint state").
- **Services** — synchronous request/response ("compute IK for this
  pose").
- **Actions** — long-running goals with feedback and cancellation
  ("execute this trajectory; tell me when you're done").

A well-built skill exposes itself as a **ROS 2 action**, so an
orchestrator (behaviour tree leaf, state-machine state) can fire it,
wait for completion, get feedback, and cancel cleanly. This is the
detail beginners most often get wrong: they wire skills as topics or
services and then can't cancel them.

## How to pick

1. **Single robot, multiple tasks, some failures expected?** →
   BehaviorTree.CPP + Groot.
2. **One simple sequence, you'll never extend it?** → A plain state
   machine or `yasmin`.
3. **Assembly-like task where steps come from reasoning?** → MoveIt
   Task Constructor.
4. **Research with LLMs?** → Code-as-Policies-style on top of a
   small skill library.
5. **Production cell, vendor is the system?** → Vendor language for
   the core, BT / FSM only for the perception side.

## Output of this file — your orchestration plan

```
Orchestrator framework:  BehaviorTree.CPP / py_trees / yasmin / MTC / vendor
Visual editor:           Groot 2 / Groot 3 / vendor IDE / none
Skill interface:         ROS 2 action / service / topic-only (avoid)
Failure handling:        retry N times / fallback action / human handoff / safe stop
Human-in-the-loop?:      no / Slack alert / pendant prompt / web dashboard
Logs the task tree?:     yes (logger: ___) / no
Tree / FSM stored in:    XML / YAML / code / vendor file
```

## Common mistakes

1. **One giant state machine for everything.** Splits into ten BTs you
   actually understand.
2. **No timeout on any step.** A motion that hangs blocks the whole
   tree forever. Always give every action a timeout.
3. **Returning Success too eagerly.** A `Grasp` step that returns
   Success before verifying the grasp held will plant errors
   downstream.
4. **Failure handling deferred to "later."** Without explicit failure
   branches, the robot does undefined things on partial success.
5. **Hard-coded waypoint poses inside the BT.** Treat waypoints as
   parameters; load them from a config file.

## What's next

The orchestrator runs the task. When something goes wrong, you need
to be able to *see* what happened. That's logging and observability.

→ Next: [09-data-logging-and-observability.md](09-data-logging-and-observability.md)
