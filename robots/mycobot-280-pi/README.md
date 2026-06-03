# myCobot 280 Pi

This folder holds everything specific to the **myCobot 280 Pi** — a 6-DOF
desktop robot arm from Elephant Robotics with a Raspberry Pi controller.
Simulation work is the current focus; real-hardware support is planned but not
yet wired up.

## What's in this folder

```
mycobot-280-pi/
├── cobot280_moveit_task/   # Our minimal custom MoveIt 2 task package.
│                           # The "hello world" path that exercises
│                           # MoveGroupInterface directly — sequencing
│                           # home -> ready -> joint goal -> home.
└── docs/                   # Plain-English documentation for the whole
                            # myCobot 280 Pi pipeline (setup, concepts,
                            # deep-dives, recipes, reference).
```

`cobot280_moveit_task/` is a normal ROS 2 / colcon package — `package.xml`,
`CMakeLists.txt`, `src/`, `launch/`. It lives here because it targets this
specific robot model; if we ever add a second robot (say a UR5e), it would get
its own peer folder `robots/ur5e/` with its own packages and docs.

`docs/` is organised by purpose, not chronology:

- **`docs/setup/`** — get a clean Ubuntu install ready to build and run the
  demos. Start here if nothing works yet.
- **`docs/concepts/`** — what each piece of the simulation does, in plain
  English. Read after setup.
- **`docs/deep-dives/`** — the math behind perception and planning, without AI
  hand-waving.
- **`docs/recipes/`** — operational cheatsheets: the four-terminal launch
  sequence, viewing the camera output.
- **`docs/reference/`** — glossary of acronyms and terms.

The full reading order with links is in
[`docs/README.md`](docs/README.md).

## Quick links

- **Brand-new, nothing installed?** Start with
  [`docs/setup/01-system-prereqs.md`](docs/setup/01-system-prereqs.md).
- **Just want to understand the system without running it?**
  [`docs/concepts/01-gazebo.md`](docs/concepts/01-gazebo.md).
- **Already set up, want the operational cheatsheet?**
  [`docs/recipes/the-four-terminals.md`](docs/recipes/the-four-terminals.md).
- **Want to run only our custom MoveIt task, not the full MTC demo?**
  [`cobot280_moveit_task/README.md`](cobot280_moveit_task/README.md).

## Upstream we sit on top of

- **automaticaddison/mycobot_ros2** — the simulation-focused upstream that
  provides `mycobot_gazebo`, `mycobot_moveit_config`, `mycobot_description`,
  and the `mycobot_mtc_pick_place_demo` (perception + MTC task). We treat it as
  read-only; our work either extends it (new packages here) or applies small
  local fixes to it (documented per-fix in
  [`docs/concepts/04-pick-place-task.md`](docs/concepts/04-pick-place-task.md)).
- **elephantrobotics/mycobot_ros2** — the manufacturer's upstream, focused on
  real hardware. Not integrated yet; mentioned in the glossary as a future
  swap-in for hardware runs.
