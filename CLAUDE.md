# CLAUDE.md

This file is the entry point for any AI agent (Claude Code or otherwise) working
inside this repo. Humans should start at [`README.md`](README.md) instead.

## What this project is

`place-items-on-shelf` is a robotics project focused on **picking and placing
objects with small 6-DOF arms in simulation, and eventually on real hardware**.
The current target is the **myCobot 280 Pi** (Elephant Robotics). The longer-term
goal is loading sample vials into racks on an HPLC autosampler.

The repo is structured per-robot — each supported robot gets its own folder
under `robots/<model>/` with both its own packages and its own docs. Today only
`robots/mycobot-280-pi/` exists. There is also a top-level `docs/` series for
**robot-agnostic** beginner-friendly robotics learning, written one layer at a
time.

## Repo layout

```
.
├── README.md                       # Human entry point
├── CLAUDE.md                       # This file
├── CONTRIBUTING.md                 # Contribution guide for code + docs
├── docs/                           # Robot-agnostic beginner learning series
│   ├── README.md
│   └── 01-understanding-the-problem.md
└── robots/
    └── mycobot-280-pi/
        ├── README.md               # Folder-level overview
        ├── cobot280_moveit_task/   # Custom ROS 2 / colcon package
        │   ├── package.xml
        │   ├── CMakeLists.txt
        │   ├── src/
        │   ├── launch/
        │   └── README.md
        └── docs/
            ├── README.md           # Doc-set table of contents
            ├── setup/              # Get from a clean install to a running demo
            ├── concepts/           # What each piece of the system does
            ├── deep-dives/         # Math behind perception and planning
            ├── recipes/            # Operational cheatsheets
            └── reference/          # Glossary
```

## Two doc trees, on purpose

- **`docs/` (top-level)** — robot-agnostic, beginner-friendly, "how to think
  about a robotic-arm problem from scratch". Layered series, one topic per
  doc, no code. Read if you are new to robotics and want concepts before
  specifics.
- **`robots/<model>/docs/`** — robot-specific. Concrete commands, exact log
  lines you should see, gotchas tied to that robot's setup. Read if you want
  to run *this* robot's demos.

When adding a new doc, decide first which tree it belongs in. Robot-specific
goes under `robots/<model>/docs/`; robot-agnostic concepts go under top-level
`docs/`.

## Tooling

- **Language:** C++17 (ROS 2 nodes), Python (launch files), CMake (build).
- **Build system:** `colcon` — packages here are meant to be cloned into a
  `~/ros2_ws/src/` colcon workspace alongside upstream `mycobot_ros2`.
- **ROS distribution:** ROS 2 Jazzy.
- **No top-level lint / format / test scripts yet.** The project is small enough
  that quality checks happen at the package level:
  `colcon build --packages-select <pkg>` is the closest thing to a CI command
  today.

If you need to introduce a linter, formatter, or top-level CI workflow, **ask
first** — the choice will set conventions for every future package and should be
made deliberately rather than scaffolded ad-hoc.

## Conventions

- **Per-robot folders.** Anything specific to a single robot model lives under
  `robots/<model>/`. Cross-robot shared code (when it exists) will live under a
  separate top-level folder; do not add such code into a per-robot folder.
- **Upstream packages stay upstream.** We depend on
  `automaticaddison/mycobot_ros2`, we don't fork it. Local patches to upstream
  are documented per-fix in our concept docs (e.g.
  [`robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md`](robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md))
  so they're discoverable when someone re-clones upstream and is missing the fix.
- **Docs are plain English first.** The audience is "someone new to ROS 2
  robotics who wants to understand the whole pipeline". Avoid jargon without a
  glossary entry; the glossary lives at
  [`robots/mycobot-280-pi/docs/reference/glossary.md`](robots/mycobot-280-pi/docs/reference/glossary.md).
- **Doc files are grouped by purpose, not by date.** When adding a new
  robot-specific doc, put it in `setup/`, `concepts/`, `deep-dives/`,
  `recipes/`, or `reference/` as appropriate, and update the section's
  `README.md` index.

## Working in this repo as an agent

- Read the relevant `docs/` files **before** editing code. The existing docs
  already record subtle gotchas (controller-name typos, world-file edits,
  `execute: true`); duplicating that investigation wastes time.
- If you change behavior of a runnable demo, update the matching concepts /
  recipes doc in the same PR.
- If you add a new package or robot folder, add a folder-level `README.md` and
  link to it from this file's repo layout section.
- Don't add a `LICENSE` file without checking with a maintainer first — that's a
  legal choice, not a documentation choice.
