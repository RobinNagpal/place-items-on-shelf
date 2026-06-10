# Type 4 — 6-DoF object poses (per-frame, per-object)

## What it is

A small file that says, for every named object in the scene at
every frame, **exactly where it is in the world** — written as
six numbers:

```
(x, y, z, roll, pitch, yaw)
```

`x, y, z` are metres. `roll, pitch, yaw` are radians. "6 DoF"
just means six degrees of freedom — three for position, three
for orientation. Together they pin the object's full pose.

Gazebo already knows these numbers because the simulator
*sets* them. You only have to record them.

## When it is useful

Two distinct uses:

1. **Ground truth for scoring perception.** Once you know the
   true (x, y, z) of every vial, you can ask any perception
   model "what did you predict?" and compute the error
   automatically — no human labelling. This is what
   [`exercises/05-score-detections-vs-gazebo/`](../../../../exercises/05-score-detections-vs-gazebo/)
   already does for 2D boxes; the same idea extends to 6-DoF.
2. **Direct label for an ArUco / AprilTag pipeline.** Stick a
   marker on a rack corner; the marker's true world pose is
   the ground truth your detector must recover.

## Who uses it

**Mostly not an ML model** — this is a *reference signal* the
rest of the system measures itself against.

| Consumer | What it does with the pose |
|---|---|
| **Scorer for type 1 / 2** (boxes / masks) | Project the true pose into pixels, compare with the predicted box / mask, compute IoU. |
| **Scorer for type 3** (depth) | Project the true (x, y, z) and check how far the depth-derived 3D point is from it. |
| **ArUco pipeline** | The expected output of `cv2.solvePnP` is the marker's pose. The simulator's logged pose tells you whether the OpenCV code recovered it correctly. |
| **Trajectory generator** | The pick-and-place script needs to know the rack and tray pose to choose targets. In sim it can read the truth directly; the same code on hardware reads the perception output instead. |

If anyone wants to **train a pose-estimation network** (DOPE,
FoundationPose, PoseCNN), the same per-object 6-DoF log is the
supervised target. But for this cell that's optional — ArUco +
fixture geometry covers it.

## How to produce it in Gazebo

The simulator already publishes this stream. You just bridge it
to ROS 2 and write it to disk.

### 1. Find the topic

Gazebo publishes object poses on its native transport at
`/world/<world_name>/pose/info`. The message type is
`gz.msgs.Pose_V` (a vector of poses, one per model).

For the world `autosampler_cell`, the topic is
`/world/autosampler_cell/pose/info`.

### 2. Bridge it to ROS 2

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /world/autosampler_cell/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V \
    --ros-args -r /world/autosampler_cell/pose/info:=/gazebo/pose_info
```

Now `/gazebo/pose_info` carries a `tf2_msgs/TFMessage` where
each `TransformStamped` has:

- `child_frame_id` — the SDF model name (e.g. `vial_b1_r1`).
- `transform.translation.x / y / z` — metres, world frame.
- `transform.rotation.x / y / z / w` — quaternion (you can
  convert to roll / pitch / yaw with `tf_transformations`).

### 3. Record to disk

The cheapest path is a tiny rosbag2 of the topic during your
sim run:

```bash
ros2 bag record /gazebo/pose_info -o synthetic_<step>/poses.bag
```

For a per-frame `.json` (matching the image filenames) write a
short subscriber:

```python
# pseudo-code
import json, rclpy
from tf2_msgs.msg import TFMessage

def cb(msg):
    out = {}
    for t in msg.transforms:
        out[t.child_frame_id] = {
            "x": t.transform.translation.x,
            "y": t.transform.translation.y,
            "z": t.transform.translation.z,
            "qx": t.transform.rotation.x,
            "qy": t.transform.rotation.y,
            "qz": t.transform.rotation.z,
            "qw": t.transform.rotation.w,
        }
    json.dump(out, open(f"poses_{frame_idx}.json", "w"))
```

One file per camera frame, indexed by frame number.

## What you end up with

```
synthetic_<step>/
└── labels/
    └── poses_<N>.json   # {"beaker_1": {"x":0.05, "y":-0.30, "z":0.900, "qx":0, ...}, ...}
```

Or, if you prefer one tidy table for the whole run, a long
CSV with columns
`frame, object_name, x, y, z, qx, qy, qz, qw`.

## Why this is the most important "non-trainable" type

Almost every per-step decision in the cell ultimately needs to
know **where things are**. Even simple HSV cap-colour detection
needs to map "I found red pixels at (320, 240)" to "the red cap
is at slot (3, 7)" — and that map goes through the rack's
ground-truth pose. So although no model trains on this, every
model **needs** it. It's the connective tissue of the dataset.

## Existing project reference

The same topic is what
[`exercises/05-score-detections-vs-gazebo/`](../../../../exercises/05-score-detections-vs-gazebo/)
subscribes to for ground-truth pose. Nothing changes for the
ketchup case — the topic name follows the world name, and the
recording is the same one-liner.
