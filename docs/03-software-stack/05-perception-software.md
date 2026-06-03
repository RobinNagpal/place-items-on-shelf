# Perception Software

The perception stack is the **software that turns camera frames into a
list of objects**: "there's a red cup at (0.32, -0.15, 0.05), tilted
12° about the vertical axis."

Without perception, the robot only moves to **memorised** positions —
fine for a fixed jig, useless the moment something shifts by a
centimetre.

This file is just about which perception libraries to use and what each
one does.

## What you check, before anything else

- **What does the task need?** "Pick from a fixed jig" doesn't need
  perception at all. "Pick whatever's on the table" needs full 6-DOF
  pose estimation.
- **What sensors did you pick in Layer 2?** A 2D RGB camera limits you
  to 2D detection plus an assumed working plane. A depth (RGB-D) camera
  lets you do 3D segmentation and pose. A stereo or structured-light
  industrial scanner does it best, at higher cost.
- **Is the lighting controlled?** Uncontrolled lighting punishes
  classical CV. ML models tolerate it better.
- **Real-time or offline?** "Detect once before moving" is forgiving.
  "Detect every 30 ms while moving" tightens every choice.

## What perception is composed of

A complete pipeline usually has these stages:

1. **Capture** — read frames from the camera. Driver-specific.
2. **Calibrate** — intrinsics (lens), extrinsics (camera-to-robot
   transform), depth alignment.
3. **Pre-process** — denoise, crop, undistort.
4. **Detect / segment** — find objects in the frame. Output bounding
   boxes or per-pixel masks.
5. **Estimate pose** — turn the detection into a 6-DOF pose in the
   robot's frame.
6. **Track / filter** — smooth across frames, handle dropouts.
7. **Publish** — broadcast results as ROS 2 topics for the planner.

Pick a library per stage. Most projects use one library for stages 1-3,
another for 4-5, and ROS 2 / tf2 for 6-7.

## The main options

### Driver / capture libraries

- **`v4l2`** — Linux's generic camera capture. Works for most USB
  webcams.
- **`librealsense2`** — Intel RealSense depth cameras.
- **`pyk4a` / Azure Kinect Sensor SDK** — Azure Kinect.
- **`pyzed` / ZED SDK** — Stereolabs ZED.
- **`Spinnaker SDK`** — FLIR / Teledyne machine-vision cameras.
- **`pylon`** — Basler cameras.
- **ROS 2 camera drivers** — `image_pipeline`, `realsense2_camera`,
  `azure_kinect_ros_driver`, vendor packages.

**Best for what:** pick the SDK that matches your camera. The ROS 2
wrapper saves you from writing capture code yourself.

### Classical 2D computer vision

Useful for controlled lighting, known textures, fast prototypes.

- **OpenCV** — the canonical 2D CV library. Thresholding, contour
  detection, feature matching (SIFT, ORB), template matching, ArUco /
  AprilTag detection.
- **AprilTag / ArUco** — fiducial markers. Stick them on objects or on
  fixtures for cheap, robust pose.

**Best for what:** ArUco tags on calibration boards, classical color
thresholding when you control lighting, sub-pixel feature alignment.

### Classical 3D / point cloud processing

For depth cameras and LiDAR-like data.

- **PCL (Point Cloud Library)** — the standard C++ library. Filtering,
  segmentation, plane fitting, registration (ICP), feature descriptors
  (FPFH, SHOT).
- **Open3D** — Python-friendly modern alternative. Faster development,
  easier to read.
- **CGAL** — geometry kernels when you need exact predicates.

**Best for what:**
- PCL — embedded into existing C++ pipelines, plane removal, cluster
  segmentation.
- Open3D — Python research, custom ML preprocessing, faster iteration.

### Deep-learning detection / segmentation

When classical CV isn't enough — the lighting varies, the objects
change, or you want the system to generalise.

- **YOLO (Ultralytics YOLOv8, YOLOv11)** — fast object detection.
  Pretrained on COCO, easy to fine-tune.
- **Detectron2 (Meta)** — Mask R-CNN, instance segmentation. Heavier
  but more accurate.
- **Segment Anything (SAM, SAM 2)** — promptable segmentation. Click
  or describe; SAM returns the mask. Great for labelling new datasets
  fast.
- **MMDetection / MMSegmentation** — OpenMMLab's training and zoo.
- **Grounding DINO + SAM** — open-vocabulary detection: "find the
  red mug" in text, get a mask back.

**Best for what:**
- YOLO — real-time on Jetson, simple classes you can label.
- SAM 2 — when classes change often, you want zero-shot masks.
- Grounding DINO + SAM — research / general-purpose pick robots.

### 6-DOF pose estimation

Once you have a detection, you need pose in metres + orientation in the
robot's frame.

- **MegaPose, FoundationPose** — recent neural pose estimators.
  Work on novel objects with a CAD model.
- **CosyPose, DenseFusion, PVNet** — earlier neural methods. Still
  used for known objects.
- **Industrial bin-picking software** — Mech-Mind, Photoneo, Zivid
  bundle their scanner with proprietary pose software. Highest
  accuracy when you can afford it.
- **Manual: ArUco / AprilTag** — when you can stick a tag on, use it.

**Best for what:**
- FoundationPose — novel objects with a CAD mesh, research and pilots.
- Mech-Mind / Photoneo — production bin picking with budget.
- ArUco — fixtures, calibration, "cheat" demos.

### Grasp generation

A specialised perception output: where to grip the detected object.

- **GraspNet, ContactGraspNet** — generate grasp candidates from depth
  + RGB.
- **Dex-Net** — older but still cited.
- **Vendor grasp software** — bundled with industrial bin-picking
  scanners.

**Best for:** "given an object I've never seen, where should the gripper
go?" Pair with detection / segmentation upstream.

### Calibration tools

Often the unsexy bit that makes or breaks the cell.

- **`camera_calibration` (ROS 2)** — intrinsics for monocular cameras.
- **`ros2_easy_handeye`, `MoveIt Calibration`** — hand-eye calibration
  (camera-to-robot transform). Critical for accuracy.
- **Kalibr** — multi-camera + IMU calibration.

**Best for what:** every cell needs hand-eye calibration done **once,
correctly**. If your picks are off by 5 mm every time, this is
where you look.

## How to pick

1. **Fixed jig, known positions?** → No perception needed. Use tf2.
2. **Single known object class, controlled lighting?** → OpenCV +
   ArUco tags or simple color / contour.
3. **Multiple objects, decent lighting, depth camera?** → YOLO (or
   SAM 2) + Open3D for 3D segmentation + simple cluster centroid.
4. **Novel objects with CAD?** → FoundationPose / MegaPose.
5. **Industrial bin picking with budget?** → Mech-Mind / Photoneo
   bundle.
6. **Research, "pick whatever I describe"?** → Grounding DINO + SAM
   2 + GraspNet, glued together.

## Output of this file — your perception plan

```
Camera driver:           realsense2_camera / azure_kinect_ros_driver / pylon / v4l2
Calibration done?:       yes (date: ___ , RMS error: ___ ) / no
Detection / segmentation: YOLO ___ / SAM 2 / Detectron2 / OpenCV classical / ArUco
6-DOF pose method:       FoundationPose / MegaPose / ArUco tag / vendor bundle / none
Grasp generation:        ContactGraspNet / vendor / hand-tuned heuristic / none
3D library:              PCL / Open3D / both
Publishing as:           tf2 frames / PoseStamped / Detection3DArray / vendor
Frame rate target:       ___ Hz
Latency budget:          ___ ms (capture → published pose)
```

## Common mistakes

1. **Skipping hand-eye calibration.** Every later pick is off by the
   error you didn't measure.
2. **Training a custom model when ArUco would do.** Use the tag.
3. **Ignoring lighting.** Add a hood. Add diffuse light. Spending $50
   on lighting saves a week of model tuning.
4. **Running on a Pi when the model needs a Jetson.** Inference is
   too slow, frames pile up. Test the model on the actual target
   hardware before committing.
5. **No frame timestamps.** Without per-frame timestamps, the planner
   can't tell whether a detection is fresh.
6. **Publishing in the wrong frame.** Always publish poses in a clearly
   named frame, tf2-linked to `base_link`.

## What's next

Classical perception covers most pick-and-place tasks. When it doesn't
— when you want the robot to generalise to objects it's never seen, or
to follow natural-language instructions — you reach for foundation
models.

→ Next: [06-ai-and-foundation-models.md](06-ai-and-foundation-models.md)
