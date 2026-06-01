# place-items-on-shelf

A multi-robot evaluation monorepo for prototyping a "place items on a shelf" task across different robotic arms.

Each robot we evaluate lives in its own self-contained subfolder under `robots/`.

## Layout

```
.
└── robots/
    └── rebot-arm-b601-dm/        # Seeed reBot Arm B601 (Damiao motor variant)
```

## Per-robot evaluations

| Robot | Folder | Status | Source |
| --- | --- | --- | --- |
| reBot Arm B601 DM | [`robots/rebot-arm-b601-dm/`](robots/rebot-arm-b601-dm/) | URDF-in-RViz viewer working; Isaac Sim pending Seeed's ~2026-06-20 drop | [Seeed-Projects/reBotArmController_ROS2](https://github.com/Seeed-Projects/reBotArmController_ROS2) (git submodule) |

To add another arm later, create a new sibling folder under `robots/` with its own `README.md`, `src/` submodule, `launch/`, and `docs/`.

## Cloning

This repo uses git submodules. **You must initialize them or builds will find zero packages.**

Fresh clone:

```bash
git clone --recurse-submodules https://github.com/RobinNagpal/place-items-on-shelf.git
```

If you already cloned, or you switched branches with `git switch` / `git checkout` (which updates the submodule pointer but does NOT update the working tree), run from the repo root:

```bash
git submodule update --init --recursive
```

Verify it worked:

```bash
ls robots/rebot-arm-b601-dm/src/rebotarm_ros2/src
# Expect: rebotarm_bringup  rebotarm_msgs  rebotarmcontroller
```
