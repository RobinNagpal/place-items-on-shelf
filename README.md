# place-items-on-shelf

A multi-robot evaluation monorepo for prototyping a "place items on a shelf" task across different robotic arms. Simulation first; hardware is only ordered once a viewer + simulator pipeline works end-to-end.

## Layout

```
.
└── robots/
    ├── elephant-robotics-best-option/   # decision record: which Elephant Robotics arm to use
    └── mycobot-280-pi/                  # Step 1 (this round): no-hardware URDF viewer in RViz
```

| Robot / task | Folder | Status |
|---|---|---|
| Pick best Elephant Robotics arm | [`robots/elephant-robotics-best-option/`](robots/elephant-robotics-best-option/) | Decision: myCobot 280 Pi |
| myCobot 280 Pi | [`robots/mycobot-280-pi/`](robots/mycobot-280-pi/) | Step 1: URDF-in-RViz viewer working |

## Cloning

This repo uses git submodules to vendor in vendor ROS 2 SDKs. **You must initialise them or builds will find zero packages.**

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
ls robots/mycobot-280-pi/src/mycobot_ros2/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf
# Expected: the path is printed back.
```

## Where to start

If you want to run the myCobot 280 Pi viewer on your machine, follow:

1. [`robots/mycobot-280-pi/docs/install.md`](robots/mycobot-280-pi/docs/install.md) — one-time ROS 2 Humble setup on Ubuntu 22.04 (incl. WSL 2).
2. [`robots/mycobot-280-pi/docs/verify-env.md`](robots/mycobot-280-pi/docs/verify-env.md) — quick checks before you build.
3. [`robots/mycobot-280-pi/docs/run.md`](robots/mycobot-280-pi/docs/run.md) — build `mycobot_description` and launch the viewer.
