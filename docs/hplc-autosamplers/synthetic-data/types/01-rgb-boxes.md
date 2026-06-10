# Type 1 — RGB images + 2D bounding boxes

## What it is

A picture from a virtual camera, plus a small text file listing
the rectangles around the objects in that picture. Each rectangle
is tagged with a class name like `beaker`, `vial`, or `centrifuge`.

The picture is a normal `.jpg`. The rectangles are stored in the
standard **YOLO format** — one line per object:

```
<class_id> <cx> <cy> <w> <h>
```

All four numbers are written as fractions of the image width and
height, so they stay the same even if you resize the picture.

## When it is useful

- "Is there a beaker on the bench right now?"
- "Where roughly is the source rack in the camera frame?"
- "Are any vials missing from this row of the tray?"

It answers **"is the thing there, and roughly where in pixels."**
It does **not** tell you the exact 3D position or the exact shape.

## Who uses it

A neural-network **object detector**. The default choice for this
project is **YOLOv8 (`yolov8n.pt`, the smallest variant)** because
the runtime fits on a Raspberry Pi next to the arm. Other
detectors with the same input format: YOLOv9, RT-DETR,
Detectron2's Faster R-CNN.

Training reads the `.jpg` + `.txt` pairs and learns to draw the
boxes by itself.

## How to produce it in Gazebo

Four small steps. None of them need physics — only the renderer.

### 1. Put a virtual camera in the world

Add a Gazebo camera sensor to the SDF, looking down at the
bench. The pose, focal length, and image size are all written in
the SDF — you control them:

```xml
<sensor name="overhead_rgb" type="camera">
  <pose>0 0 1.4 0 1.5708 0</pose>
  <camera>
    <horizontal_fov>1.05</horizontal_fov>
    <image>
      <width>1280</width>
      <height>720</height>
    </image>
  </camera>
  <update_rate>30</update_rate>
  <topic>/overhead/image</topic>
</sensor>
```

### 2. Stream the image into ROS 2

One line with `ros_gz_bridge`:

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /overhead/image@sensor_msgs/msg/Image[gz.msgs.Image
```

You now have a normal ROS 2 image topic you can save with
`image_saver` or read frame-by-frame in Python.

### 3. Get the ground-truth boxes for free

Gazebo already knows the true pose and the true bounding box of
every model in the scene. Read them off
`/world/<world_name>/pose/info` (see
[`04-6dof-object-poses.md`](04-6dof-object-poses.md) for the
bridge command). Then **project** each model's 3D bounding box
into the image with the same camera intrinsics from the SDF:

```python
# pseudo-code — 20 lines, OpenCV does the projection
import cv2, numpy as np

def world_box_to_pixel_box(model_pose, box_3d, K, R_cw, t_cw):
    corners_world = box_3d.corners(model_pose)               # 8 points
    corners_cam   = R_cw @ corners_world.T + t_cw[:, None]
    pixels, _     = cv2.projectPoints(corners_cam.T, ..., K, None)
    u_min, v_min  = pixels.min(axis=0).ravel()
    u_max, v_max  = pixels.max(axis=0).ravel()
    return u_min, v_min, u_max, v_max
```

For each frame, write one `.txt` line per visible model in YOLO
format. The class id is just a fixed lookup
(`beaker → 0, vial → 1, centrifuge → 2, …`).

### 4. Randomise so the dataset isn't one canned shot

For each frame, vary:

- Lighting — random sun angle and a random HDR environment map.
- Camera pose — small (±2 cm, ±2°) nudges.
- Object pose — small jitter for objects that can move (e.g.
  the beaker), keep fixed for objects that can't (the bench).
- Material colours — different cap colours, different lab-bench
  laminate finish.

Variety beats volume. **2 000** randomised frames usually beat
**20 000** near-identical ones.

## What you end up with

```
synthetic_<step>/
├── images/
│   └── frame_<N>.jpg          # 1280×720 RGB
└── labels/
    └── frame_<N>.txt          # YOLO-format boxes
└── dataset.yaml               # class names + split paths
```

That folder drops directly into `exercises/03-tiny-yolo/`'s
`dataset.yaml` and trains a YOLO model with one `python
train.py` call.

## Existing project reference

The current
[`exercises/03-tiny-yolo/`](../../../../exercises/03-tiny-yolo/)
expects exactly this layout. Its `data/synthetic_autosampler/`
folder is the same shape but for the v1 autosampler 5-class set;
for the ketchup case you would dump a `data/synthetic_ketchup/`
shaped identically and re-train.
