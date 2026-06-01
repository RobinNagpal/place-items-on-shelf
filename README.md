# place-items-on-shelf

A multi-robot evaluation monorepo for prototyping a "place items on a shelf" task across different robotic arms. Simulation first; hardware is only ordered once a viewer + simulator pipeline works end-to-end.

The current focus is the **HPLC autosampler tray-loading** use case: a stationary arm that picks small vials from a holder and places them into specific slots in a tray.

## Layout

```
.
└── robots/
    ├── elephant-robotics-best-option/   # decision record: which Elephant Robotics arm to use
    └── mycobot-280-pi/                  # simulation-first bring-up of the chosen arm (Steps 1-7)
```

| Robot / task | Folder | Status |
|---|---|---|
| Pick best Elephant Robotics arm | [`robots/elephant-robotics-best-option/`](robots/elephant-robotics-best-option/) | Decision: myCobot 280 Pi |
| myCobot 280 Pi | [`robots/mycobot-280-pi/`](robots/mycobot-280-pi/) | Steps 1–2 working via upstream `automaticaddison/mycobot_ros2` (Jul 2025 pin) |

## Cloning

This repo uses a git submodule to vendor in the [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2) ROS 2 stack. **You must initialise it or builds will find zero packages.**

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
ls robots/mycobot-280-pi/src/mycobot_ros2/mycobot_gazebo/launch/mycobot.gazebo.launch.py
# Expected: the path is printed back.
```

## Where to start

If you want to run the myCobot 280 Pi simulation on your machine, follow:

1. [`robots/mycobot-280-pi/docs/install.md`](robots/mycobot-280-pi/docs/install.md) — one-time setup (ROS 2 + Gazebo + addison's rosdep deps).
2. [`robots/mycobot-280-pi/docs/verify-env.md`](robots/mycobot-280-pi/docs/verify-env.md) — quick checks before you build.
3. [`robots/mycobot-280-pi/docs/run.md`](robots/mycobot-280-pi/docs/run.md) — Step 1: URDF viewer in RViz.
4. [`robots/mycobot-280-pi/docs/run_sim.md`](robots/mycobot-280-pi/docs/run_sim.md) — Step 2: Gazebo Sim.

For the full Step-by-step roadmap (1 through 7), see [`robots/mycobot-280-pi/README.md`](robots/mycobot-280-pi/README.md).
