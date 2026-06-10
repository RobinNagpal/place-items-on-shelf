# Synthetic RGB + YOLO-box dataset — Step 2 dissolution / extraction

Produces a small **RGB + YOLO-box** dataset from the
`ketchup_extraction.sdf` world. Two classes:

| id | class            | what it is in the scene                                |
|----|------------------|--------------------------------------------------------|
| 0  | `solvent_bottle` | The 500 mL water / mild-acid bottle on the bench left  |
| 1  | `beaker`         | Any of the three Pyrex 100 mL beakers on the right     |

This is the implementation of
[`docs/hplc-autosamplers/synthetic-data/types/01-rgb-boxes.md`](../../../docs/hplc-autosamplers/synthetic-data/types/01-rgb-boxes.md)
for the easiest world in the set — no vials, no fine-grained
dexterous targets, just two object types the arm needs to find
before it can pick a beaker or pour solvent.

## How it works (one paragraph)

The world's SDF now has an **overhead RGB camera** at 0.5 m above
the bench top, looking straight down, publishing 640 × 480 frames
at 30 Hz on the Gazebo Transport topic
`/overhead_camera/image_raw`. Gazebo also publishes the **true 3D
pose** of every model on
`/world/ketchup_extraction_cell/pose/info`. The `ros_gz_bridge`
parameter bridge forwards both topics into ROS 2.
`generate_dataset.py` then subscribes to both: every second it
saves the current frame to `images/frame_<N>.jpg`, projects each
tracked object's 3D bounding box into the image with a pinhole
camera model, and writes one YOLO line per box to
`labels/frame_<N>.txt`. No manual labelling — Gazebo provides the
ground truth for free.

## Requirements

- **WSL2 Ubuntu 22.04** (or native Ubuntu 22.04).
  - Windows 11 with WSLg shows GUI windows out of the box.
  - On Windows 10 WSL2 without an X server the `gz sim` GUI will
    not open, but `gz sim -s -r` (headless server, auto-run) still
    publishes camera frames. See "Headless WSL fallback" below.
- **ROS 2 Humble** — install `ros-humble-desktop`.
- **Gazebo Garden** (`gz sim`). Older Fortress (`ign gazebo`)
  also works; the bridge syntax loses the `gz.msgs.` prefix.
- `ros-humble-ros-gz-bridge` for the topic bridge.
- Python packages: `pip install -r requirements.txt`.

## Run it — three terminals

Source ROS 2 at the top of every new terminal:

```bash
source /opt/ros/humble/setup.bash
```

### Terminal 1 — start the simulator

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

Click the **play** button (▶) at the bottom-left of the Gazebo
window to start sim time. The camera does not publish frames
while sim is paused.

### Terminal 2 — bridge gz topics into ROS 2

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /overhead_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image \
    /world/ketchup_extraction_cell/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V
```

Leave this terminal running. Sanity-check the topics with:

```bash
ros2 topic list                                # both topics should be present
ros2 topic hz /overhead_camera/image_raw       # ~30 Hz
ros2 topic hz /world/ketchup_extraction_cell/pose/info   # ~250 Hz
```

### Terminal 3 — run the generator

```bash
cd ~/ros2_ws/src/place-items-on-shelf/gazebo_worlds/02-dissolution-and-extraction/synthetic_data
pip install -r requirements.txt              # one time
python3 generate_dataset.py --out ./synthetic_dataset --num-frames 50
```

After ~50 seconds the script exits. You now have:

```
synthetic_dataset/
├── images/
│   ├── frame_0000.jpg
│   ├── frame_0001.jpg
│   └── ...
└── labels/
    ├── frame_0000.txt
    ├── frame_0001.txt
    └── ...
```

Each `.txt` looks like (one line per visible model):

```
0 0.667 0.167 0.111 0.292      # solvent_bottle
1 0.084 0.700 0.077 0.117      # beaker_1
1 0.252 0.700 0.077 0.117      # beaker_2
1 0.420 0.700 0.077 0.117      # beaker_3
```

## Sanity-check one frame

Verify the boxes line up with the objects by drawing them onto the
first frame:

```bash
python3 - <<'EOF'
import cv2
img = cv2.imread("synthetic_dataset/images/frame_0000.jpg")
H, W = img.shape[:2]
NAMES = {"0": "solvent_bottle", "1": "beaker"}
with open("synthetic_dataset/labels/frame_0000.txt") as f:
    for line in f:
        cls, cx, cy, w, h = line.split()
        cx, cy, w, h = float(cx)*W, float(cy)*H, float(w)*W, float(h)*H
        x1, y1 = int(cx - w/2), int(cy - h/2)
        x2, y2 = int(cx + w/2), int(cy + h/2)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, NAMES[cls], (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
cv2.imwrite("frame_0000_annotated.jpg", img)
print("wrote frame_0000_annotated.jpg")
EOF
```

Open `frame_0000_annotated.jpg`. The green boxes should sit
tightly around the solvent bottle and the three beakers.

## Headless WSL fallback

If Gazebo's GUI does not open on your WSL setup, run the
simulator in headless mode and let it auto-play sim time:

```bash
gz sim -s -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

Terminals 2 and 3 stay exactly the same. The camera still
renders frames using OGRE2 in software / headless mode.

## Where it falls short, and what to do about it

The world is **static** — every beaker and the solvent bottle sit
at the same `<pose>` for the whole run. So 50 frames will all
look near-identical. That is fine for verifying the pipeline
works; it is **not enough variety to train a real YOLO model.**

Two cheap ways to add variety:

1. **Re-pose objects between frames.** Call
   `gz service /world/ketchup_extraction_cell/set_pose ...` with
   random offsets (e.g. ±20 mm on beaker X/Y, ±10 mm on solvent
   bottle X/Y) between saves. The current script has no flag for
   this yet — add a `--jitter` option later.
2. **Re-pose the camera.** Nudge the overhead camera ±2 cm in
   X/Y and ±2° in roll between saves. Same `set_pose` trick.

Both are left as follow-ups. This file is the minimum-viable
skeleton — capture works, projection math works, dataset layout
matches what `exercises/03-tiny-yolo/dataset.yaml` already
expects.

## File list

```
synthetic_data/
├── README.md            (this file)
├── generate_dataset.py  (the ROS 2 node)
├── dataset.yaml         (Ultralytics YOLO config)
└── requirements.txt     (extra Python deps)
```

## Related docs

- [`docs/hplc-autosamplers/synthetic-data/types/01-rgb-boxes.md`](../../../docs/hplc-autosamplers/synthetic-data/types/01-rgb-boxes.md)
  — the "what / when / who / how" spec this implements.
- [`exercises/03-tiny-yolo/`](../../../exercises/03-tiny-yolo/) —
  the YOLO trainer that this dataset feeds into.
- [`exercises/05-score-detections-vs-gazebo/detection_scorer.py`](../../../exercises/05-score-detections-vs-gazebo/detection_scorer.py)
  — same pinhole-projection math, scoring direction instead of
  labelling direction.
