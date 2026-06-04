# Architecture — 01 Custom Gazebo world

## Folder tree

```
01-custom-gazebo-world/
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_NOTES.md
└── worlds/
    └── pick_place_world.sdf
```

One code file, three docs. That's the whole exercise.

## File responsibilities

### `worlds/pick_place_world.sdf`

The world description. Everything the simulator needs to render the scene
lives in this one file.

- **Why it exists:** Gazebo is a *general* simulator. It does not know
  what we want to simulate until we hand it an SDF file. This file is our
  "what to simulate".
- **What it owns:** the lighting (sun), the floor (ground_plane), the
  table model (defined inline), the three cube models (defined inline),
  and an `<include>` reference to the myCobot 280 model.
- **What depends on it:** every later exercise that needs a scene — the
  perception items, the motion items, and the full pick-and-place demo.
  None of those import this file as code; they either load it the same
  way (`gazebo <path>`) or copy and extend it.

### `README.md`

The "what is this?" doc. Aimed at a reader who has never written or read
an SDF file before. Concept-level only.

### `ARCHITECTURE.md`

This file. Lists what each file in the folder is for and how they relate.

### `IMPLEMENTATION_NOTES.md`

The "why did we build it this way?" doc. Engineering trade-offs and
known limitations.

## How the files interact

Only the SDF file is consumed by software. The three docs are consumed
by humans. There is no build step, no compile step, no scripts to run.

```
human reader  --(reads)--> README.md, ARCHITECTURE.md, IMPLEMENTATION_NOTES.md
gazebo binary --(reads)--> worlds/pick_place_world.sdf
```

## Dependency relationships

```
worlds/pick_place_world.sdf
  ├── depends on: model://sun           (Gazebo's built-in model database)
  ├── depends on: model://ground_plane  (Gazebo's built-in model database)
  └── depends on: model://mycobot_280   (resolved via GAZEBO_MODEL_PATH
                                         or GZ_SIM_RESOURCE_PATH)
```

If the `mycobot_280` model is not on the search path, Gazebo will print a
warning and load everything else. The world still opens; the arm is just
missing.

## Important SDF elements

ROS-style "nodes / topics / services" do not apply here — the file is
pure description. The SDF elements that matter most:

| Element | Role |
|---|---|
| `<world>` | the top-level container; one per file |
| `<include><uri>...</uri></include>` | pull in a model from a model database |
| `<model>` | define a model inline (the table and the cubes) |
| `<static>` | when true, physics ignores the model — it cannot move |
| `<pose>` | starting position and orientation, six numbers `x y z roll pitch yaw` |
| `<collision>` | the shape physics uses for contact and dragging |
| `<visual>` | the shape rendering uses (often the same as the collision) |
| `<inertial>` | mass and inertia — needed for dynamic models like the cubes |

The visual / collision split exists so you can have a low-detail collision
mesh and a high-detail visual mesh for performance. For our cubes both
are the same.
