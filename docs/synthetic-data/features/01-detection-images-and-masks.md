# Feature 1 — Detection Images and Masks

> **Poster wording.** "Camera frames with bounding boxes plus
> segmentation masks at every pixel. Ready to train YOLO or any model
> your team already runs."

## What it is, in simple words

The simulator renders a camera frame — like a photograph from a virtual
camera inside the cell. For every object in the frame we also output:

- A **bounding box** — a rectangle that tightly wraps the object, plus
  its class name. ("This rectangle is a `vial`.")
- A **segmentation mask** — a black-and-white image the same size as
  the frame. Every pixel of the object is white; every other pixel is
  black. One mask per object.

Both labels come from the simulator's **ground truth** — the simulator
already knows which pixel belongs to which object, so we just dump it.
No human labeler involved.

A finished dataset looks like a folder of thousands of pairs:

```
detection_<project>/
├── images/         frame_00001.png, frame_00002.png, …
├── labels/         frame_00001.txt   (YOLO format, one box per line)
└── masks/          frame_00001_vial.png, frame_00001_cap.png, …
```

## Who will use it

The customer's **perception engineer** or **ML engineer**. They feed
this dataset into an object detector or a segmentation model, then run
the trained model on the real camera in production.

Typical job titles to look for in outreach: *Perception Engineer*,
*Computer Vision Engineer*, *Robotics ML Engineer*, *Applied Scientist
(Vision)*.

## What models the customer trains with it

- **YOLOv5 / YOLOv8 / YOLOv11** — the most common object detector in
  industry. Fast, easy to deploy on a Jetson.
- **YOLOv8-seg** — same family, also outputs segmentation masks.
- **Mask R-CNN** — older but still common; outputs masks.
- **Faster R-CNN, RT-DETR** — alternative detectors.
- **SAM (Segment Anything) fine-tunes** — when the customer wants a
  big foundation model that segments novel objects.

## Libraries and frameworks involved

**On our side (to build the data):**

- **Gazebo** with the `sensors` plugin for the virtual camera.
- **Isaac Sim Replicator** when the customer needs photo-real frames
  (RTX path tracer).
- A small Python script that reads the simulator's "object id" buffer
  and turns it into bounding boxes and masks.

**On the customer's side (to train):**

- **Ultralytics** (`pip install ultralytics`) — trains YOLOv5/8/11.
- **MMDetection** or **Detectron2** — the research-style alternatives.
- **PyTorch** — the underlying deep-learning library.

## What we ship (the formats)

| Format | When we use it |
|--------|---------------|
| **YOLO labels** — one `.txt` per image with `class x_center y_center width height` | Default for any Ultralytics YOLO project. |
| **COCO JSON** — one big JSON file with all images and all boxes / masks | Detectron2, MMDetection, RT-DETR, plus YOLOv8 also reads it. |
| **PNG masks** — one PNG per object per frame | When the customer wants per-pixel masks for Mask R-CNN. |

The customer tells us their format; we ship in that format. No
post-processing on their side.

## How we generate it (the methods)

- **Domain randomisation** — every frame has different lighting,
  random textures on the table and walls, the camera shifted a few
  cm, and a few distractor objects scattered around. The model trains
  on variation, so it does not memorise "what sim looks like."
- **Photo-real rendering** — when the customer's real camera is high
  quality (RealSense, Basler, FLIR), we render with Isaac Sim's RTX
  path tracer so the synthetic frames look close to a real photo.
- **Procedural scenes** — when the cell layout itself can vary (rack
  in slightly different position, products restocked in random
  order), we generate the layout from code every time, not from one
  fixed scene.

We do **not** add sensor noise to the RGB by default — the model needs
to see *clean* edges of objects to learn the boxes. Noise is added at
training time using standard augmentation (`Albumentations`,
`torchvision.transforms`).

## Pain points this solves

- **"Labelling is killing our budget."** A human labels ~50 frames /
  hour. We produce ~10 000 labelled frames overnight.
- **"Our model overfits."** Domain randomisation gives much more
  variation than a real-world dataset.
- **"We can't get rare angles."** In sim we can mount the camera
  anywhere; rare camera angles are free.

## What to say in a sales conversation

- "How many objects do you need to detect, and do you have CAD files
  for each?" *We need 3D models. PLY / STL / OBJ / USD all work.*
- "What format does your training pipeline already read?" *Default to
  COCO JSON or YOLO labels.*
- "How realistic do the images need to look?" *If they ship a vision
  model to a real RealSense, push for Isaac Sim. If the task is
  geometric (vials in fixed slots), Gazebo is enough.*
- "How many frames do you need?" *Typical scope: 5 000–50 000 frames.*

## Typical scope and delivery

- **Inputs we need from the customer:** CAD or STL of each object, a
  rough scene description (table size, camera mount position), one or
  two real photos of the cell for material matching, and the list of
  classes.
- **What we ship:** the project folder above, a `metadata.json` (what
  randomisation, what scene, what units), and a `README.md` telling
  the customer's engineer how to point Ultralytics at the dataset.
- **Typical timeline:** 2–3 weeks for the first 10 000-frame batch.
