# v2 — backroom map

Second iteration of the place-items-on-shelf project. Unlike `v1_simple_pick/`,
which executes a hardcoded scripted sequence, v2 is being built up as a proper
implementation. The first step is the environment itself — a Gazebo Harmonic
world modelling the backroom/storeroom of a grocery store (not the customer-
facing shop floor).

## What this world represents

A small backroom where bulk overstock is kept on pallet racking. The robot
will start at a marked home position, drive to a shelf, retrieve a product,
return to a marked drop station near the door, and come back to home. This
file only defines the **environment**; the robot, sensing, planning, and
control are deliberately not part of this commit.

No products are placed on the shelves yet, and there are no obstacles in
the aisle.

## Room layout

Floor origin is at the centre of the room. X is right, Y is forward
(towards the back wall), Z is up.

```
 y = +4 ┌───────────────────────────────────────────┐
        │ ▓ rack_left  ▓  rack_center  ▓ rack_right ▓│  (north wall)
        │                                            │
        │                                            │
 x=-5   │                  (aisle)                   │  x=+5
        │                                            │
        │                                            │
        │  ◯ robot_home          ▣ drop_station      │
 y = -4 └─────────────────┐  door  ┌─────────────────┘
                          │ 1.8m  │
                       (south wall)
```

| Element                | Position (x, y, z) | Size (x × y × z) | Notes                              |
| ---------------------- | ------------------ | ---------------- | ---------------------------------- |
| Room (internal)        | centre 0, 0, 1.5   | 10.0 × 8.0 × 3.0 | Walls 0.2 m thick                  |
| Door opening           | x ∈ [-0.9, +0.9]   | 1.8 × — × 2.4    | South wall, ground to lintel       |
| Rack left              | -3.5, +3.2, 1.2    | 2.5 × 0.8 × 2.4  | 3 horizontal decks                 |
| Rack center            | 0.0, +3.2, 1.2     | 2.5 × 0.8 × 2.4  | 3 horizontal decks                 |
| Rack right             | +3.5, +3.2, 1.2    | 2.5 × 0.8 × 2.4  | 3 horizontal decks                 |
| Robot home marker      | -3.0, -3.0, 0      | 1.0 × 1.0 × —    | Yellow floor decal                 |
| Drop station           | +2.5, -3.0, 0.25   | 1.0 × 0.8 × 0.5  | Green-topped packing table         |

The three pallet racks each have four steel uprights at the corners
(0.08 × 0.08 m square posts) and three horizontal decks at z = 0.10, 1.10,
and 2.10 m — typical low / mid / top tiers for storing bulk product cases.

## Files

- `pos_v2_bringup/worlds/backroom.sdf` — the world definition.
- `pos_v2_bringup/launch/backroom.launch.py` — launches Gazebo Harmonic with
  the world (no robot spawned yet).
- `pos_v2_bringup/package.xml`, `CMakeLists.txt` — ROS 2 (ament_cmake)
  package metadata so `colcon build` installs the world and launch file
  into the workspace share directory.

## How to view it

After `colcon build` from the workspace root and sourcing the install:

```bash
ros2 launch pos_v2_bringup backroom.launch.py
```

## Next steps (not in this commit)

1. Add a `pos_v2_description/` package with the v2 robot URDF/xacro. We
   may start from v1's robot and improve it, but no code from v1 is being
   copied over yet.
2. Add a `pos_v2_task/` package with the planning/control nodes — closed
   loop, not the hardcoded sequence used in v1.
3. Populate the shelves with parameterised product models.
