# Perception Software

Perception software **turns camera frames into a list of objects**:
"there's a red cup at (0.32, -0.15, 0.05), tilted 12° about the
vertical axis."

Without perception, the robot only moves to **memorised** positions —
fine for a fixed jig, useless the moment something shifts.

## What you check first

- **What does the task need?** "Pick from a jig" needs no perception.
  "Pick whatever's on the table" needs full 6-DOF pose.
- **Which sensors did you pick in Layer 2?** A plain 2D camera limits
  you to 2D detection. A depth (RGB-D) camera lets you do 3D
  segmentation and pose.
- **Lighting controlled?** Uncontrolled lighting hurts classical CV.
  ML models handle it better.
- **Speed?** "Detect once before moving" is forgiving. "Detect every
  30 ms while moving" tightens everything.

## The stages of a perception pipeline

1. **Capture** — read frames from the camera.
2. **Calibrate** — lens (intrinsics) + camera-to-robot transform
   (hand-eye).
3. **Detect / segment** — find the object in the frame.
4. **Estimate pose** — turn the detection into a 6-DOF pose in the
   robot's frame.
5. **Publish** — send the pose to the planner on a `tf2` / ROS 2 topic.

You pick a library per stage. The big decision is **how you do
steps 3–4** — that's the "main options" below.

## The "how to find the object" ladder

From simplest to hardest. Pick the simplest one your task allows.

### 0. No perception — fixed jig

The object is always in the same place. Hardcode the pose; skip this
file entirely.

### 1. Fiducial markers (ArUco / AprilTag)

Stick a printed tag on the object or fixture. OpenCV detects the tag
and gives you a precise 6-DOF pose. Free, robust, no training.

**Best for:** calibration, demos, or any case where you control the
object and can put a sticker on it.

### 2. Known-dimension geometric detection

You don't know **where** the object is, but you do know its **size
and shape** — say, a 60 mm × 40 mm × 30 mm box, or a 50 mm-diameter
cylinder. The camera segments the table; the cluster whose
dimensions match is your target. Its centroid + principal axes give
you the pose, which you pass straight to MoveIt 2.

How it works:

- **Depth camera + Open3D / PCL** — drop the table plane (`RANSAC`
  plane fit), cluster the remaining points (Euclidean clustering),
  keep clusters whose bounding-box L × W × H matches the known
  dimensions within tolerance.
- **2D camera + known working plane** — threshold the image, fit
  contours, measure pixels, project to the working plane using the
  camera calibration.

No ML, no training data, no labels — pure geometry.

**Best for:** one object, one workspace, known dimensions, controlled
lighting. The cheapest "look-then-pick" pipeline after fiducials.

### 3. Classical colour / shape detection

Threshold by colour, find contours, match templates. The OpenCV
toolbox: `cv::inRange`, `findContours`, `matchTemplate`, `SIFT` /
`ORB` feature matching.

**Best for:** controlled lighting, distinctive colours, a small fixed
set of objects.

### 4. Deep-learning detection + segmentation

When the object changes, the lighting varies, or you want the system
to generalise.

- **YOLO (Ultralytics)** — fast object detection on Jetson. Pretrained
  on COCO; fine-tune for your classes.
- **Segment Anything (SAM, SAM 2)** — point or describe; SAM returns
  a pixel-perfect mask. Great for fast labelling and zero-shot
  segmentation.
- **Grounding DINO + SAM** — open-vocabulary: type "find the red mug",
  get a mask.
- **Detectron2 / Mask R-CNN** — heavier, more accurate, still common.

**Best for:** many object classes, varying lighting, real-time
inference on a GPU.

### 5. Neural 6-DOF pose estimation

You need not just *where* but *how* the object is oriented.

- **FoundationPose, MegaPose** — neural pose on novel objects from a
  CAD mesh.
- **CosyPose, DenseFusion, PVNet** — earlier methods for known
  objects.
- **Industrial bin-picking** — **Mech-Mind, Photoneo, Zivid** sell
  scanner + pose software bundles. Highest accuracy when you can
  afford it.

**Best for:** "pick an arbitrary object I have a CAD model for", or
production bin picking.

## Supporting libraries

You'll use these alongside whichever option above:

- **Camera drivers:** `realsense2_camera`, `azure_kinect_ros_driver`,
  `pylon` (Basler), `Spinnaker` (FLIR), `v4l2` (generic USB).
- **2D CV:** **OpenCV** — the canonical library.
- **3D / point cloud:** **PCL** (C++) or **Open3D** (Python).
- **Calibration:**
  - Intrinsics — `camera_calibration` (ROS 2).
  - Hand-eye (camera-to-robot) — `easy_handeye2`, `MoveIt Calibration`.
  - Multi-cam + IMU — `Kalibr`.

Every cell needs hand-eye calibration done **once, correctly**. If
your picks are off by 5 mm every time, this is where to look first.

## Grasp generation (a separate question)

After you've found the object, *where* should the gripper actually go?

- **GraspNet, ContactGraspNet** — generate grasp candidates from
  depth + RGB.
- **Vendor grasp software** — bundled with bin-picking scanners.
- **Hand-tuned** — for one known object, top-down centroid grip is
  often enough.

## How to pick

1. **Fixed jig?** → No perception. tf2 + hardcoded pose.
2. **Tag on the object or fixture is fine?** → ArUco / AprilTag.
3. **One known-dimension object, controlled lighting?** → Geometric
   detection (option 2). Pass pose to MoveIt 2.
4. **Few known objects, controlled lighting?** → OpenCV classical.
5. **Many objects, varying lighting, depth camera?** → YOLO or
   SAM 2 + Open3D for 3D segmentation.
6. **Novel objects with CAD?** → FoundationPose / MegaPose.
7. **Production bin picking with budget?** → Mech-Mind / Photoneo
   bundle.
8. **"Pick whatever I describe"?** → Grounding DINO + SAM 2 +
   GraspNet glued together.

## Output of this file — your perception plan

```
Camera driver:           realsense2_camera / azure_kinect_ros_driver / pylon / v4l2
Calibration done?:       yes (date: ___, RMS error: ___) / no
"How to find" option:    0 fixed-jig / 1 fiducial / 2 known-dimension / 3 classical / 4 DL / 5 6-DOF neural / vendor
6-DOF pose method:       geometric / ArUco / FoundationPose / MegaPose / vendor / none
Grasp generation:        ContactGraspNet / vendor / hand-tuned heuristic / none
3D library:              PCL / Open3D / both
Publishing as:           tf2 frames / PoseStamped / Detection3DArray / vendor
Frame rate target:       ___ Hz
Latency budget:          ___ ms (capture → published pose)
```

## Common mistakes

1. **Skipping hand-eye calibration.** Every pick is off by the error
   you didn't measure.
2. **Training a custom model when ArUco would do.** Use the tag.
3. **Reaching for ML when geometric detection would do.** If the
   object's size is fixed, segment by size and skip training entirely.
4. **Ignoring lighting.** A $50 hood saves a week of model tuning.
5. **Running on a Pi when the model needs a Jetson.** Inference is
   too slow, frames pile up. Test on real hardware before committing.
6. **Publishing in the wrong frame.** Always publish in a clearly
   named frame, tf2-linked to `base_link`.

## What's next

Classical perception covers most pick-and-place. When you want the
robot to generalise to unseen objects, or follow natural-language
instructions, you reach for foundation models.

→ Next: [06-ai-and-foundation-models.md](06-ai-and-foundation-models.md)
