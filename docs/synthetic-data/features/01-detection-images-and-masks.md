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

We rely on three families of techniques, in roughly this order of
importance: **domain randomisation**, then **photo-real rendering**,
then **procedural scenes**.

### 1. Domain randomisation — the six axes

The single most important technique for sim-to-real transfer. The
idea: vary as many aspects of the scene as possible per frame, so
the model is forced to learn the *invariant* (the object) and ignore
everything else. Choosing just one or two axes is what produces
brittle detectors that overfit to "what sim looks like."

The six axes the literature (NVIDIA Replicator, BlenderProc,
OpenAI's 2017 DR paper) and production pipelines actually turn:

1. **Camera pose** — yaw / pitch / distance jitter, sometimes a few
   centimetres of position noise too. Cheap, easy, the obvious
   first axis. By itself it is **not enough** — you also need
   the object to move, not just the viewpoint.
2. **Object pose** — every object's translation (±5 cm typical) and
   yaw (±20° typical) randomised per frame. This is the single
   most important axis once camera pose is done; without it the
   model memorises one staged scene.
3. **Lighting** — direction, intensity, colour temperature, and
   often the *number* of lights. Add ambient fill, change the sun
   angle, sometimes drop in a coloured fill light.
4. **Materials / textures** — randomise the bench colour, the floor
   texture, the wall pattern. Even pattern the *target* objects
   with random textures sometimes (so the model learns the
   *shape*, not the colour). Often called "structured DR".

   For real textures (not just flat colours), Gazebo accepts PBR
   maps inside `<material><pbr><metal>`: `<albedo_map>`,
   `<normal_map>`, `<roughness_map>`, `<metalness_map>`. Drop a
   folder of free PBR sets (e.g. from
   [Polyhaven](https://polyhaven.com/textures) or
   [ambientCG](https://ambientcg.com)) under
   `gazebo_worlds/.../textures/`, export
   `GZ_SIM_RESOURCE_PATH=$PWD/gazebo_worlds/...` so `file://`
   paths resolve, and swap the script's `<diffuse>` line for an
   `<albedo_map>file:///abs/path.png</albedo_map>`. The same
   spawn-and-remove flow used for colour randomisation works for
   texture randomisation — and uses no extra Gazebo plugin.
5. **Distractor objects** — spawn 1-10 random clutter items (a pen,
   a tape roll, a clipboard, an unrelated bottle) at random poses
   in each frame so the model learns "not every cylindrical
   object is a beaker".
6. **Background** — swap the floor / walls / skybox between frames.
   Common trick: render onto a random photo from COCO behind the
   bench.

Rule of thumb: vary 1-2 axes and the detector overfits; vary 5-6
aggressively and it generalises to real photos it was never trained
on. The exercise under
[`gazebo_worlds/02-dissolution-and-extraction/synthetic_data/`](../../../gazebo_worlds/02-dissolution-and-extraction/synthetic_data/)
now implements **all six** axes — #1 (camera pose), #2 (object pose),
#3 (lighting), #4 (materials / textures), #5 (distractor objects)
and #6 (background) — as six separate warm-up scripts, one per
axis. A production dataset would combine them per frame rather than
running them in isolation; that's the next iteration.

### 2. Photo-real rendering

When the customer's real camera is high-quality (RealSense, Basler,
FLIR), we render with Isaac Sim's RTX path tracer so the synthetic
frames look close to a real photo (PBR materials, ray-traced
shadows, screen-space reflections). For geometric-only tasks
("which slot is the vial in?") Gazebo's faster OGRE renderer is
enough.

### 3. Procedural scenes

When the cell layout itself can vary (rack in slightly different
position, products restocked in random order), we generate the
layout from code every time, not from one fixed scene. This is
randomisation axis #2 on steroids — instead of jittering known
poses, we re-instantiate the whole scene from a small set of
parameters.

### What we do NOT add

We do **not** bake sensor noise (Gaussian RGB noise, motion blur,
JPEG compression artefacts) into the rendered frames. The model
needs to see *clean* edges of objects to learn the boxes; noise is
added at training time using standard augmentation libraries
(`Albumentations`, `torchvision.transforms`). Treating noise as a
training-time transform — not a generation-time bake-in — also lets
the same dataset feed multiple models with different augmentation
budgets.

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
