# 04 — Run YOLO live on a Gazebo camera feed

Implements checklist item **4** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

This is the first time YOLO from
[`../03-tiny-yolo/`](../03-tiny-yolo/) stops being "a Python script
on a folder of images" and becomes a **live ROS 2 node that detects
vials on every camera frame from Gazebo**.

## The 30-second version

Three boxes, three arrows:

```
   Gazebo Sim                 ROS 2                 RViz
  (renders frames)        (detector node)        (shows it)
        │                        │
        │  /overhead_camera      │
        │     /image_raw         │
        ├──── sensor_msgs ──────►│
        │       /Image           │  YOLO model.predict(frame)
        │                        │
        │                        ├──► /yolo/detections
        │                        │     vision_msgs/Detection2DArray
        │                        │
        │                        └──► /yolo/image_annotated
        │                              sensor_msgs/Image (with boxes drawn)
        └──── camera plugin ─────┘                       │
                                                         ▼
                                                  picked up by RViz
                                                  next to the raw feed
```

That's the whole exercise. Everything below explains one box or one
arrow in more detail.

## The questions a beginner usually asks

### 1. How does the `.pt` file actually work inside Gazebo + ROS?

**Gazebo never sees the `.pt`.** Gazebo only knows about its 3D
scene and its built-in sensors. When the simulator renders a camera
frame, it publishes the pixels on a Gazebo Transport topic — that
is it.

Our **ROS 2 Python node** is the part that knows about YOLO:

1. On startup it loads `best.pt` with one line:
   `model = YOLO("/abs/path/to/best.pt")`.
2. Every time a new `sensor_msgs/Image` arrives, it calls
   `model.predict(frame)` and gets a list of boxes back.
3. It packs those boxes into a `vision_msgs/Detection2DArray` and
   publishes them on `/yolo/detections`.

The simulator and the model **live in different processes** and
only talk through ROS topics. That decoupling is the whole point —
swap Gazebo for a real Pi-camera-publishing node, and the YOLO node
keeps working unchanged.

### 2. How does the camera actually publish images?

Two short hops:

1. **In the SDF world** we attach a `<sensor type="camera">` to a
   small static model parked 0.5 m above the bench. Gazebo's
   `gz-sim-sensors-system` plugin (declared at the bottom of
   [`worlds/autosampler_cell_with_camera.sdf`](worlds/autosampler_cell_with_camera.sdf))
   renders that camera 30 times a second and pushes each frame onto
   the Gazebo Transport topic `/overhead_camera/image_raw`.
2. **`ros_gz_image`** is a tiny bridge program that subscribes to
   that Gazebo Transport topic and re-publishes the SAME frames as
   `sensor_msgs/Image` on the **same name** on the ROS 2 side. From
   then on every ROS 2 node — including ours — treats the camera
   like any normal ROS camera.

So the data path is:

```
Gazebo Sim ─► gz topic ─► ros_gz_image bridge ─► ROS 2 topic ─► YOLO node
```

### 3. Then we run the model on those images — how?

The detector node
([`yolo_live_demo/yolo_live_demo/live_detector_node.py`](yolo_live_demo/yolo_live_demo/live_detector_node.py))
subscribes to the ROS 2 image topic. On every message:

1. **`cv_bridge`** converts the `sensor_msgs/Image` into a numpy
   array (the same shape OpenCV uses).
2. **`model.predict(frame)`** runs YOLOv8 on that array. Same call
   as in exercise 3's `validate.py`, just on one image at a time.
3. The result has a list of boxes, each with class id, confidence,
   and pixel coordinates.
4. We pack those into a ROS message (see next question) and
   publish.

The model is loaded **once** during `__init__`; we do NOT reload it
on every frame. Loading `.pt` is the slow part.

### 4. In what format does ROS get the results so it knows the position?

The ROS 2 standard for this is **`vision_msgs/Detection2DArray`**
(installed by the `vision_msgs` package). It is a list of
`Detection2D` entries. Each entry has:

| Field                | What it carries                                  |
|----------------------|--------------------------------------------------|
| `bbox.center.x`      | x of the box centre, in **pixels**               |
| `bbox.center.y`      | y of the box centre, in **pixels**               |
| `bbox.size_x`        | box width in pixels                              |
| `bbox.size_y`        | box height in pixels                             |
| `results[0].hypothesis.class_id` | string class name (e.g. `"vial"`)     |
| `results[0].hypothesis.score`    | 0.0 – 1.0 confidence                  |

The whole array also carries a `header` with the timestamp and the
camera's TF frame, so any later node can ask: *"this detection — in
which frame of reference, at what time?"*. We just copy those from
the incoming image header — that keeps the detection synced with
the frame that produced it.

You can watch the detections live with:

```bash
ros2 topic echo /yolo/detections
```

### 5. Does YOLO give exact 3D location?

**No.** YOLO gives **pixel coordinates only — 2D, not 3D.**

A detection like *"vial at pixel (240, 318), 90 px tall"* does not
tell the arm where the vial is in the world. To get from that
2D pixel box to a real `(X, Y, Z)` in the arm's frame, you need:

| Need                        | Which exercise solves it           |
|-----------------------------|------------------------------------|
| A depth value per pixel     | item 8 (depth point cloud)         |
| Correct lens distortion     | item 11 (intrinsics calibration)   |
| Camera → arm frame transform | item 12 (hand-eye calibration)    |

**For this exercise that is fine** — closed-loop perception lives
in 2D first. Item 4 is "can the robot *see* a vial in real time?".
"Can it *reach* the vial it sees?" is later.

## Workflow at a glance

```
Gazebo Sim with autosampler_cell_with_camera.sdf
            │
            │  /overhead_camera/image_raw  (Gazebo Transport)
            ▼
       ros_gz_image bridge
            │
            │  /overhead_camera/image_raw  (sensor_msgs/Image, now ROS 2)
            ▼
   yolo_live_detector node
            │  cv_bridge -> numpy
            │  model.predict(frame)
            │  pack pixel boxes into Detection2D
            │
            ├─►  /yolo/detections           (vision_msgs/Detection2DArray)
            │
            └─►  /yolo/image_annotated      (sensor_msgs/Image w/ boxes drawn)
                                              │
                                              ▼
                                            RViz
```

## What "Done when" means here

The checklist says: *"The detection box tracks an object as you drag
it in Gazebo's GUI."*

Concretely:

- Drag a vial in the Gazebo GUI with the mouse.
- The same vial's bounding box in the RViz "YOLO overlay" view
  moves with it, every frame.
- `ros2 topic hz /yolo/detections` shows roughly the camera's
  frame rate (we set 30 Hz; on a CPU you might see 5–10 Hz once
  YOLO is in the loop).

## Run it (single terminal, single launch file)

You need a trained `.pt`. Use the one from exercise 3 once you have
real data, or any pretrained YOLOv8 file as a stand-in:

```bash
# 1. Install the Python deps (one time):
pip install ultralytics

# 2. Build the package:
cd ~/ros2_ws/src
ln -s /abs/path/to/exercises/04-yolo-live-on-gazebo-camera/yolo_live_demo .
cd ~/ros2_ws
colcon build --packages-select yolo_live_demo
source install/setup.bash

# 3. Launch everything:
ros2 launch yolo_live_demo yolo_live.launch.py \
    weights:=/abs/path/to/best.pt
```

The launch file starts: **Gazebo Sim** → **ros_gz_image bridge** →
**YOLO detector node** → **RViz**. RViz opens with two image
panels: the raw camera and the annotated overlay.

### Sanity-check commands

```bash
ros2 topic list                                   # both /overhead_camera and /yolo topics show
ros2 topic hz /overhead_camera/image_raw          # ~30 Hz
ros2 topic hz /yolo/detections                    # 5-30 Hz (depends on CPU/GPU)
ros2 topic echo /yolo/detections --field detections[0].results[0].hypothesis.class_id
```

## What this exercise is **not**

| What people sometimes expect | Where it actually lives             |
|------------------------------|-------------------------------------|
| 3D world coordinates for each vial | items 8 / 11 / 12 (depth + calibration) |
| Score per frame vs ground truth    | item 5 (auto-score from Gazebo)    |
| Faster / quantised inference       | item 6 (INT8 export)               |
| Reading the barcode                | item 14                            |

This exercise stops at *"the camera frame turns into a list of pixel
boxes on a ROS topic, in real time."* That is the foundation every
later perception item builds on.

## What's next

- **Item 5** — score `/yolo/detections` against the ground-truth
  poses Gazebo already publishes on its model-state topic, so we
  get an mAP per second with no manual labelling.
- **Item 8** — add an RGB-D camera and turn pixel boxes into 3D
  centroids.
