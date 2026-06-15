# Synthetic data — Step 3: lighting randomisation

## TL;DR

- The **camera stays put** at the overhead view.
- Every labelled object is **re-parked at its SDF default pose** at
  startup, so the geometry is identical between runs.
- Every frame, the world's `<light name="sun">` directional light is
  replaced via `gz service .../light_config` with:
  - a new **direction** (elevation 25°–80°, azimuth 0°–360°),
  - a new **diffuse colour** (warmth scalar tinted warm-red ↔ cool-blue),
  - a new **intensity** multiplier (0.45×–1.20×).
- Five frames captured by default; the YOLO labels are unchanged
  between frames (objects don't move) but are still emitted per-frame.

This is axis #3 of the six in
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md):

| # | Axis              | Where it lives                                |
|---|-------------------|-----------------------------------------------|
| 1 | Camera pose       | `move_camera.py`                              |
| 2 | Object pose       | `randomize_objects.py`                        |
| 3 | Lighting          | `randomize_lighting.py`  **<-- this file**    |
| 4 | Materials         | not yet                                       |
| 5 | Distractors       | not yet                                       |
| 6 | Background        | not yet                                       |

## How Gazebo lights can be controlled at runtime

The `UserCommands` plugin (already loaded in `ketchup_extraction.sdf`)
exposes the same service the GUI's "Light" panel uses:

```
/world/<world>/light_config   (gz.msgs.Light  ->  gz.msgs.Boolean)
```

Send a fully-populated `gz.msgs.Light` and the existing light with
the same `name` is replaced. The message fields we care about:

| Field         | Type        | What it does                                                   |
|---------------|-------------|----------------------------------------------------------------|
| `name`        | string      | Identifies which light to update (`"sun"` in our SDF).         |
| `type`        | enum        | `POINT=0`, `SPOT=1`, `DIRECTIONAL=2`.                          |
| `direction`   | Vector3d    | Unit vector the rays travel along (FROM sun TO scene).         |
| `diffuse`     | Color (rgba)| Main light colour. Most renderers multiply this with surface.  |
| `specular`    | Color (rgba)| Highlight colour. We keep it at 0.2 × diffuse.                 |
| `intensity`   | float       | Multiplier on top of diffuse. Gazebo Harmonic honours this.    |
| `range`       | float       | Effective range. SDF default = 1000 m.                         |
| `attenuation_*` | float (×3)| Falloff coefficients. SDF defaults reused.                     |
| `cast_shadows`| bool        | Re-rendered every frame regardless.                            |

We always send the full message because the service treats the
request as a *complete description* of the light — fields you omit
silently revert to their proto defaults (typically zero), which
black-out the scene the first time you try a partial update.

Source: [Gazebo Sim — Light config service](https://gazebosim.org/api/sim/9/light_config.html)
and the [`gz-msgs/light.proto`](https://github.com/gazebosim/gz-msgs/blob/main/proto/gz/msgs/light.proto)
field list.

## Run it — two terminals

Same recipe as the sibling scripts. Both terminals must be in the
repo root.

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

### Terminal 2 — randomise the lights + capture

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_lighting.py
```

Defaults: 5 frames, 2 s dwell, seed 0. So one run produces 5 PNGs.

Sample output:

```
gz-transport Python: Harmonic (transport13 + msgs10)
subscribing to       /overhead_camera/image_raw
saving PNGs to       /home/.../captured_frames/
YOLO classes file    /home/.../captured_frames/classes.txt  (2 class(es), 4 object(s))
image intrinsics     640x480  hfov=60deg  fx=554.3
camera (fixed)       pos=(0.05, 0.0, 1.5)  aim=(0.05, 0.0, 0.94)  pitch=+90deg yaw=+0deg
light service        /world/ketchup_extraction_cell/light_config  (target: 'sun')
random seed          0  (elev=(25.0, 80.0) deg, az=(0.0, 360.0) deg, ...)
bbox overlays to     /home/.../captured_frames/overlays/  (disable with --no-overlay)

parking camera + objects at SDF defaults ...
  set_pose overhead_camera: (+0.050, +0.000, +1.500) -> OK
  set_pose   solvent_bottle: (+0.100, +0.250, +0.975) yaw=+0.0deg -> OK
  set_pose         beaker_1: (+0.050, -0.300, +0.935) yaw=+0.0deg -> OK
  ...

waiting for the first frame ...
first frame received after 0.4 s (got 1 frames so far).

[frame 00]
  light  elev=+71.4deg  az= 272.9deg  warmth=-0.16  intensity=0.64  diffuse=(0.93,0.95,0.98)
  -> /home/.../captured_frames/frame_00.png  (640x480)  labels=4 -> frame_00.txt  overlay=4 -> overlays/frame_00_bbox.png

[frame 01]
  light  elev=+53.1deg  az= 145.8deg  warmth=+0.57  intensity=0.68  diffuse=(1.00,0.95,0.84)
  -> ...
...
done. saved 5 PNGs -> /home/.../captured_frames/
      per-frame lights -> /home/.../captured_frames/lights.jsonl
```

Open `overlays/frame_00_bbox.png` and `overlays/frame_03_bbox.png`
side-by-side and you should see the same objects under visibly
different lighting — different shadow angles, different white
balance, different overall brightness.

Useful flags:

```bash
# Capture 20 frames instead of 5.
python3 .../randomize_lighting.py --frames 20

# Different seed -> different (still deterministic) lighting sequence.
python3 .../randomize_lighting.py --seed 42

# Spend longer at each pose (helps if your render is slow).
python3 .../randomize_lighting.py --dwell 4

# Save somewhere else.
python3 .../randomize_lighting.py --out /tmp/my_lighting_dataset
```

## Where the images and labels land

By default: `./captured_frames/` relative to the launch directory.
After one run with defaults:

```
captured_frames/
├── classes.txt
├── frame_00.png
├── frame_00.txt
├── frame_01.png
├── frame_01.txt
├── frame_02.png
├── frame_02.txt
├── frame_03.png
├── frame_03.txt
├── frame_04.png
├── frame_04.txt
├── lights.jsonl            # one JSON line per frame — what light went where
└── overlays/
    ├── frame_00_bbox.png
    ├── frame_01_bbox.png
    ├── frame_02_bbox.png
    ├── frame_03_bbox.png
    └── frame_04_bbox.png
```

`lights.jsonl` records the exact light parameters for each frame so
the dataset is reproducible from disk:

```
{"frame": 0, "image": "frame_00.png", "light": {
    "name": "sun", "type": "DIRECTIONAL",
    "elevation_deg": 71.4, "azimuth_deg": 272.9,
    "direction": [-0.016, 0.318, -0.948],
    "warmth": -0.16, "intensity": 0.64,
    "diffuse_rgb": [0.93, 0.95, 0.98]
}}
```

## Tuning the jitter ranges

The four scalar ranges at the top of `randomize_lighting.py`
control everything:

```python
ELEVATION_DEG_RANGE = (25.0, 80.0)
AZIMUTH_DEG_RANGE   = (0.0, 360.0)
WARMTH_RANGE        = (-1.0, 1.0)
INTENSITY_RANGE     = (0.45, 1.20)
```

Rules of thumb:

- **Elevation below ~25°** lights the scene from the side, which
  produces nice long shadows but also clips half the bench in
  darkness. Useful for "early-morning" augmentation, but blow out
  too many frames here and the detector struggles to find anything.
- **Azimuth** is safe to fully randomise — what you want is for the
  shadow on every object to face a different way per frame.
- **Warmth** is a single scalar in `[-1, +1]` rather than a Kelvin
  number. The mapping in `warmth_to_rgb()` is a small linear
  approximation; swap it for a real Kelvin-to-RGB table if you
  need radiometrically-accurate temperature.
- **Intensity** above ~1.5 mostly saturates white in OGRE2's clip;
  the renderer-side tonemap doesn't help. Tune the *low* end if
  you need night scenes.

To turn one axis OFF while you debug another, set its range to
`(value, value)` so it always picks the same point.

## Why we re-park the objects at startup

This script *only* varies lighting. But if you ran
`randomize_objects.py` immediately before it, the objects in the
running sim are still wherever the last frame of that script left
them — and the YOLO labels in `LABELLED_OBJECTS` here assume the
SDF defaults. To avoid silently mis-labelling, we issue one
`set_pose` per object at startup and reset them. Skip that step
and the bboxes will float around the actual objects in the overlay.

## Troubleshooting

- **`light_config FAILED` with `Could not find requested service`.**
  Either gz sim isn't running, or its `UserCommands` plugin isn't
  loaded. Confirm with `gz service -l | grep light_config` — the
  service must appear.
- **The light changes on the *next* frame, not this one.** The
  `--dwell` value is too short for your render to catch up. Bump
  it to 4 s and the lag goes away.
- **Light updates apply but the image looks identical.** Some
  renderers cache the previous-frame shadow map. Set `--dwell` to
  >= 3 s (Gazebo recomputes shadows every render tick), or restart
  gz sim with `--render-engine ogre2` explicitly so the SDF's
  `<render_engine>` block actually takes effect.
- **`field "intensity" not found` in the request error.** Your
  `gz-msgs` is older than v10 (Harmonic). Either upgrade or delete
  the `intensity: ...` line at the bottom of
  `set_directional_light()` — diffuse-scaling alone will still
  produce a usable brightness range.
- **Black image after a few frames.** A previous request probably
  succeeded but with `intensity: 0` because a field was misspelled
  and silently dropped — the service overwrites every field on
  every call. Re-launch gz sim to reset the lighting; the script
  already sends the full message every frame.

## Next axis

Axis #4 is **materials / textures** — replace the bench colour, the
floor texture and (in "structured DR") even the object surfaces per
frame so the detector learns shape rather than colour. That requires
swapping `<material>` blocks at runtime (via the `/material_color`
service in Gazebo Harmonic, or by writing the material into a
separate `<plugin>` block). Future PR.

## Sources

- [Gazebo Sim — Light config service tutorial](https://gazebosim.org/api/sim/9/light_config.html)
- [`gz-msgs/light.proto`](https://github.com/gazebosim/gz-msgs/blob/main/proto/gz/msgs/light.proto)
