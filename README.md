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

This repo uses git submodules. After cloning:

```bash
git clone --recurse-submodules https://github.com/RobinNagpal/place-items-on-shelf.git
# or, if already cloned:
git submodule update --init --recursive
```
