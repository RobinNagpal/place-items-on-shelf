# Implementation notes — exercise 10

## Why ArUco and not AprilTag / QR code

All three encode an ID in a small printed square; all three can be
located in 6-DoF. We chose ArUco because:

- **It ships with OpenCV.** No extra ROS package, no AprilTag2-ROS
  binding to manage.
- **Square markers (vs round ones) suit `cv2.SOLVEPNP_IPPE_SQUARE`,**
  the fastest specialised PnP solver in OpenCV.
- **Multiple dictionaries** to pick from (`DICT_4X4_50`,
  `DICT_5X5_100`, `DICT_ARUCO_ORIGINAL`, ...) — we pick the
  smallest that gives enough unique IDs.

AprilTag has marginally better pose accuracy at small marker
sizes; QR codes encode arbitrary strings but are slower to detect
and locate. Neither difference matters for our tray-marker use
case.

## Why `cv2.SOLVEPNP_IPPE_SQUARE`

OpenCV ships several PnP back-ends:

| Flag                          | Best for                                  |
|-------------------------------|-------------------------------------------|
| `SOLVEPNP_ITERATIVE`          | General N-point; needs an initial guess   |
| `SOLVEPNP_AP3P` / `SOLVEPNP_P3P` | Exactly 3 points                       |
| `SOLVEPNP_EPNP`               | N ≥ 4, fast, slightly less accurate       |
| `SOLVEPNP_IPPE`               | N ≥ 4 coplanar points                     |
| `SOLVEPNP_IPPE_SQUARE`        | Exactly 4 coplanar corners of a square    |

For ArUco we always have exactly 4 coplanar corners of a square;
`IPPE_SQUARE` is the analytical solver designed for that case. It
is ~5× faster than the iterative solver and dodges the planar
ambiguity issues that bite EPNP.

The choice is one line; revisit if you ever swap markers for
non-square shapes.

## Why marker SIZE matters (and where to set it)

The PnP solver computes the marker-to-camera **distance** from the
ratio between the marker's known physical size and how big it
appears in the image. A 30 mm square that covers 36 pixels says
"camera is X away"; the same 30 mm at 18 pixels says "camera is
2X away".

If you tell the node the marker is 30 mm but it's actually 25 mm,
**every distance comes out 20% wrong**. The PnP residual will
still report "solved successfully" because the math is internally
consistent — the only person who can catch the mistake is whoever
typed the wrong number.

The size is a node parameter, defaulted to 30 mm. Override at
launch:

```bash
python3 aruco_detector_node.py --ros-args -p marker_size_m:=0.025
```

## Dictionary sizing

`DICT_4X4_50` (4×4 internal grid, 50 unique IDs) is enough for our
use case — we need maybe 2–4 tray markers plus one for the EE
during calibration. Larger dictionaries trade marker IDs for
higher per-bit redundancy:

| Dictionary           | Internal grid | # IDs | Robustness                             |
|----------------------|---------------|-------|-----------------------------------------|
| `DICT_4X4_50`         | 4 × 4         | 50    | Lowest; fine for clean overhead lighting |
| `DICT_5X5_100`        | 5 × 5         | 100   | Better; more hamming distance per ID    |
| `DICT_6X6_250`        | 6 × 6         | 250   | Best; needed if you have many markers   |
| `DICT_APRILTAG_36h11` | 6 × 6         | 587   | Highest hamming distance, large IDs     |

All four are detectable by `cv2.aruco` with one parameter change.

## Camera intrinsics — same constants, in a third place

`CAMERA_MATRIX` here is the same matrix as in
`exercises/05-score-detections-vs-gazebo/detection_scorer.py` and
`exercises/08-depth-to-3d-centroid/centroid_node.py`. Three copies
of the same constants is a small smell — when we add a `camera_info`
publisher (item 11 in the original checklist, deferred), all three
files should subscribe to `/overhead_camera/camera_info` instead
of hard-coding.

Until then, keep them synchronised by hand. If you edit the SDF
camera, grep:

```
grep -rn "HFOV = 1.0472" exercises/
```

…and update every match.

## Putting an ArUco marker in Gazebo

For Gazebo to display a marker the world must contain a textured
plane. Two steps:

1. **Generate the PNG:**

   ```python
   import cv2
   d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
   img = cv2.aruco.generateImageMarker(d, 3, 300)  # ID=3, 300x300 px
   cv2.imwrite("aruco_3.png", img)
   ```

2. **Add a 30 mm × 30 mm box with the PNG as its texture** to the
   SDF (next to the tray model):

   ```xml
   <model name="aruco_tray_source">
     <static>true</static>
     <pose>0.20 0.00 0.825 0 0 0</pose>     <!-- glued to the tray top -->
     <link name="link">
       <visual name="v">
         <geometry><box><size>0.030 0.030 0.0005</size></box></geometry>
         <material>
           <pbr><metal>
             <albedo_map>file://aruco_3.png</albedo_map>
           </metal></pbr>
         </material>
       </visual>
       <collision name="c">
         <geometry><box><size>0.030 0.030 0.0005</size></box></geometry>
       </collision>
     </link>
   </model>
   ```

We do not ship this SDF block here — it belongs in exercise 04's
world file, and adding it touches a different folder. The intent
is to document the recipe in one place rather than scatter SDF
fragments.

## Failure modes you'll see first

| Symptom                                         | Most likely cause                                                |
|-------------------------------------------------|------------------------------------------------------------------|
| `detectMarkers` returns nothing every frame      | Marker too small in the image — fewer than ~25 px per side fails |
| Detected, but pose is off by ~20%                | `marker_size_m` parameter wrong                                  |
| Pose flips orientation between frames            | Marker viewed near edge-on; IPPE has known planar ambiguity      |
| `cv2.aruco.ArucoDetector` AttributeError         | OpenCV < 4.7 — older API is `cv2.aruco.detectMarkers(gray, dict)` directly |
| Quaternion appears unnormalised in RViz          | The trace-formula branch picked is wrong; check `rmat_to_quat`   |

## Performance

`detectMarkers` plus four `solvePnP` calls (one per marker)
finishes in ~5 ms on a modern CPU for 640 × 480. Throughput is
camera-limited at 30 Hz, never CPU-limited. No GPU needed.

If you ever scale to hundreds of markers in one frame (unlikely
here), batch their corners into a single `solvePnP` call with a
larger `objectPoints` array; the OpenCV docs walk through the
trick.

## Where the output should ultimately publish to TF

We chose to publish on a topic instead of broadcasting TF directly,
for two reasons:

- Tray markers move only when a tech bumps the tray. Broadcasting
  at 30 Hz is wasteful.
- The downstream consumer (a tray-pose latcher) wants to validate
  the detection (multiple frames agree, marker hasn't suddenly
  jumped) before committing it to TF.

The natural downstream pipeline is:

```
/aruco/markers ──► tray_pose_latcher (validate + smooth)
                         │
                         ▼
                static_transform_publisher per tray
                         │
                         ▼
                  TF for the pick controller
```

That latcher is one short rclpy node; we leave it to whoever wires
the pick controller end-to-end.
