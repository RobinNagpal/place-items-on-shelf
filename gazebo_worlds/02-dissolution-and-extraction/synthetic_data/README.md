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

### Terminal 3 — install deps + run the generator

Ubuntu 24.04 ships Python 3.12 with **PEP 668** turned on, which
blocks `pip install` into the system Python. Pick **one** of these
three install paths:

```bash
# Path A — recommended. Use apt; no pip needed at all.
sudo apt install -y python3-opencv python3-numpy

# Path B — venv that still sees the system ROS 2 packages
# (rclpy, cv_bridge, sensor_msgs). Use this if you want to keep
# python3-opencv off the system.
cd ~/ros2_ws/src/place-items-on-shelf/gazebo_worlds/02-dissolution-and-extraction/synthetic_data
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt

# Path C — override PEP 668. Only do this if you know what you're
# doing; it mixes apt-managed and pip-managed packages.
pip install --break-system-packages -r requirements.txt
```

Then run the generator:

```bash
cd ~/ros2_ws/src/place-items-on-shelf/gazebo_worlds/02-dissolution-and-extraction/synthetic_data

# Recommended: --jitter so the frames are not all identical.
python3 generate_dataset.py --out ./synthetic_dataset --num-frames 50 --jitter
```

`--jitter` teleports every tracked object (beakers, solvent bottle)
and the camera to small random offsets before each save, using
`gz service /world/.../set_pose`. Defaults:

- objects: ±20 mm in X/Y, ±20° yaw
- camera: ±50 mm in X/Y (Z and the straight-down pitch stay fixed)

Drop `--jitter` to capture the canonical scene only (useful for a
quick sanity check that the bridge is working).

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

## Adding more variety

`--jitter` already shuffles object X/Y/yaw and camera X/Y. To go
further:

1. **Wider object jitter.** Edit `OBJ_JITTER_XY`, `OBJ_JITTER_YAW`,
   `CAM_JITTER_XY` at the top of `generate_dataset.py`. Anything
   above ±40 mm risks beakers falling off the bench — bump the
   bench size in the SDF if you want larger jitter.
2. **Tilted camera angles.** The current camera always looks
   straight down so the pinhole projection stays a one-liner.
   To capture oblique views, replace `project_point` with
   `cv2.projectPoints` and a proper extrinsic matrix, then jitter
   the camera's roll / pitch / yaw in addition to its X / Y.
   Left as a follow-up.
3. **Lighting and material randomisation.** Vary the `<light>`
   direction and intensity, swap material textures between
   captures. Done by editing the SDF before each `gz sim` run, or
   by calling `gz service` on the light entity.

## Verifying the camera is publishing

The camera shows up in the world as a small dark-grey **5 cm cube
floating 0.6 m above the bench**. That cube is just a marker — a
Gazebo `<sensor>` on its own renders nothing in the GUI, so without
the cube the camera would be invisible. The sensor publishes frames
whether the marker is there or not.

To check frames are actually flowing:

```bash
# rate should be ~30 Hz once gz sim is playing
ros2 topic hz /overhead_camera/image_raw

# live preview of what the camera sees (apt: ros-humble-rqt-image-view)
ros2 run rqt_image_view rqt_image_view /overhead_camera/image_raw
```

## Troubleshooting

- **Gazebo window opens blank, no objects.** Old version of this
  SDF added one `<plugin>` tag and broke Gazebo's auto-loaded
  default plugins. The current SDF declares all four required
  plugins (Physics, UserCommands, SceneBroadcaster, Sensors)
  explicitly, so pull the latest world file.
- **`pip install` fails with `externally-managed-environment`.**
  Ubuntu 24.04's PEP 668 lock. Use one of the three install paths
  above — `sudo apt install python3-opencv python3-numpy` is the
  simplest.
- **No visible camera in the GUI.** The camera is the small dark
  cube floating 0.6 m above the bench centre. If you do not see
  it, pull the latest SDF — earlier versions had a sensor with no
  visual.
- **`/overhead_camera/image_raw` exists but `ros2 topic hz` shows
  0 Hz.** Sim is paused. Click ▶ in the Gazebo GUI, or relaunch
  with `gz sim -r ...` to auto-run.
- **`gz service set_pose` calls hang or print "service call
  timed out".** The UserCommands plugin is not loaded. Same
  fix — pull the latest SDF.
- **Boxes look offset from the objects in the annotated frame.**
  The camera intrinsics in `generate_dataset.py` (IMG_W, IMG_H,
  HFOV, NOMINAL_CAM) are out of sync with the `<sensor type="camera">`
  tag in the SDF. Keep them aligned.

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
