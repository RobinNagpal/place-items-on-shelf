# Architecture — 07 Instance segmentation

## Folder tree

```
07-instance-segmentation/
├── README.md
├── ARCHITECTURE.md          # this file
├── IMPLEMENTATION_NOTES.md
└── seg_node.py              # the only new code
```

Same pattern as exercise 05: ship just the new node + docs. The
world, the image bridge, and the ROS package layout from exercise 04
are reused as-is.

## Per-file responsibility

| File | Owns |
|---|---|
| [`seg_node.py`](seg_node.py) | The whole new node. Loads a YOLOv8-seg `.pt`, subscribes to the same image topic exercise 04 already publishes (`/overhead_camera/image_raw`), runs `model.predict()` per frame, and publishes three outputs: a `Detection2DArray` of bounding boxes, an `Image` (mono8) instance map where each pixel value is the instance id, and an `Image` (bgr8) frame with the masks drawn translucently. |

## What we reuse from exercise 04

| From `04-yolo-live-on-gazebo-camera/`                       | Used here as                                |
|--------------------------------------------------------------|---------------------------------------------|
| `worlds/autosampler_cell_with_camera.sdf`                    | The world Gazebo Sim renders.               |
| `yolo_live_demo/launch/yolo_live.launch.py`                  | Starts Gazebo + `ros_gz_image` bridge. We do not need the detector node from that launch (it will run alongside happily, on a separate output topic — they do not conflict). |
| `/overhead_camera/image_raw` (`sensor_msgs/Image`)           | Subscription input.                         |

## What we add on top

```
                /overhead_camera/image_raw
                          │
                          ▼
                     seg_node
                          │
              ┌───────────┼───────────────────────────────┐
              ▼           ▼                               ▼
   /yolo_seg/detections   /yolo_seg/instance_mask    /yolo_seg/image_annotated
   (Detection2DArray)     (Image, mono8, pixel=iid)  (Image, bgr8, overlay)
```

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/overhead_camera/image_raw` | `sensor_msgs/Image` | bridge → this node | 640×480 BGR camera frames |
| `/yolo_seg/detections` | `vision_msgs/Detection2DArray` | this node → anyone | Per-frame bboxes + class + confidence (same shape as exercise 04). |
| `/yolo_seg/instance_mask` | `sensor_msgs/Image` (mono8) | this node → anyone | Single-channel image, pixel value = instance id (0 = background, 1..254 = detections, capped). |
| `/yolo_seg/image_annotated` | `sensor_msgs/Image` (bgr8) | this node → RViz | Frame with translucent masks drawn by Ultralytics' `.plot()`. |

## Why three output topics instead of one fat custom message

ROS has no off-the-shelf "detection + mask" message. The choices
were:

| Option                                  | Why we passed                                              |
|-----------------------------------------|------------------------------------------------------------|
| Custom `msg/SegmentedDetection.msg`     | Requires a new `msg/` folder, a new `colcon build`, and downstream subscribers have to depend on a custom message — overkill for an exercise. |
| One image with masks baked in           | Loses class + confidence information per instance.         |
| **Three topics: bboxes + instance map + overlay** | Each subscriber takes only what it needs. The exercise-05 style scorer reads `instance_map == i` and the matching `detections[i-1]`. RViz only reads the overlay. |

The price is one numpy comparison on the subscriber side. Cheap.

## Why we ignore the `Detection2DArray.results` "list of masks" field

`vision_msgs/Detection2DArray` does not carry mask data. Some
projects fork `vision_msgs` with a `mask` field added to
`Detection2D`. We do not — the instance-map pattern above is
simpler and keeps the message standard.
