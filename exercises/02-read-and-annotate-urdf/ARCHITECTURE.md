# Architecture — 02 Read and annotate the arm's URDF

## Folder tree

```
02-read-and-annotate-urdf/
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_NOTES.md
└── annotation.md
```

Four markdown files. No code, no build step, no scripts.

## File responsibilities

### `annotation.md`

The **deliverable** of the exercise. Everything the reader produced by
reading the URDF lives here:

- the kinematic tree as an ASCII diagram,
- the link table (which physical part each link represents),
- the joint table (axis, limits, velocity, what each joint controls),
- the home / ready joint values from the SRDF,
- a short "how to verify" recipe.

- **Why it exists:** every later exercise needs a quick-reference for
  joint axes and limits. Without this, every new contributor would have
  to re-read 800 lines of xacro.
- **What it owns:** the *human-readable* truth about the kinematic
  chain.
- **What depends on it:** docs in `../../docs/` cross-link here when
  they need a joint name. Exercises 18–20 lean on the joint limit
  numbers when they set goals.

### `README.md`

Beginner-facing overview. Explains what the exercise is, why anyone
should do it, and how to read `annotation.md`.

### `ARCHITECTURE.md`

This file.

### `IMPLEMENTATION_NOTES.md`

Notes on what URDF source was used, why the numbers were copied rather
than computed, and how to keep this folder in sync with upstream URDF
changes.

## How the files interact

There is no software interaction. The flow is one-directional:

```
upstream URDF  --(read by human)-->  annotation.md
annotation.md  --(read by humans)-->  every later exercise
README.md      --(read by humans)-->  annotation.md
```

`ARCHITECTURE.md` and `IMPLEMENTATION_NOTES.md` are pure meta — they
describe how this folder is organised and why we made the choices we
did.

## Dependency relationships

```
annotation.md
  └── depends on:
        mycobot_280.urdf.xacro  (upstream, not in this repo)
        mycobot_280.srdf        (upstream, not in this repo)
```

The dependency is **textual and frozen**: when we wrote `annotation.md`
we read upstream and copied the numbers. If upstream changes a limit,
`annotation.md` does not magically update — see
[`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md) for how to refresh
it.

## Important ROS / robotics concepts touched

This exercise does not run any ROS nodes, publish any topics, or use
any services. But understanding the URDF unlocks:

- **`/tf` and `/tf_static`** — every link becomes a frame on the TF
  tree at runtime.
- **`robot_state_publisher`** — the ROS node that reads the URDF and
  publishes `/tf` and `/tf_static` based on `/joint_states`.
- **MoveIt planning groups** — defined in the SRDF on top of the URDF,
  they name subsets of joints (e.g. `arm` = joints 1–6).
- **Joint state controllers** — the controllers in ros2_control read
  the URDF's `<transmission>` blocks to know which joints they own.

You do not need any of these to *read* the URDF, but knowing what the
URDF feeds explains why the document is worth producing.
