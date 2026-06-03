# 01-b — Build the Virtual Cell

You have a simulator running. Now you put **your robot, your table,
and a few objects** inside it. The goal is to create a virtual version
of the workspace your real cell will eventually have.

You do this once. After this step, everything you build runs against
this scene — motion planning, perception, the task code, and (later)
the policy you might train.

## What you need before this step

- A working simulator from [01-a](01-a-choose-and-install-simulator.md).
- The **URDF / xacro file** for your arm. Most arm vendors ship one in
  their ROS 2 package (`ur_description`, `franka_description`,
  `mycobot_description`, `panda_moveit_config/`, etc.).
- A rough idea of:
  - **Where the arm mounts** — on a table corner? Centred? Hanging?
  - **The table dimensions.**
  - **The objects you'll pick** — even a placeholder cube works.
  - **Where the camera sits** — overhead? Wrist-mounted? Both?

## What "the virtual cell" actually contains

A minimum useful cell has six things:

1. **Ground / world frame.** A reference origin.
2. **A table mesh** at the real height and footprint.
3. **The arm**, mounted to the table at the real location.
4. **At least one object** to pick (a cube, a cylinder, a cup mesh).
5. **A camera**, mounted where your real camera will be.
6. **A bin / drop zone** if your task has one.

That's it. Resist adding a fancy environment now — every prop is one
more thing to debug.

## Step-by-step

### Step 1 — load the arm URDF in the simulator

Pull the description package into your ROS 2 workspace:

```
cd ~/ros2_ws/src
git clone <vendor-or-community-description-pkg>
cd ~/ros2_ws && colcon build --packages-select <pkg_name>
```

Confirm the URDF parses with `check_urdf` and view it in RViz with the
`joint_state_publisher_gui` for a sanity sliders test.

### Step 2 — write a Gazebo / Isaac world that includes the arm

For **Gazebo Harmonic**, write a `world.sdf` that:

- Sets the physics engine (DART or Bullet).
- Spawns the ground plane.
- Spawns the arm by referencing the URDF (via `<include>` or `xacro`).
- Adds the table, objects, and camera (each as a `<model>`).

For **Isaac Sim**, do the equivalent in USD via the GUI or a Python
build script. Save the result as a `.usd` scene.

For **MuJoCo**, write a `scene.xml` that includes the arm's MJCF (most
vendor URDFs convert with `mjpython -c "import mujoco; …"`).

### Step 3 — add the table

A box. Set its dimensions, mass, and friction. Place it so the arm's
`base_link` sits at the corner / centre / wherever it will be in real.

### Step 4 — add the objects

Start with **primitives** (boxes, cylinders). Use realistic mass and
friction values (a steel cube is 2.7 g/cm³; an empty plastic cup is
~30 g). Later you can swap to mesh imports.

### Step 5 — add the camera

A `camera` sensor in Gazebo (or `Camera` prim in Isaac, or `<camera>`
in MuJoCo XML). Match the **real** camera's resolution (e.g. 1280×720
RGB) and field of view (~ 60-90° for typical RealSense / Kinect).

Mount it at the planned real-world pose. If you're using a depth
camera, add the depth sensor variant.

### Step 6 — verify the tf tree

Launch the world. Open RViz 2. Add a `TF` display. Check that:

- `world` → `base_link` → `link_1` → … → `tool0` is intact.
- `camera_link` (or `optical_frame`) sits at the planned pose.
- The arm is upright, not exploded, not sunk through the table.

If `tf` is incomplete, the planner won't work later. Fix it now.

## How long this should take

For a vendor-supported arm in Gazebo: **half a day, first time.** It
shortens fast once you have a template scene. Don't get sucked into
making it pretty.

## Tools that save time

- **xacro** — parameterise the URDF (different gripper variants from
  one file).
- **ros_gz_sim_spawn_model.launch.py** — spawns a URDF into Gazebo
  cleanly.
- **`moveit_setup_assistant`** — generates the SRDF needed in
  [01-c](01-c-bring-up-moveit-in-sim.md). Run it now if you can.
- **Asset libraries** — Gazebo Fuel (`fuel.gazebosim.org`),
  Isaac Sim's NVIDIA assets, MuJoCo Menagerie. Don't model a coffee
  cup from scratch.
- **Blender → URDF / USD** — for custom object meshes; export to
  Collada (`.dae`) or USD.

## Output of this step

```
Arm URDF source:        <package or repo>
Table dims (m):         ___ × ___ × ___
Arm mount point:        corner / centre / edge (offset from table origin: ___ )
Objects in scene:       cube / cylinder / vendor mesh (list: ___ )
Camera type:            RGB / RGB-D / stereo (model in real: ___ )
Camera mount:           overhead at (x, y, z) / wrist-mounted
TF tree intact?:        yes / no — broken at: ___
World file path:        ___
Gazebo / Isaac version pinned: ___
```

## Common mistakes

1. **Wrong arm mounting pose in URDF.** A 90° rotation later means
   nothing reaches anywhere. Match the real plan now.
2. **Massless objects.** Default mass = 0 turns objects into
   collision-less ghosts. Always set realistic mass and inertia.
3. **No friction.** Default values for `mu1`/`mu2` lead to slipping
   even on grippable shapes. Tune `0.5–1.0` for graspable objects.
4. **Cluttered scene from day one.** Build the minimum: table, arm,
   one object, one camera. Add clutter only when the basics work.
5. **Hard-coded camera resolution that doesn't match real.** When the
   real camera arrives at 1280×720, your sim-trained code expects
   640×480. Match early.
6. **Skipping the TF check.** Fix `tf` problems while they're small.

## What's next

The cell exists in sim. Now you give the arm a *brain* — MoveIt for
motion planning.

→ Next: [01-c-bring-up-moveit-in-sim.md](01-c-bring-up-moveit-in-sim.md)
