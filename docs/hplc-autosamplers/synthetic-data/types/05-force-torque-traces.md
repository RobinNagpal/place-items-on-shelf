# Type 5 — Force / torque time-series

## What it is

A small CSV (or rosbag) file where each row is one timestep and
the columns are the six readings from a virtual **six-axis
force / torque (F/T) sensor**:

```
t,  Fx, Fy, Fz,  Tx, Ty, Tz
0.000, 0.01, 0.00, -0.02, 0.000, 0.000, 0.000
0.001, 0.01, 0.00, -0.02, 0.000, 0.000, 0.000
...
0.412, 0.05, 0.00,  1.04, 0.020, 0.010, 0.000   ← here the cap touched the tray
```

`Fx, Fy, Fz` are forces in newtons. `Tx, Ty, Tz` are torques in
newton-metres. The sensor sits between the arm's last link and
the gripper, so the readings describe **what the tool tip is
feeling**.

This is the robot's sense of **touch**. The camera goes blind
the moment two objects make contact; the F/T sensor wakes up.

## When it is useful

The cell has a small number of distinct contact moments. F/T
catches every one of them:

- **"Did the vial bottom touch the tray slot?"** — Fz jumps
  from near-zero to ~1 N. Stop the descent.
- **"Did the gripper close on a vial, or on air?"** — A
  short Fxy / Tz spike when the fingers meet the glass; flat
  trace if there's nothing there.
- **"Is the cap screwed to the right torque?"** — Tz ramps
  smoothly and plateaus.
- **"Did the arm crash into the source rack?"** — Big spikes
  across all six channels. Trigger an e-stop.

## Who uses it

Two consumers, **mostly not a neural network**.

### a) Threshold rules (the default — no ML)

Most uses are one if-statement:

```python
while not done:
    move_down(0.001)            # 1 mm per loop
    if abs(ft.fz) > 1.0:        # 1 N threshold
        stop()
        break
```

This is the same idea as a real F/T-protected insertion. No
model. The synthetic trace is used to **pick the right
threshold** (1.0 N for a vial-into-slot, 0.4 N·m for a screw
cap) and to verify the trigger doesn't fire on normal motion
jitter.

### b) Small temporal classifier (when thresholds aren't enough)

For events that share a magnitude but differ in *shape* — e.g.
"smooth ramp to plateau" (good cap-on) vs "oscillating ramp"
(cross-threading) — a tiny model is justified:

- **1D-CNN** with 1-2 conv layers, ~10 k parameters.
- **Small LSTM / GRU** with ~5 k parameters.
- **TSAI / sktime** tree-based classifiers — often beat tiny
  neural nets on short F/T windows.

Input: a 1-2 s window of `(Fx, Fy, Fz, Tx, Ty, Tz)`.
Output: a class id (`good`, `cross_thread`, `missed`).

## How to produce it in Gazebo

Two short steps.

### 1. Add an F/T sensor to the URDF (or SDF)

A six-axis sensor lives in a joint between two links. Add it
between the wrist (`tool0` or equivalent) and a small "gripper
mount" link:

```xml
<joint name="ft_joint" type="fixed">
  <parent link="tool0"/>
  <child  link="gripper_mount"/>
  <origin xyz="0 0 0" rpy="0 0 0"/>
</joint>

<gazebo reference="ft_joint">
  <provideFeedback>true</provideFeedback>
  <sensor name="wrist_ft" type="force_torque">
    <update_rate>1000</update_rate>      <!-- 1 kHz — match real hardware -->
    <topic>/wrist_ft</topic>
  </sensor>
</gazebo>
```

`provideFeedback` is the magic bit — without it, Gazebo
computes the contact but does not expose it on a topic.

### 2. Bridge to ROS 2 and record

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /wrist_ft@geometry_msgs/msg/WrenchStamped[gz.msgs.Wrench
ros2 bag record /wrist_ft -o synthetic_<step>/ft.bag
```

Convert to CSV after the run with a one-liner — `rosbag2` ships
a CSV exporter.

### 3. Drive the contact events from a script

The trace is only interesting if **the contact actually
happens**. Run a scripted trajectory in sim that produces the
event you want to capture:

| Event you want a trace of | Scripted motion in sim |
|---|---|
| Vial-bottom touches tray slot | Slow vertical descent of the gripper holding a vial until the contact engine fires |
| Empty-gripper close | Close the gripper at a pose with no object between the fingers |
| Vial-grasp close | Same, but with the vial centred between the fingers |
| Cap-on torque (if you re-enable Step 6) | Place a cap on a vial neck, rotate the wrist around z until torque rises |

The point is to **trigger the contact in sim** so the F/T
plugin produces a real (simulated) trace, not a hand-faked one.

## What you end up with

```
synthetic_<step>/
└── traces/
    ├── ft_<event_name>_<traj_idx>.csv     # 1 kHz, 6 columns
    └── joints_<traj_idx>.csv              # ride-along, see type 8
```

For each labelled event keep ~100 traces per class — enough for
both threshold tuning and a small temporal classifier.

## What the simulator gets wrong (so you don't over-trust it)

Gazebo's contact engine is rigid-body and approximate. Two
known limitations to keep in mind when training on this data:

- **No micro-stiction.** Real-world threading wobbles. Sim
  threading is too clean. For a Step 6 cap-screw trace, this
  matters; for the simpler "did the cap touch the tray" check
  it does not.
- **Contact-stiffness is a single number.** Real plastic vials
  and aluminium trays have different stiffnesses; in sim they
  share the engine's constant. So absolute force values are
  approximate — train classifiers on **shape and direction**,
  not on exact newton-thresholds.

## Existing project reference

The repo's [`docs/learning-checklist.md`](../../../learning-checklist.md)
item 15 ("Wrist F/T sensor — detect surface contact") is the
target consumer. The exercise is not implemented yet, but when
it is, this trace dataset is the input.
