# Architecture — 01 Custom Gazebo world

## Folder tree

```
01-custom-gazebo-world/
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_NOTES.md
├── robot-arm-urdf-primer.md
└── worlds/
    └── autosampler_cell.sdf
```

## File responsibilities

- **`worlds/autosampler_cell.sdf`** — the only thing software reads.
  Describes the bench, the rack, the alignment plate + tray, three
  vials, and an `<include>` reference to the myCobot 280 model.
  Everything later exercises spawn into the scene (camera, MoveIt
  collision objects, additional vials) gets added on top of this file
  or copied and extended from it.
- **`robot-arm-urdf-primer.md`** — explains the `.urdf.xacro` file
  extension and walks through the two upstream xacro files that
  actually define the arm the SDF includes. Read this before opening
  the arm's URDF for the first time.
- **`README.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_NOTES.md`** —
  for human readers only. No build step depends on them.

## Dependencies

```
worlds/autosampler_cell.sdf
  ├── model://sun           (Gazebo built-in)
  ├── model://ground_plane  (Gazebo built-in)
  └── model://mycobot_280   (upstream automaticaddison/mycobot_ros2,
                             resolved via GAZEBO_MODEL_PATH or
                             GZ_SIM_RESOURCE_PATH)
```

The rack, the alignment plate, the tray, and the vials are defined
inline so the file is self-contained for everything except the arm.
