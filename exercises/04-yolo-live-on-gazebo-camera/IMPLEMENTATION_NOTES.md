# Implementation notes — 04 YOLO live on a Gazebo camera

## Why `vision_msgs/Detection2DArray` and not a custom message

`vision_msgs` is the **official ROS 2 standard** for object
detection / segmentation. Using it means:

- Existing ROS 2 visualisers (`rqt_image_view`, `rviz_imu_plugin`,
  custom plot panels) already know how to render it.
- Later perception items (5, 6, 7, 14) can subscribe to the same
  topic without us changing the message contract.
- We do not have to add a `msg/` folder to this exercise — no
  custom build step.

The only thing we lose vs a custom message is the temptation to
stuff arm-specific metadata in there. Good — that belongs in the
arm-control nodes, not perception.

## Why we publish the annotated image as a separate topic

Two reasons:

1. **Subscribers can pick.** Production nodes only care about
   `/yolo/detections`. Humans only care about
   `/yolo/image_annotated`. RViz subscribes to the latter; the arm
   subscribes to the former.
2. **No re-encoding for production.** Drawing boxes on the image
   costs CPU. Splitting the topics means a future "headless" mode
   can disable the overlay publisher without touching the
   detection pipeline.

The annotation comes for free from Ultralytics' `results[0].plot()`,
so the cost today is small — but the structural separation matters.

## Why we load the model in `__init__`, not the callback

Loading a `.pt` file is the slowest part of the whole pipeline
(parses the architecture, downloads weights on first use, allocates
the inference graph). Doing it once at startup means:

- The first frame is slow (~1–3 s on CPU); every subsequent frame
  is fast (~30–100 ms on CPU, single-digit ms on a modest GPU).
- We only need one set of GPU memory for the model.
- A reload bug (wrong path, corrupt file) fails the node *before*
  any subscribers connect.

The trade-off: if you want to switch checkpoints at runtime, you
need a service / re-init. That is a future addition.

## Why we use `model.predict(..., verbose=False)` instead of `model(frame)`

Both work. The differences:

- `model.predict()` accepts the explicit `conf`, `iou`, `device`,
  `verbose` kwargs we want to expose as ROS parameters. The bare
  `model(frame)` shortcut takes fewer kwargs.
- `verbose=False` silences Ultralytics' per-frame
  "0: 480x640 1 vial, …" log line. With 30 frames per second of
  that, the terminal becomes unreadable.

## Why we keep the camera frame header

Every ROS message has a `header` with a timestamp and a
`frame_id`. The detection callback copies the **incoming
image's** header into both output messages. That means:

- A subscriber asking "which Gazebo frame produced this
  detection?" has the answer (the `stamp`).
- TF lookups against `frame_id` (e.g. *"where is this box in the
  arm's base frame?"*) work out of the box once exercise 12 lays
  down the camera-to-arm transform.

Skipping the header copy is the single most common ROS 2 perception
bug — symptoms range from "everything is at time zero" to "TF
says the camera has not moved in five minutes."

## Why `qos_profile=10`, not the sensor profile

`sensor_msgs/Image` is often paired with `qos_profile_sensor_data`
(best-effort, depth 5). On modern Gazebo Sim + `ros_gz_image`,
sensor QoS reliably causes dropped frames on the bridge side. The
default reliable profile with depth 10 is more forgiving and we are
happy to drop *whole frames* under load — late detections are
worse than missing ones.

If you point the same node at a real camera publishing on the
sensor profile, change the subscription QoS to match — otherwise
`ros2 topic hz` will show data but the node will not receive
anything.

## Why a single launch file (instead of three terminals)

Earlier exercises (18 / 19 / 22) use a three-terminal pattern
because they share processes with MoveIt. This exercise has no
MoveIt — only the bridge, the detector, RViz, and Gazebo — so a
single launch file is simpler.

The launch file declares three CLI args (`weights`, `device`,
`conf`) so the same file handles both CPU and GPU runs without
edits.

## Why we resolve the SDF path twice

```python
world_path = os.path.join(get_package_share_directory(...), "..", ..., "worlds", "...")
if not os.path.exists(world_path):
    world_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "worlds", "..."))
```

`ros2 launch` runs the file out of the **installed** package
share dir (where the SDF is **not** present, because we did not
install it). The fallback path walks back to the source tree so a
fresh `colcon build` works. Once we add the SDF to `data_files` in
`setup.py`, the fallback becomes unused — but I left it because
it's cheap insurance against beginner-confusing path errors.

## Why this exercise does NOT do 3D position

A pixel bounding box is a 2D measurement of where the object
appears in the image. Turning that into a 3D world position needs
**three** pieces this exercise does not yet have:

1. **Depth per pixel** — solved by an RGB-D camera + point-cloud
   processing in item 8.
2. **Calibrated camera intrinsics** — solved in item 11.
3. **Camera → arm frame transform** — solved in item 12.

You can fake 3D positions today by assuming the vials sit at a
known z (the rack top, 0.825 m above the world). That works for
demo videos and it is the trick exercise 21's hardcoded-pose
script uses. It does **not** generalise once the rack moves.

## Failure modes you will see in practice

- **`No module named ultralytics`** — `pip install ultralytics` in
  the same Python env ROS 2 uses (usually system Python on Ubuntu
  22.04 + Jazzy, a venv on 24.04).
- **No frames on `/overhead_camera/image_raw`** — the
  `gz-sim-sensors-system` plugin block at the bottom of the SDF
  was deleted. Without it, the `<sensor>` declaration is inert.
- **Frames flow but detections topic is empty** — the YOLO node's
  conf threshold is too high, or the camera view does not contain
  anything the trained model has seen. Confirm with
  `ros2 topic echo /overhead_camera/image_raw --no-arr` (raw bytes,
  noisy — proves the frame exists).
- **RViz shows the raw image but not the overlay** — `cv_bridge`
  mismatch (the node publishes `bgr8`, RViz expects… `bgr8`, so
  this is almost always a wrong QoS or a stale RViz config).
- **YOLO is very slow** — single-digit FPS on CPU is normal for
  YOLOv8-nano at 640×480; quantised inference is item 6. Try
  `device:=0` if you have a GPU; the same launch file passes it
  through.

## Things to revisit later

- Replace `ros_gz_image` with the unified `ros_gz_bridge` config
  file when the project picks up other Gazebo topics (e.g.
  `/clock`, `/model/.../joint_state`).
- Publish a `vision_msgs/VisionInfo` message once on startup with
  the class-id-to-name map, so other nodes can decode class names
  without hardcoding the list.
- Move the detection callback into a separate executor thread so
  the subscription can keep up with the bridge while inference is
  running on the previous frame (latency hiding).
