# Type 3 — Depth images and point clouds

## What it is

Two related things that come from the same sensor:

- **Depth image.** A second "picture" the same size as the RGB
  one where every pixel stores **how far away that pixel is from
  the camera**, in metres. A pure number per pixel — no colour.
- **Point cloud.** The same depth image converted to a list of
  3D points `(x, y, z)` in the camera frame. Stored as `.ply`,
  `.pcd`, or just a `numpy` array.

In real hardware this comes from an Intel RealSense D435,
Microsoft Azure Kinect, or similar RGB-D camera. In Gazebo it
comes from a built-in **depth-camera sensor**.

## When it is useful

Anything that needs a **3D position** without sticking a marker
on the object:

- "How tall is the cap above the bench surface?" — needed to
  plan the gripper approach.
- "Where exactly is the centre of the centrifuge well, in
  metres?" — needed to drop the Falcon tube in.
- "How high is the rack top compared to the bench top?" — needed
  to plan a clear hover-pose between picks.

In short: **depth turns a 2D pixel into a 3D coordinate**.

## Who uses it

**Not a neural network**, in most cases. Depth feeds a small
piece of straight-line math:

```python
# given a pixel (u, v) and depth d_metres,
# the 3D point in camera frame is:
import numpy as np
K = camera_intrinsic_matrix_from_sdf()
xy_h   = np.linalg.inv(K) @ np.array([u, v, 1.0])
point  = xy_h * d_metres                      # (X, Y, Z) in camera frame
```

That's it — no training, no model. The depth value plus the
known camera intrinsics is the whole calculation.

Where ML does enter: **RGB-D segmentation networks** (e.g. SAM
with depth, FCN-with-depth) take depth as a second input
channel. They aren't standard for this cell, but the option
exists.

## How to produce it in Gazebo

Gazebo ships a depth-camera plugin. You add it to the SDF
alongside (or instead of) the RGB camera.

### 1. Add the sensor

```xml
<sensor name="overhead_depth" type="depth_camera">
  <pose>0 0 1.4 0 1.5708 0</pose>
  <camera>
    <horizontal_fov>1.05</horizontal_fov>
    <image>
      <width>1280</width>
      <height>720</height>
      <format>R_FLOAT32</format>
    </image>
    <clip>
      <near>0.10</near>
      <far>2.00</far>
    </clip>
  </camera>
  <update_rate>30</update_rate>
  <topic>/overhead/depth</topic>
</sensor>
```

The `<clip>` block matters: a RealSense D435 cannot see closer
than ~0.10 m or farther than ~3 m reliably; matching those
limits in sim avoids surprises later.

### 2. Bridge to ROS 2

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /overhead/depth@sensor_msgs/msg/Image[gz.msgs.Image \
    /overhead/depth/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked
```

The depth topic gives you the per-pixel metric image; the
points topic gives you the same data already converted to
`PointCloud2`.

### 3. Make the depth realistic (optional but recommended)

A real depth camera is not noise-free. To stop your trained
code from over-trusting metre-accurate sim depth and then
breaking on real noisy hardware, add a small noise model to the
sensor:

```xml
<noise>
  <type>gaussian</type>
  <mean>0.0</mean>
  <stddev>0.003</stddev>     <!-- 3 mm at this distance -->
</noise>
```

The RealSense D435 gives roughly ±2–3 mm at 40 cm — matching
those numbers in the simulator means the sim trace looks like
the real trace.

### 4. Save what you need

For a per-frame dataset, you can save either format — both
are recoverable from the other:

```
synthetic_<step>/
├── images/
│   ├── frame_<N>.jpg              # RGB
│   ├── frame_<N>.depth.npy        # H×W float32 metres
│   └── frame_<N>.cloud.ply        # optional — same data as a point cloud
└── camera_intrinsics.json         # K, distortion
```

`.depth.npy` is the cheapest and most flexible — every
RGB-D library reads it.

## Common gotcha

Gazebo's depth-camera output is **z-depth** (distance along the
optical axis), not **Euclidean range** (distance from the camera
centre). Most ROS / OpenCV code expects z-depth, so you are
usually fine, but check if your tooling complains — there is a
short conversion if needed.

## Existing project reference

[`exercises/08-depth-to-3d-centroid/`](../../../../exercises/08-depth-to-3d-centroid/)
already runs the depth-pixel → 3D-metres math on the v1
autosampler world. For the ketchup case, the same pipeline reads
the same depth topic — only the world file changes.
