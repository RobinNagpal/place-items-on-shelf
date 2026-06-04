# Architecture — exercise 08

This exercise is intentionally one file. Everything heavy
(detector, Gazebo, image bridge, segmentation node) is already
running from exercises 04 and 07.

```
08-depth-to-3d-centroid/
├── README.md                 # concept + the two design paths
├── ARCHITECTURE.md           # this file
├── IMPLEMENTATION_NOTES.md   # SDF snippet, design trade-offs, knobs
└── centroid_node.py          # only new code in the exercise
```

## What `centroid_node.py` owns

A single ROS 2 node `CentroidNode` (a `rclpy.node.Node`) that:

| Responsibility                          | How                                                                                        |
|-----------------------------------------|--------------------------------------------------------------------------------------------|
| Receive instance masks                  | subscribes to `/yolo_seg/instance_mask` (`sensor_msgs/Image`, `mono8`)                     |
| Receive class labels per instance       | subscribes to `/yolo_seg/detections` (`vision_msgs/Detection2DArray`)                      |
| Receive per-pixel depth                 | subscribes to `/overhead_camera/depth` (`sensor_msgs/Image`, `32FC1` in metres)            |
| Trigger one output frame per mask       | the mask callback is the publisher trigger; depth and detections are cached state          |
| Compute one 3D centroid per instance    | `_compute_centroids` — loops over `np.unique(instance_map)`                                |
| Publish results                         | `/objects/centroids` (`vision_msgs/Detection3DArray`) — one `Detection3D` per instance     |

The node holds three pieces of mutable state: `self._depth`
(latest depth ndarray), `self._classes` (latest dict of
`instance_id → (class, score)`), and the ROS publisher/subscribers.
That's it.

## Why this file does **not** reach into the Gazebo SDF

The SDF lives in exercise 04 (`worlds/autosampler_cell_with_camera.sdf`).
Item 8 needs one extra `<sensor type="depth_camera">` block; the
snippet and rationale live in `IMPLEMENTATION_NOTES.md` so future
edits to the SDF stay in one place rather than scattering between
exercises.

## Inputs / outputs at the ROS layer

```
SUBSCRIBES
   /yolo_seg/instance_mask    sensor_msgs/Image    (mono8)
   /yolo_seg/detections       vision_msgs/Detection2DArray
   /overhead_camera/depth     sensor_msgs/Image    (32FC1, metres)

PUBLISHES
   /objects/centroids         vision_msgs/Detection3DArray
       header.frame_id = camera frame from instance_mask
       detections[i].bbox.center.position = (X, Y, Z) in metres
       detections[i].results[0].hypothesis.class_id = "vial" | "cap_red" | ...
       detections[i].results[0].hypothesis.score    = passthrough from YOLO
```

## How the three streams stay in sync

We do not run a strict time synchroniser (`message_filters`):

- The depth camera is steady (30 Hz, no motion in the scene from
  the camera's perspective). Re-using the most recent depth image
  for the mask frame that just arrived is within a few ms.
- The detection and mask topics come from the same node in exercise
  07 and share a header. We assume "detection index `i` matches
  instance id `i + 1`" — the same contract the seg node honoured
  when it painted the instance map.

If you ever swap the seg node for one that does asynchronous
publishing, switch to `message_filters.ApproximateTimeSynchronizer`
across mask + detection + depth.

## What depends on what

- This node depends on **exercise 07's output topics** — change
  those topic names and update the `mask_topic` / `det_topic`
  parameters here.
- The deprojection assumes the **camera intrinsics from the SDF in
  exercise 04**. The same constants live in
  `exercises/05-score-detections-vs-gazebo/detection_scorer.py`.
  Move the camera and both files need updating.
- Downstream (item 9, grasp planning) will consume
  `/objects/centroids`. That topic name and message shape are the
  stable contract this exercise exports.
