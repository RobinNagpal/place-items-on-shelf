# Implementation notes — exercise 08

## Where depth comes from in Gazebo

Gazebo Sim ships a `depth_camera` sensor type that emits a
32-bit float image where each pixel is **metres of range**. To get
it we add one sensor block next to the existing RGB camera in
`exercises/04-yolo-live-on-gazebo-camera/worlds/autosampler_cell_with_camera.sdf`:

```xml
<sensor name="overhead_depth" type="depth_camera">
  <pose>0 0 0 0 0 0</pose>           <!-- relative to the camera link -->
  <update_rate>30</update_rate>
  <topic>overhead_camera/depth</topic>
  <camera>
    <horizontal_fov>1.0472</horizontal_fov>   <!-- 60 deg, same as RGB -->
    <image><width>640</width><height>480</height><format>R_FLOAT32</format></image>
    <clip><near>0.05</near><far>3.0</far></clip>
  </camera>
</sensor>
```

Bridge it to ROS 2 with `ros_gz_image`:

```bash
ros2 run ros_gz_image image_bridge /overhead_camera/depth
```

That single line gives us a ROS topic `/overhead_camera/depth` of
type `sensor_msgs/Image` with encoding `32FC1` and units in metres.
Beyond `<far>` Gazebo writes `+Inf`; behind `<near>` it writes
`0` — the node filters both with `np.isfinite` plus `> 0.05`.

## Why median depth instead of mean

A 12 mm vial cap projects to ~14 px wide top-down. A few rim
pixels along the mask edge will pick up the bench top instead of
the cap, which sits a few cm above the bench. Mean depth pulls
toward the bench in that case; median stays on the cap.

We also skip per-pixel deprojection. Once the depth is a single
robust value, deprojecting only the mask centroid `(u_mean, v_mean)`
is mathematically equivalent to deprojecting every pixel and then
averaging — to within sub-millimetre rounding on our intrinsics.
One vector operation instead of N.

## Pinhole intrinsics — same as exercise 05

```
fx = (W / 2) / tan(HFOV / 2)        = 554.26 px @ 640 wide / 60 deg
fy = fx                              (square pixels in the SDF)
cx = W / 2 = 320
cy = H / 2 = 240
```

These are baked as module-level constants. If you move the camera
or change the FOV in the SDF, update them here **and** in
`detection_scorer.py` from exercise 05. There is no `/camera_info`
topic on a plain Gazebo camera sensor — it has to be re-emitted by
hand, which is item 11's job.

## What the output frame really is

The depth image is in the **camera optical frame**: +X right, +Y
down, +Z forward (out of the lens). Our overhead camera looks
straight down at the bench, so:

- `+Z` in the centroid output points from the camera **down** to
  the bench (positive = farther = lower in world).
- `+X` in the centroid output points to the right of the image.
- `+Y` in the centroid output points to the bottom of the image.

This is **not** the world frame from exercise 05. The world-frame
mapping is one TF lookup away (`camera_optical_frame → world`), but
publishing TF is a different exercise. The contract this exercise
exports is *"3D points consistent with the depth image they came
from"* — downstream picks the transform.

## Pure-geometry alternative — why not in this exercise

The README walks through the pure-geometry path (Euclidean
clustering, RANSAC cylinder fit). It is a real and useful pipeline
and was the default before deep detectors arrived. The reasons we
skipped it for v1:

- **Identity** — the autosampler needs to know "slot A3", not
  "some vial". Detection already provides the label.
- **Speed** — RANSAC on a 640×480 point cloud is roughly an order
  of magnitude slower than mask + median depth.
- **Occlusion robustness** — a half-visible vial fails a cylinder
  fit but still produces a usable mask centroid.

Two cases where pure geometry *would* be worth doing later:

- If the model fails to detect a vial, a geometric cylinder fit
  near the expected slot pose is a useful fall-back.
- For rack/tray *bodies* (flat planes), classical plane fitting is
  far better than waiting for a detector. Item 9's grasp planner
  may want this for collision avoidance.

## Detection ↔ instance id contract

The seg node from exercise 07 paints the instance map with
`iid = i + 1` for the `i`-th detection. We rely on that ordering:

```python
self._classes[i + 1] = (class_id, score)        # in _on_dets
...
cls, score = self._classes.get(int(iid), ...)   # in _compute_centroids
```

If `detections.detections[]` ever gets reordered between the seg
node and this one, the labels here will be wrong. The fix would be
to publish detections inside the instance-map message itself
(`Detection3DArray` consuming a `Detection2DArray` directly), but
that requires a custom message and we are not paying that cost yet.

## Failure modes you'll see first

| Symptom                                                | Most likely cause                                                   |
|--------------------------------------------------------|---------------------------------------------------------------------|
| Centroids at `(0, 0, 0)`                               | Depth topic not bridged — node falls back to "no depth yet" path    |
| Z is constant ≈ 1.30 m for everything                  | Centroid was computed from the *camera height*, not depth — bridge is publishing range from world origin instead of from the camera; check `<pose>` block of the depth sensor |
| Centroid jumps several cm frame-to-frame               | Mask is being recomputed each frame with shuffled instance ids — verify exercise 07 is publishing stable ids per object |
| `depth shape != mask shape` warnings                   | Depth and RGB SDF blocks have different `<width>/<height>` — they must match |
| Vials behind the front row come out at wrong distance  | Side-view camera. Either move back to top-down (exercise 07's note) or accept that occluded vials need exercise 09's PCA + a second look |

## Performance

Per frame on a CPU:

- `np.unique(instance_map)` — ~1 ms for 640×480 mono8.
- `depth[pixel_mask]` plus median — ~1 ms per instance.
- 50 instances total → ~50 ms. Still well under the 30 Hz camera
  budget once the seg node (~60–100 ms) is amortised.

We do not need GPU for this step. The deprojection is four float
ops per object.
