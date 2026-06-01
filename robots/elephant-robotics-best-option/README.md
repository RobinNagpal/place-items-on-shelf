# Pick the best Elephant Robotics arm for place-items-on-shelf

This is a **research / evaluation task** — not a hardware bring-up. Goal: pick which Elephant Robotics arm we will actually buy and integrate for the `place-items-on-shelf` benchmark, and record the reasoning so a future reader (or future us) can sanity-check the call.

Once a winner is chosen and ordered, the next PR creates a sibling folder under `robots/` (e.g. `robots/mycobot-320-pi/`) with the URDF viewer scaffold, the same way [`robots/rebot-arm-b601-dm/`](../rebot-arm-b601-dm/) was set up. This folder stays as the decision record.

## The task we are sizing for

`place-items-on-shelf` is a tabletop pick-and-place: grasp a small consumer item (~6 cm cube, ~100 g) off a flat surface and place it on a shelf ~25 cm away and ~15 cm above the base. Concretely the arm must be able to:

| Need | Hard requirement |
|---|---|
| Reach | ≥ 300 mm radius (table corner → shelf face) |
| Payload | ≥ ~250 g (a soda can is ~350 g full; we will test with lighter cubes first) |
| DOF | 6 (need wrist orientation for top-down + side approaches into shelf) |
| Repeatability | ≤ ±1 mm (placement on a shelf, not surgery) |
| ROS 2 support | First-party URDF + MoveIt + Gazebo packages |
| Onboard compute | Nice-to-have; reduces tether to a host PC |

## Candidates (Elephant Robotics lineup, as of June 2026)

| Model | Reach | Payload | Repeatability | DOF | Onboard compute | First-party ROS 2 |
|---|---|---|---|---|---|---|
| mechArm 270 | 270 mm | 250 g | ±0.5 mm | 6 | none (host needed) | URDF + MoveIt (community) |
| myCobot 280 (M5 / Pi) | 280 mm | 250 g | ±0.5 mm | 6 | Pi variant only | yes — `mycobot_ros2` (URDF, MoveIt, Gazebo) |
| myCobot 320 (M5 / Pi) | 350 mm | 1 kg | ±1 mm | 6 | Pi variant only | yes — `mycobot_ros2` (URDF, MoveIt, Gazebo) |
| myCobot Pro 630 | 600 mm | 2 kg | ±0.5 mm | 6 | yes (industrial controller) | yes, but heavier integration |

(Specs from Elephant Robotics' product pages and Robots International's summary — see Sources at the bottom. Repeatability and reach figures are the manufacturer's published numbers; we have not independently measured.)

## Filtering against the requirements

- **mechArm 270.** Reach is 270 mm — *under* our 300 mm floor before we even add a gripper. Out.
- **myCobot 280 (Pi).** Same 280 mm reach; payload is only 250 g. It works in v1 sim but on real hardware the table-to-shelf path will be at the edge of its envelope. Already explored in [the previous `v3_mycobot_pi` work on `robotics-research-pick-hardware`](https://github.com/RobinNagpal/place-items-on-shelf/tree/robotics-research-pick-hardware/v3_mycobot_pi) — kept as a fallback, not the primary pick.
- **myCobot 320 Pi.** 350 mm reach, 1 kg payload, ±1 mm repeatability, onboard Raspberry Pi, same `mycobot_ros2` ROS 2 stack as the 280. Comfortably clears every requirement with headroom.
- **myCobot Pro 630.** Massive overkill for a 6 cm cube. ~2× the price, larger footprint than our tabletop, and the integration is closer to an industrial cobot than a desktop arm. Out unless we change the benchmark.

## Recommendation

**myCobot 320 Pi.**

Why:

1. **Reach with margin.** 350 mm vs. our 300 mm floor — comfortable, and it leaves room to add a gripper without losing the shelf-top approach.
2. **Payload with margin.** 1 kg vs. our ~250 g working target — we are not running close to the limit, so torque is not a noise source.
3. **Same software stack as the 280.** [`mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) supports the 320 with first-party URDF, MoveIt, and Gazebo packages. The simulation work already done for v3 (`mycobot_280pi`) translates directly — only link lengths change.
4. **Onboard Raspberry Pi.** Cuts the tether to a host PC, which matches how `rebot-arm-b601-dm` and v3 are already structured (the arm runs ROS 2 on its own compute).
5. **Repeatability is fine for the task.** ±1 mm on shelf placement is well inside any reasonable success criterion.

## What's NOT in this PR (intentionally)

- No URDF, no launch files, no `colcon` package — that comes in the **next** PR once this recommendation is accepted and we order the arm. The scaffold will follow the [`robots/rebot-arm-b601-dm/`](../rebot-arm-b601-dm/) layout (`launch/`, `rviz/`, `docs/`, `src/` submodule pointing at `mycobot_ros2`).
- No price comparison or purchase decision — that lives outside the repo.
- No benchmark numbers — manufacturer specs only. We measure on real hardware after delivery.

## Verifying this PR

This is a docs-only change. There is no build, lint, or test to run.

```bash
# Sanity check that the file is readable markdown and rendered links resolve.
ls robots/elephant-robotics-best-option/README.md
```

## Sources

- [Elephant Robotics product line summary — Robots International](https://www.robotsinternational.com/Elephant-Robotics.htm)
- [myCobot Pro 630 product page](https://shop.elephantrobotics.com/collections/mycobot-pro-630)
- [myCobot 320 Pi product page](https://www.elephantrobotics.com/en/mycobot-320-pi-en/)
- [myCobot 280 Pi product page](https://qviro.com/product/elephant-robotics/mycobot-280-pi/specifications)
- [mechArm 270 product page](https://shop.elephantrobotics.com/collections/mecharm)
- [Elephant Robotics expands lightweight arm product line — IEEE Spectrum](https://spectrum.ieee.org/elephant-robotics-lightweight-robot-arms)
- [`elephantrobotics/mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) — first-party ROS 2 packages for the myCobot family
