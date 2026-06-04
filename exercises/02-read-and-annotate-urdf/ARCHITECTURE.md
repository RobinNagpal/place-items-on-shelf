# Architecture — 02 Read and annotate the arm's URDF

## Folder tree

```
02-read-and-annotate-urdf/
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_NOTES.md
└── annotation.md
```

Four markdown files, no code.

## File responsibilities

- **`annotation.md`** — the deliverable. Kinematic tree, link table,
  joint table, and the autosampler-cell reach arithmetic. Every later
  exercise that touches a joint or a slot pose reads this file first.
- **`README.md`** — beginner-facing overview, points readers at
  `annotation.md` and explains how to re-use it.
- **`ARCHITECTURE.md`** — this file.
- **`IMPLEMENTATION_NOTES.md`** — which URDF source we used, why we
  copied numbers instead of computing them, and what to do when
  upstream changes a limit.

## Dependencies

```
annotation.md
  ├── reads (frozen at copy time):
  │     mycobot_280.urdf.xacro                                (upstream)
  │     mycobot_280.srdf                                      (upstream)
  └── reads (live):
        ../01-custom-gazebo-world/worlds/autosampler_cell.sdf (this repo)
```

Joint values are a snapshot of upstream and need a manual refresh on
upstream changes. The reach check, on the other hand, references the
sibling SDF — update the arithmetic any time peripheral poses move.
