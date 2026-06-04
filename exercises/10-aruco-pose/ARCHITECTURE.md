# Architecture — exercise 10

One file owns the work; everything else (image source, intrinsics
constants, downstream consumers) lives in other exercises.

```
10-aruco-pose/
├── README.md                  # concept, full Q&A on how detection works
├── ARCHITECTURE.md            # this file
├── IMPLEMENTATION_NOTES.md    # SDF marker snippet, knobs, failure modes
└── aruco_detector_node.py     # only new code
```

## What `aruco_detector_node.py` owns

A single ROS 2 node `ArucoDetectorNode` plus one helper:

| Function / class            | Responsibility                                                            |
|-----------------------------|---------------------------------------------------------------------------|
| `rmat_to_quat`              | 3×3 rotation matrix → `(qx, qy, qz, qw)`. Pure NumPy, no SciPy / tf.       |
| `ArucoDetectorNode.__init__`| Subscribe, publish, build dictionary + detector + 3D corner template      |
| `ArucoDetectorNode._on_image` | Per-frame detect + PnP + publish                                        |

Module-level constants:

- `CAMERA_MATRIX` and `DIST_COEFFS` — pinhole intrinsics derived
  from the SDF (same numbers as exercises 05 / 08 / 12). The
  distortion vector is all zeros because Gazebo cameras are
  perfectly pinhole.
- The 3D corner template `_object_pts` is computed once in
  `__init__` from the `marker_size_m` parameter; PnP needs the
  marker's own-frame corner coordinates as input.

## Inputs / outputs at the ROS layer

```
SUBSCRIBES
   /overhead_camera/image_raw    sensor_msgs/Image  (bgr8)

PUBLISHES
   /aruco/markers                vision_msgs/Detection3DArray
       one Detection3D per detected marker
       header.frame_id  = camera optical frame (copied from input)
       bbox.center      = 6-DoF pose of marker centre in camera frame
       bbox.size        = (marker_size, marker_size, ~0)
       results[0].hypothesis.class_id = "aruco_<int_id>"
       results[0].hypothesis.score    = 1.0
       results[0].pose.pose            = mirror of bbox.center
```

## Per-frame control flow

```
_on_image (called for every input image at ~30 Hz)
  cv_bridge convert → numpy BGR
  cv2.cvtColor → grayscale
  detector.detectMarkers(gray) → corners list, ids array
  for each (corner, id) pair:
      cv2.solvePnP(object_pts, image_pts, K, dist, IPPE_SQUARE)
          → rvec, tvec
      cv2.Rodrigues(rvec) → 3x3 rotation matrix
      rmat_to_quat(R) → quaternion
      build Detection3D, append to out.detections
  publish out
```

No state is held across frames. Every input image produces one
fully self-contained output message.

## What depends on what

- **Upstream:** the overhead camera SDF + bridge from exercise 04.
  Move the camera in the SDF and the constants at the top of this
  file need updating in sync with `detection_scorer.py` and
  `centroid_node.py`.
- **Downstream:**
  - **Exercise 12 (hand-eye calibration)** subscribes to
    `/aruco/markers` and pulls the marker glued to the EE.
  - **A future tray-locator helper** (not on the checklist as its
    own item) maps `class_id == "aruco_<n>"` → a tray identity and
    computes slot poses by applying a fixed CAD offset.

## What is deliberately not here

- **The Gazebo marker model** — the SDF snippet for a textured
  ArUco plate lives in `IMPLEMENTATION_NOTES.md` so SDF changes
  stay in one prose file rather than scattering.
- **The slot-pose calculator** — domain logic that belongs near the
  pick controller, not in the perception node.
- **TF broadcasting** — we publish poses on a topic; downstream
  decides whether to broadcast them as TF. Keeps this node a leaf.
