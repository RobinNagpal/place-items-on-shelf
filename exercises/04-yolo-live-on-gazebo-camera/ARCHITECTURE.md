# Architecture — 04 YOLO live on a Gazebo camera

## Folder tree

```
04-yolo-live-on-gazebo-camera/
├── README.md
├── ARCHITECTURE.md            # this file
├── IMPLEMENTATION_NOTES.md
├── worlds/
│   └── autosampler_cell_with_camera.sdf
└── yolo_live_demo/             # the ROS 2 ament_python package
    ├── package.xml
    ├── setup.py
    ├── setup.cfg
    ├── resource/yolo_live_demo
    ├── yolo_live_demo/
    │   ├── __init__.py
    │   └── live_detector_node.py
    ├── launch/
    │   └── yolo_live.launch.py
    └── config/
        └── yolo_live.rviz
```

## Per-file responsibility

| File | Owns |
|---|---|
| [`worlds/autosampler_cell_with_camera.sdf`](worlds/autosampler_cell_with_camera.sdf) | Exercise 1's world **plus** an `<overhead_camera>` model with a `<sensor type="camera">` and the `gz-sim-sensors-system` plugin. The camera frame is published on the Gazebo Transport topic `/overhead_camera/image_raw` at 30 Hz, 640×480 RGB. |
| [`yolo_live_demo/yolo_live_demo/live_detector_node.py`](yolo_live_demo/yolo_live_demo/live_detector_node.py) | The whole node. Loads the `.pt` once, subscribes to the image topic, runs `model.predict()` per frame, publishes `vision_msgs/Detection2DArray` and an annotated `sensor_msgs/Image`. |
| [`yolo_live_demo/launch/yolo_live.launch.py`](yolo_live_demo/launch/yolo_live.launch.py) | One-shot launcher. Starts (1) Gazebo Sim on the world, (2) `ros_gz_image image_bridge`, (3) the YOLO node with its parameters, (4) RViz with a saved layout. |
| [`yolo_live_demo/config/yolo_live.rviz`](yolo_live_demo/config/yolo_live.rviz) | RViz layout with two image panels (raw + annotated). Saved separately so you can edit / overwrite it without touching code. |
| [`yolo_live_demo/setup.py`](yolo_live_demo/setup.py) | ament_python install: declares the `live_detector` console script and ships the launch / config files to `share/yolo_live_demo/`. |
| [`yolo_live_demo/package.xml`](yolo_live_demo/package.xml) | ROS package manifest. `exec_depend`s on `rclpy`, `sensor_msgs`, `vision_msgs`, `cv_bridge`, `ros_gz_image`. Ultralytics is a Python (`pip`) dep, not a ROS one. |

## Data flow at runtime

```
gz sim worlds/autosampler_cell_with_camera.sdf
         │
         │  /overhead_camera/image_raw       (Gazebo Transport)
         ▼
ros_gz_image image_bridge
         │
         │  /overhead_camera/image_raw       (sensor_msgs/Image on ROS 2)
         ▼
yolo_live_detector node
   _on_image(msg):
     frame      = cv_bridge.imgmsg_to_cv2(msg)
     results    = model.predict(frame)
     det_array  = _build_detections_msg(results[0], msg.header)
     ann_image  = cv_bridge.cv2_to_imgmsg(results[0].plot())
         │
         ├── /yolo/detections                (vision_msgs/Detection2DArray)
         └── /yolo/image_annotated           (sensor_msgs/Image)
                                                       │
                                                       ▼
                                                     RViz (overlay panel)
```

Three processes participate, but the **only piece of state that
crosses process boundaries is a ROS topic**. Gazebo does not import
ultralytics; the YOLO node does not link against Gazebo. That is
the property that lets you swap the simulated camera for a real
Pi-cam later with no code change.

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/overhead_camera/image_raw` | `sensor_msgs/Image` | Gazebo → bridge → node | 640×480 BGR camera frames at ~30 Hz |
| `/yolo/detections` | `vision_msgs/Detection2DArray` | node → anyone | Per-frame list of pixel boxes with class id + confidence |
| `/yolo/image_annotated` | `sensor_msgs/Image` | node → RViz | The same frame with bounding boxes drawn on top |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | bridge → all | Camera link frame (used by RViz to anchor the image panel) |

## Why we split `worlds/` from the package

The world is **data**, not Python code. Keeping it in
`exercises/04-.../worlds/` rather than inside the package makes:

- Browsing the SDF on GitHub more obvious.
- Reusing the same SDF in later exercises straightforward (item 5
  needs the same overhead view to score detections).
- The package installation footprint smaller.

The launch file resolves the world path relative to the package
share dir first, then falls back to the source-tree path so an
ad-hoc `colcon build` from a worktree still works.

## What this exercise does NOT touch

| Subsystem            | Where it lives                                  |
|----------------------|-------------------------------------------------|
| Training the model   | exercise 3 (`03-tiny-yolo/`)                    |
| Scoring vs ground truth | exercise 5 (planned)                         |
| MoveIt motion        | exercises 18–22                                 |
| Quantising the model | exercise 6 (planned)                            |

This is **inference plumbing only**: camera → model → ROS topic.
