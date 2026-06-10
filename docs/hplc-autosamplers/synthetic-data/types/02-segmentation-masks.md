# Type 2 — Per-pixel segmentation masks

## What it is

The same picture as type 1, plus a **second image** of the same
size where every pixel is colour-coded by **the object it
belongs to**.

Two flavours:

- **Semantic mask.** All vial pixels are colour 1, all beaker
  pixels are colour 2, no matter how many vials or beakers.
- **Instance mask.** Vial #1 is colour 1, vial #2 is colour 2,
  …, so touching items can be counted and separated.

A picture is worth a thousand words here: the mask "shows you
the exact silhouette of every object," not just the rectangle.

## When it is useful

Whenever the **shape** matters more than the location:

- Vials in a tray sit ~14 mm centre-to-centre. Their boxes
  overlap; their **masks** don't. Telling vial #34 from vial
  #35 needs masks.
- Telling "the cap is sitting flush on the rim" from "the cap
  is sitting at an angle" needs the cap silhouette, not its
  bounding box.
- Computing the pellet-vs-supernatant boundary inside a Falcon
  tube is a mask problem.

## Who uses it

A **segmentation neural network**. Standard choices:

- **YOLOv8-seg** — adds a mask head to YOLO, same Ultralytics
  workflow. Best default for this project.
- **SAM / SAM 2** — Meta's foundation segmenter, works
  zero-shot but is heavier.
- **Mask R-CNN** — the classical academic choice.

Training reads `(image, mask)` pairs.

## How to produce it in Gazebo

Two options, depending on which simulator you are on.

### Option A — Gazebo Ignition's segmentation camera (preferred)

Gazebo Ignition / Gazebo Sim ships a **segmentation camera
sensor** (`segmentation_camera` in the SDF) that renders the
scene a second time but emits a per-pixel object-ID image
instead of RGB. The IDs match what's in `/world/.../pose/info`,
so you get a labelled mask aligned with the RGB frame for free.

```xml
<sensor name="overhead_seg" type="segmentation_camera">
  <pose>0 0 1.4 0 1.5708 0</pose>
  <camera>
    <segmentation_type>instance</segmentation_type>    <!-- or "semantic" -->
    <horizontal_fov>1.05</horizontal_fov>
    <image>
      <width>1280</width>
      <height>720</height>
      <format>L_INT16</format>
    </image>
  </camera>
  <update_rate>30</update_rate>
  <topic>/overhead/segmentation</topic>
</sensor>
```

Bridge to ROS 2 and save:

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /overhead/segmentation@sensor_msgs/msg/Image[gz.msgs.Image
```

The image is single-channel; each pixel's integer value is the
model ID. Convert to a coloured PNG for inspection, but keep the
raw ID image as the training label.

### Option B — shader trick if you're on classical Gazebo

Old Gazebo (Garden and older) does not have a segmentation
camera. Workaround: render the scene twice — once normally,
once with **every model given a unique flat material colour**
and lighting disabled. The flat-colour pass *is* the mask.

```xml
<material>
  <ambient>0 0.1 0 1</ambient>            <!-- ID 26, encoded as RGB -->
  <diffuse>0 0.1 0 1</diffuse>
  <emissive>0 0.1 0 1</emissive>          <!-- ignores lighting -->
</material>
```

Threshold the flat-colour image by colour bins back to IDs.

### Adding the right kind of variety

Same as type 1 — randomise lighting, camera pose, materials.
For masks specifically also vary:

- **Occlusion** — drop a pen / cloth / hand into the scene that
  partially covers other objects. The mask boundary tightens
  the model.
- **Clutter** — add extra non-target items (a marker, a notebook)
  so the model learns "no, that's not a vial."

## What you end up with

```
synthetic_<step>/
├── images/
│   └── frame_<N>.jpg
├── masks/
│   └── frame_<N>.png             # single-channel, ID per pixel
└── class_lookup.json             # {"1": "beaker", "2": "vial", ...}
```

For YOLOv8-seg specifically you may also need polygon labels
(YOLO's seg format). They are a 5-line conversion from the
ID image:

```python
import cv2, numpy as np
ids = cv2.imread("frame_0001.png", cv2.IMREAD_UNCHANGED)
for cid in np.unique(ids):
    if cid == 0: continue                     # background
    mask = (ids == cid).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    # write polygon as YOLO-seg .txt row
```

## Existing project reference

[`exercises/07-instance-segmentation/`](../../../../exercises/07-instance-segmentation/)
already runs YOLOv8-seg on the Gazebo camera and consumes
exactly this shape of label, so the produce-and-train loop is
already wired up — you just need to point it at the
ketchup-world dataset.
