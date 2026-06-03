# 01 — Gazebo: The Physics Sandbox

## What is Gazebo, in one sentence?

**Gazebo is a 3D world simulator with physics.** It creates a virtual place where a
virtual robot lives — gravity pulls things down, objects bump into each other, motors
on the robot have realistic torque limits, and cameras see what a real camera would see.

Think of it like a video game engine, but built specifically so engineers can test robots
without paying for hardware and without breaking it when something goes wrong.

## Why we need a simulator

When you're learning robotics, you ideally want to:

- Test code without crashing a real arm into a wall.
- Try out designs that don't physically exist yet.
- Run the same scene a hundred times the same way to compare results.
- Skip the cost of buying a real robot until you know what you're doing.

A simulator gives you all of that. Gazebo is the most common open-source one in the
ROS 2 ecosystem.

## What's actually inside Gazebo when you run it

Three categories of "stuff":

1. **A world** — a `.world` file (XML). It describes the floor (a ground plane), maybe a
   table, maybe some objects sitting on the table, the sun, the sky. Think of it as the
   "stage" for your scene.
2. **Models** — individual objects, each in their own `.sdf` file. Robots are models.
   Tables, boxes, cans, cylinders — all models. Each model has shape, weight, friction,
   and (for robots) joints that can rotate.
3. **Plugins** — code modules that add behavior. The physics plugin makes gravity work.
   The sensors plugin makes cameras render images. The "user commands" plugin lets you
   click in the GUI to drag things around.

## What you see when you launch *just* Gazebo

Run the launch command and you get a single GUI window that looks a bit like a game:

- A floor.
- A table (we added this — the original demo was missing it).
- Five small objects on the table: a red cylinder, a mustard bottle, a cheezit box, a
  cardboard box, a coke can. These are real product models scanned from the YCB object
  set, which is a standard for robotics research.
- The myCobot 280 robot arm, standing on or near the table.
- A second object that looks like a black tripod with a small camera on top — that's
  a **standalone RGBD camera** (color + depth) mounted independently of the arm,
  looking down at the table.

You can rotate the view with the mouse, zoom, click on an object to inspect it. **But
you cannot make the arm move yet** — Gazebo by itself only knows about physics and
shapes. It doesn't know "how" or "why" to move the arm.

## What Gazebo *does* publish, even by itself

Once Gazebo is running, it shares information with the rest of the ROS 2 system via
**topics** (think: channels). Some of the key ones for us:

- **`/joint_states`** — the current angle of every joint on the arm, updated ~30 times
  per second. This is how the rest of the system knows where the arm currently is.
- **`/camera_head/color/image_raw`** — the RGB camera image, like a webcam feed.
- **`/camera_head/depth/color/points`** — a 3D point cloud of what the camera sees
  (each pixel turned into an x/y/z coordinate). This is what the depth sensor gives us.
- **`/clock`** — the simulated time. We use this so all the other programs agree on
  "now" even if the simulation runs faster or slower than real time.

## The terminal command (Step 1 in your sequence)

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
  world_file:=pick_and_place_demo.world \
  use_camera:=true \
  use_rviz:=false
```

The launch arguments mean:

- `world_file:=pick_and_place_demo.world` — load the world with the table and objects.
- `use_camera:=true` — turn on the standalone overhead camera that the perception
  pipeline needs.
- `use_rviz:=false` — don't auto-open RViz; we'll talk about RViz separately in the
  next doc.

## What success looks like

You should see in the terminal:

- `Loaded arm_controller` and `Loaded joint_state_broadcaster` lines.
- No crash, no `[ERROR]` red lines.
- A Gazebo window opens showing the scene described above.

If you don't see the table, the rebuild for `mycobot_gazebo` didn't pick up the table
edit. If you don't see the camera tripod, `use_camera` got dropped. If you see neither,
you launched a different world by accident.

## What's still missing

At this point you can *look* at the robot but not control it. There's no path-planning,
no perception, no execution. That's what the next three components add.

→ Next: [02-rviz.md](02-rviz.md)
