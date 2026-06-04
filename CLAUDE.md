# CLAUDE.md

## What this repo is for

Three things:

1. **Plain-English documentation** about how to build a real robotic-arm cell —
   from picking the task, to picking hardware, to picking software, to
   integration and bring-up. The general (vendor-neutral) docs live in
   [`docs/`](docs/).
2. **Hands-on simulation playground** for one specific arm — the
   **myCobot 280 Pi**. The robot-specific docs, MoveIt 2 task package, and
   simulation source live under [`robots/mycobot-280-pi/`](robots/mycobot-280-pi/).
3. **Small, self-contained code exercises** that implement the items in
   [`docs/learning-checklist.md`](docs/learning-checklist.md). One subfolder
   per checklist item under [`exercises/`](exercises/).

No real hardware is required to follow along. Everything works in simulation.

## Where to read first

- [`README.md`](README.md) — 30-second project overview.
- [`docs/README.md`](docs/README.md) — the layered learning walkthrough
  (requirements → hardware → software → integration). Also contains the
  **writing guidelines** to follow when adding or editing docs.
- [`robots/mycobot-280-pi/docs/README.md`](robots/mycobot-280-pi/docs/README.md) —
  myCobot-specific concepts, deep-dives, recipes, and reference.
- [`exercises/README.md`](exercises/README.md) — index of the implemented
  learning-checklist exercises and the docs convention each one follows.

## When editing docs

Follow the writing guidelines in [`docs/README.md`](docs/README.md). Short
version: simple English, proper Markdown, pinpoint details, no fluff.

## When implementing a learning-checklist item

Each implemented item from [`docs/learning-checklist.md`](docs/learning-checklist.md)
lives in its own folder under [`exercises/`](exercises/), named
`NN-short-slug/` (e.g. `01-custom-gazebo-world/`, `02-read-and-annotate-urdf/`).

**Keep the code as small as possible** — just enough to satisfy the "Done
when" check from the checklist. Comment the code so a beginner can follow
it: short sentences, plain English, and one comment per non-obvious step.
No essay-length comments; the conceptual context belongs in the docs.

**Every exercise folder must contain these three docs** (in addition to
the code or annotation files):

- **`README.md`** — high-level overview for a beginner.
  Cover: what the exercise does, the main workflow, the core concepts, the
  libraries / frameworks used, the data flow, the inputs and outputs, and
  one example execution. Goal: a reader who has never touched ROS or
  Gazebo can read this and understand the system at a conceptual level.
- **`ARCHITECTURE.md`** — project structure and per-file responsibility.
  Cover: folder tree, what each file owns, how the files interact, the
  dependency relationships, and any important ROS nodes, topics, services,
  or message types. For each file, say *why it exists*, *what
  responsibility it owns*, and *what depends on it*.
- **`IMPLEMENTATION_NOTES.md`** — engineering decisions, not code
  commentary. Cover: why each library was chosen, the algorithm in plain
  English, the assumptions, the trade-offs, the known failure cases, the
  debugging tips, and any robotics / math / ML concepts the reader needs.
  Do **not** explain every line of code — that's what comments inside the
  code are for.

Use these three doc files as a starting template, not a rigid form. If
one of them has nothing useful to say for a specific exercise (e.g. a
"no code" annotation task), keep it short and explain *why* it's short
rather than padding it.

Writing style for both docs and code comments: very simple English, short
sentences, to the point. Imagine the reader has never written a line of
robotics code before.
