# Synthetic data — Step 4: materials / textures (structured DR)

## TL;DR

- The **camera, every labelled object pose, and the lighting all
  stay fixed**.
- Every frame we paint five surfaces a fresh random colour:
  - the **bench top** (a thin coloured plane spawned on top of it)
  - the **solvent bottle** (an opaque cylinder spawned slightly
    larger than the bottle, fully obscuring the original)
  - **beaker_1**, **beaker_2**, **beaker_3** (one opaque cylinder
    wrap each)
- Colours come from a seeded RNG, sampled in HSV with high
  saturation + value so each frame is vividly different.
- After the frame is captured, every overlay is removed via
  `gz service /world/.../remove` so the next frame starts clean.
- Five frames captured by default → five "structured DR" scenarios.

This is axis #4 of the six in
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md):

| # | Axis              | Where it lives                                |
|---|-------------------|-----------------------------------------------|
| 1 | Camera pose       | `move_camera.py`                              |
| 2 | Object pose       | `randomize_objects.py`                        |
| 3 | Lighting          | `randomize_lighting.py`                       |
| 4 | Materials         | `randomize_materials.py`  **<-- this file**   |
| 5 | Distractors       | `randomize_distractors.py`                    |
| 6 | Background        | `randomize_background.py`                     |

## Why this matters — "structured DR"

Pure object-pose randomisation (axis #2) teaches a detector "an
object can be anywhere on the bench". Structured DR goes further
and teaches it "an object can be **any colour** while still being
the same class". Without this, a detector trained on white-with-
red beakers will fail on the day the lab swaps in green ones.

The classic recipe: pin every other DR axis, vary only the
*materials*, and force the detector to use **shape + size** as the
identifying signal rather than colour. Combined later with the
other axes, this is what gives a synthetic-trained YOLO model the
robustness to transfer to real photos.

## How we recolour at runtime (without editing the world SDF)

The cleanest approach in principle would be Gazebo's
`/world/<world>/material_color` topic — but that requires the
`gz::sim::systems::MaterialColor` plugin to be added to the world
SDF, and its semantics around entity-name matching change
between Garden and Harmonic. Editing the SDF for every new DR axis
gets messy.

Instead, this script uses the same `EntityFactory` spawn-and-remove
pattern as `randomize_background.py` and `randomize_distractors.py`:

- **Bench top** — spawn a thin coloured plane just above the bench
  (1 mm above, 2 mm thick). The plane's top face replaces the
  bench's wood colour for the camera's purpose.
- **Each labelled object** — spawn an opaque coloured cylinder at
  the object's world pose, with radius `original_r + 1.5 mm` and
  the full original height. The wrap is concentric with the
  original and just barely larger, so:
    1. From the overhead camera, the wrap fully hides the original
       glass / blue cap / ketchup sample.
    2. The labelled-object bbox we project (using the original
       half-extents) still matches the wrap's silhouette to within
       ~1 mm — well below YOLO label rounding.

So the YOLO labels emitted are unchanged across all 5 frames, but
the *pixels* the detector sees vary dramatically in colour.

Sources:
- [Gazebo Sim — entity creation tutorial](https://gazebosim.org/api/sim/9/entity_creation.html)
- [`gz-msgs/entity_factory.proto`](https://github.com/gazebosim/gz-msgs/blob/main/proto/gz/msgs/entity_factory.proto)

## Wrap geometry (derived once from the SDF)

| original              | wrap model name    | wrap radius   | wrap length |
|-----------------------|--------------------|---------------|-------------|
| `solvent_bottle`      | `material_bottle`  | 44.0 mm       | 175 mm      |
| `beaker_1`            | `material_beaker_1`| 26.5 mm       | 70 mm       |
| `beaker_2`            | `material_beaker_2`| 26.5 mm       | 70 mm       |
| `beaker_3`            | `material_beaker_3`| 26.5 mm       | 70 mm       |
| bench top mat         | `material_bench`   | 500×850 mm    | 2 mm thick  |

The wrap radius `original_r + WRAP_RADIUS_MARGIN_M` (1.5 mm) is
the smallest margin where Gazebo Harmonic's OGRE2 renderer
reliably hides the original surface underneath. Smaller margins
let speckles of the original colour bleed through at oblique
edges.

## Colour sampling

```python
SAT_RANGE = (0.65, 1.00)
VAL_RANGE = (0.65, 1.00)

def random_colour(rng):
    h = rng.random()
    s = rng.uniform(*SAT_RANGE)
    v = rng.uniform(*VAL_RANGE)
    return hsv_to_rgb(h, s, v)
```

Why HSV with high S+V rather than uniform RGB: a uniform RGB
sample averages to a dull grey-brown, so most frames look very
similar to the eye. Restricting saturation and value to the upper
end gives vivid colours where adjacent frames are obviously
distinct.

Each frame draws 5 independent colours — one per element. To
correlate them (e.g. always pair a warm bench with cool objects),
edit `random_colour()` to share a per-frame hue offset.

## Run it — two terminals

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

### Terminal 2 — randomise + capture

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_materials.py
```

Defaults: 5 frames, 2 s dwell, seed 0.

Sample output:

```
gz-transport Python: Harmonic (transport13 + msgs10)
subscribing to       /overhead_camera/image_raw
saving PNGs to       /home/.../captured_frames/
camera (fixed)       pos=(0.05, 0.0, 1.5)  aim=(0.05, 0.0, 0.94)
bench mat            0.5x0.85 m at z=0.901  (2.0 mm thick)  name='material_bench'
object wrap          solvent_bottle -> r=44.0 mm, len=175 mm at (+0.100, +0.250, +0.987) name='material_bottle'
object wrap                beaker_1 -> r=26.5 mm, len=70 mm at (+0.050, -0.300, +0.935) name='material_beaker_1'
...

parking camera + objects at SDF defaults ...
  set_pose overhead_camera: (+0.050, +0.000, +1.500) -> OK
  ...

[frame 00]
  bench   rgb=(0.80,0.07,0.75)
  wrap   solvent_bottle rgb=(0.43,0.79,0.14) -> OK
  wrap         beaker_1 rgb=(0.63,0.20,0.82) -> OK
  wrap         beaker_2 rgb=(0.03,0.43,0.83) -> OK
  wrap         beaker_3 rgb=(0.32,0.87,0.07) -> OK
  -> /home/.../captured_frames/frame_00.png  (640x480)  labels=4 -> frame_00.txt  overlay=4 -> overlays/frame_00_bbox.png

[frame 01]
  bench   rgb=(0.51,0.99,0.03)
  ...
```

Useful flags:

```bash
# Capture 20 frames instead of 5.
python3 .../randomize_materials.py --frames 20

# Different deterministic colour sequence.
python3 .../randomize_materials.py --seed 42

# Spend longer per pose so the renderer catches up.
python3 .../randomize_materials.py --dwell 4

# Save somewhere else.
python3 .../randomize_materials.py --out /tmp/my_materials_dataset
```

## Output layout

```
captured_frames/
├── classes.txt
├── frame_00.png
├── frame_00.txt
├── frame_01.png
├── frame_01.txt
├── ...
├── materials.jsonl       # one JSON line per frame — colours + sizes
└── overlays/
    ├── frame_00_bbox.png
    └── ...
```

`materials.jsonl` example:

```
{"frame": 0, "image": "frame_00.png",
 "bench":   {"model_name": "material_bench", "rgb": [0.80, 0.07, 0.75],
             "size": [0.5, 0.85, 0.002], "centre": [0.0, 0.0, 0.901]},
 "wraps": [
   {"slug": "solvent_bottle", "x": 0.10, "y":  0.25, "z": 0.9875,
    "radius_m": 0.044,  "length_m": 0.175, "color_rgb": [0.43, 0.79, 0.14]},
   {"slug": "beaker_1",       "x": 0.05, "y": -0.30, "z": 0.935,
    "radius_m": 0.0265, "length_m": 0.070, "color_rgb": [0.63, 0.20, 0.82]},
   ...
 ]}
```

## Tuning knobs

```python
WRAP_RADIUS_MARGIN_M = 0.0015   # extra radius over the original (1.5 mm)
SAT_RANGE = (0.65, 1.00)
VAL_RANGE = (0.65, 1.00)
# MAT_*: bench-mat plane geometry (re-used from the background script)
# WRAPS: list of (slug, model_name, world_xyz, radius, length)
```

To add a new wrapped object (e.g. once the arm is included):
1. Add a `(slug, model_name, world_xyz, radius, length)` entry to
   `WRAPS`.
2. The script automatically picks one more random colour per frame.
3. The labels are still computed from `LABELLED_OBJECTS`, so add a
   matching entry there too if the new object should be a YOLO
   class.

## Troubleshooting

- **Original glass colour bleeds through at the edges of a wrap.**
  Bump `WRAP_RADIUS_MARGIN_M` from 1.5 mm to 3 mm. The trade-off is
  the wrap silhouette starts to drift from the labelled bbox.
- **Bench mat invisible (same wood colour every frame).** See
  [`README_background.md`'s troubleshooting](README_background.md#troubleshooting)
  — the bench mat here reuses the background script's plane
  geometry, so any fix that makes the background visible
  immediately fixes the bench mat too.
- **Wraps spawn but objects still look glass-coloured in the
  overlay.** The `--dwell` is shorter than the renderer's tick
  rate. Bump it to 4 s.
- **A frame is mostly one colour.** The HSV sampler happened to
  draw nearby hues. Bump `--seed` to get a different sequence, or
  set `SAT_RANGE = (1.0, 1.0)` to maximise saturation so all
  colours are at the rim of the colour wheel.

## What's left

All six DR axes (#1–#6) now have a separate warm-up script. A real
production dataset would combine them per frame rather than running
them in isolation; the next iteration is a `combined_dr.py` that
calls every axis's setup function in one render pass.
