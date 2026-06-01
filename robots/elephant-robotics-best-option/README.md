# Pick the best Elephant Robotics arm for place-items-on-shelf

This is a **research / evaluation task** — not a hardware bring-up. Goal: pick which Elephant Robotics arm we will eventually buy, and record the reasoning so a future reader (or future us) can sanity-check the call.

We will **simulate first, order later.** No hardware purchase happens before we have a URDF working in RViz / Gazebo and a basic motion-planning loop in MoveIt. The arm we pick has to make that simulation step as cheap as possible.

Once a winner is chosen, the next PR creates a sibling folder under `robots/` (e.g. `robots/mycobot-280-pi/`) with the URDF viewer scaffold, the same way [`robots/rebot-arm-b601-dm/`](../rebot-arm-b601-dm/) was set up. This folder stays as the decision record.

## What we are optimising for (in priority order)

1. **Simplest, smallest arm in the lineup.** We are *starting*. We do not need extra payload or extra reach yet — that's complexity we'd pay for and then have to babysit in simulation.
2. **The most tutorials, blog posts, GitHub repos, forum threads on the internet.** Stuck-at-2-a.m. time scales with how many other people have hit the same problem.
3. **Easy sensor integration.** Onboard Linux + USB/I2C/GPIO so a depth camera or AprilTag camera is `apt install` + `ros2 launch`, not a custom bus driver.
4. **First-party simulation packages.** URDF, MoveIt, and Gazebo configs maintained by the vendor — not "you can probably get it working." Without this, "simulate first" is a multi-week yak shave.
5. **Latest currently-shipping revision of whatever we pick** — so docs, firmware, and the ROS 2 driver all match what arrives in the box.

Things we explicitly do **not** want at this stage:

- Higher payload — we are picking up ~100 g objects.
- Longer reach — a tabletop shelf is ~25 cm away.
- Industrial-class hardware (harmonic joints, brakes, integrated controllers). Cool, but it's a different category of project.

## Candidates (Elephant Robotics lineup, as of June 2026)

| Model | Reach | Payload | Repeatability | Onboard compute | First-party ROS 2 sim | Notes for our use case |
|---|---|---|---|---|---|---|
| myCobot 280 (Pi) | 280 mm | 250 g | ±0.5 mm | Raspberry Pi 4 (Ubuntu) | ✅ URDF + MoveIt + Gazebo in [`mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) | **Smallest. Largest community. Onboard Pi → sensors are easy.** |
| myCobot 320 (Pi) | 350 mm | 1 kg | ±1 mm | Raspberry Pi 4 (Ubuntu) | ✅ same `mycobot_ros2` stack | More payload + reach than we need, same software stack. |
| myCobot Pro 450 | 450 mm | 1 kg | ±0.1 mm | Integrated industrial controller | ✅ URDF + MoveIt + Isaac Sim + MuJoCo | Industrial-class (harmonic joints, brakes). Overkill for a starter. |
| myCobot Pro 630 | 600 mm | 2 kg | ±0.5 mm | Integrated industrial controller | ✅ but heavier integration | Way over-spec'd. Wrong form factor for a tabletop benchmark. |

(Specs from Elephant Robotics' product pages and reseller summaries — see Sources at the bottom. We have not independently measured.)

## Filtering against the criteria

- **myCobot Pro 630** — biggest of the four. Reach, payload, footprint, and price are all "industrial cobot" rather than "starter desktop arm." Ruled out by criterion 1.
- **myCobot Pro 450** — better-spec'd than the 320 on paper (harmonic joints, ±0.1 mm) but it's still industrial-class hardware with an integrated controller, and 450 mm reach + 1 kg payload is more than this task needs. Ruled out by criterion 1.
- **myCobot 320 Pi** — same software stack as the 280, but the extra 70 mm of reach and 750 g of payload are unused capability we'd be paying for and tuning around. Same Raspberry Pi compute, so it does not help us on sensors. Held as the **upgrade path** if the 280 turns out to be too small once we move out of simulation.
- **myCobot 280 Pi** — smallest in the lineup, lightest, easiest to keep on a desk. Largest installed base of any Elephant Robotics arm → largest pile of community tutorials, YouTube videos, and GitHub repos. Onboard Raspberry Pi 4 running Ubuntu means USB cameras, depth sensors, AprilTag pipelines, and GPIO peripherals are all `apt`/`pip`/`ros2 launch`-level work, not custom drivers. First-party `mycobot_ros2` ships URDF + MoveIt + Gazebo. We already have prior work targeting this exact arm (the `v3_mycobot_pi` scaffold on the [`robotics-research-pick-hardware` branch](https://github.com/RobinNagpal/place-items-on-shelf/tree/robotics-research-pick-hardware/v3_mycobot_pi)), so the simulation step starts at "extend what's already there" rather than zero.

## Recommendation

**myCobot 280 Pi (current revision).**

Why it's the right pick *for this stage*:

1. **It is the smallest, simplest arm Elephant Robotics ships.** Matches criterion 1 directly. We are not paying for unused payload or reach.
2. **It has the largest community footprint of the family.** Most tutorials, most blog posts, most GitHub examples, most forum threads. When we get stuck on URDF inertials or MoveIt SRDF, somebody else has already debugged it in public.
3. **Onboard Raspberry Pi 4 running Ubuntu makes sensors easy.** USB depth cameras (RealSense, Orbbec), AprilTag detectors, even GPIO pressure sensors are `apt install` + `ros2 launch` — no custom driver work just to read a sensor.
4. **First-party simulation packages.** [`elephantrobotics/mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) provides the URDF, MoveIt config, and Gazebo launch files for this arm specifically. "Simulate first" is realistic, not aspirational.
5. **Latest revision is currently shipping and supported.** The myCobot 280 Pi remains an actively sold, actively documented product — firmware, `pymycobot` SDK, and the ROS 2 packages all track the current hardware.
6. **We already have a head start.** The prior `v3_mycobot_pi` work was built around exactly this arm's dimensions. The next PR's URDF viewer can begin from that foundation rather than starting from scratch.

If we later discover the 280 mm reach or 250 g payload is too tight for the real shelf scene, the **myCobot 320 Pi** is the clean upgrade — same software stack, same sensor story, just a bigger envelope.

## What's NOT in this PR (intentionally)

- No URDF, no launch files, no `colcon` package — that comes in the **next** PR once this recommendation is accepted. The scaffold will follow the [`robots/rebot-arm-b601-dm/`](../rebot-arm-b601-dm/) layout (`launch/`, `rviz/`, `docs/`, `src/` submodule pointing at `mycobot_ros2`).
- No price comparison or purchase decision — that lives outside the repo. Nothing is ordered until simulation is working.
- No benchmark numbers — manufacturer specs only. Real measurements come after delivery.

## Verifying this PR

This is a docs-only change. There is no build, lint, or test to run.

```bash
# Sanity check that the file is readable markdown.
ls robots/elephant-robotics-best-option/README.md
```

## Sources

- [myCobot 280 Pi product page](https://qviro.com/product/elephant-robotics/mycobot-280-pi/specifications)
- [myCobot 280 Pi (Elephant Robotics shop)](https://shop.elephantrobotics.com/products/mycobot-pi-worlds-smallest-and-lightest-six-axis-collaborative-robot)
- [myCobot 320 Pi product page](https://www.elephantrobotics.com/en/mycobot-320-pi-en/)
- [myCobot Pro 450 specifications](https://www.elephantrobotics.com/en/mycobot-pro-450-specifications/)
- [myCobot Pro 450 — Robot Report announcement](https://www.therobotreport.com/elephant-robotics-latest-mycobot-built-meet-industrial-expectations/)
- [myCobot Pro 630 product page](https://shop.elephantrobotics.com/collections/mycobot-pro-630)
- [Elephant Robotics product line summary — Robots International](https://www.robotsinternational.com/Elephant-Robotics.htm)
- [`elephantrobotics/mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) — first-party ROS 2 packages for the myCobot family
