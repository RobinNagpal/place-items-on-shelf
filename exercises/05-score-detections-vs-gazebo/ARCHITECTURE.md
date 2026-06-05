# Architecture — 05 Score detections vs Gazebo ground truth

## Folder tree

```
05-score-detections-vs-gazebo/
├── README.md
├── ARCHITECTURE.md          # this file
├── IMPLEMENTATION_NOTES.md
└── detection_scorer.py      # the only new code
```

We deliberately do **not** ship our own world, launch file, or
ament_python package. The whole point of exercise 5 is "one step
ahead of exercise 4" — reusing what is already there.

## Per-file responsibility

| File | Owns |
|---|---|
| [`detection_scorer.py`](detection_scorer.py) | The whole new node. Loads camera intrinsics + pose from constants at the top, subscribes to `/yolo/detections` (predictions) and `/gazebo/pose_info` (ground truth), projects each tracked model to a pixel box, computes IoU, and prints running TP / FP / FN / precision / recall / mean-IoU every second. |

## What we reuse from exercise 4

| From `04-yolo-live-on-gazebo-camera/`                           | Used here as                                |
|------------------------------------------------------------------|---------------------------------------------|
| `worlds/autosampler_cell_with_camera.sdf`                        | The same world. Camera position + intrinsics in `detection_scorer.py` were chosen to match its `<sensor>`. |
| `yolo_live_demo/launch/yolo_live.launch.py`                      | Started as-is in terminal 1 — the YOLO node and camera bridge stay up. |
| `/yolo/detections` (`vision_msgs/Detection2DArray`)              | Subscription input — the predictions. |
| (implicit) `ros_gz_bridge`                                       | Used in a second invocation to bridge Gazebo's pose topic — see README run instructions. |

The arrow at the centre of the data flow is:

```
exercise 4 -> /yolo/detections ─┐
                                ├─► detection_scorer
ros_gz_bridge -> /gazebo/pose_info ─┘
```

That is the whole architectural delta.

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/yolo/detections` | `vision_msgs/Detection2DArray` | exercise 4 → this node | Per-frame YOLO predictions in pixels |
| `/gazebo/pose_info` | `tf2_msgs/TFMessage` | `ros_gz_bridge` → this node | Per-tick world pose for every model. `child_frame_id` = the model's SDF name. |

`/yolo/detections` is the same topic exercise 4 already publishes —
this node is a pure consumer of it.

## Why no launch file

Three reasons:

1. **No new processes** beyond `detection_scorer.py` itself. Exercise
   4's launch already starts Gazebo, the image bridge, the YOLO node,
   and RViz. The pose bridge is one extra `ros2 run ros_gz_bridge`
   invocation — quicker to copy out of the README than to wrap.
2. **The scorer is "the lesson"** — wrapping it in a launch file would
   put boilerplate between the reader and the comparison logic.
3. **We do not need RViz** for scoring; the output is text in the
   terminal.

If you want a single-command runner later, the launch file from
exercise 4 plus two `Node` entries (the pose bridge + this script as
an executable) is the shape you would copy.
