# Synthetic data — Step 6: background randomisation

## TL;DR

- The **camera, every labelled object and the lighting all stay
  fixed**.
- Every frame, a thin coloured plane is spawned just above the
  bench top via `gz service /world/.../create` — visually replacing
  the bench's wood colour with a different "tablecloth" each frame.
- Five backgrounds: **white paper, black mat, blue lab mat, green
  cut mat, grey rubber**.
- After capture, the plane is removed via `/remove` so the next
  frame can spawn a different colour.
- One frame per background by default (five frames total).

This is axis #6 of the six in
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md):

| # | Axis              | Where it lives                                |
|---|-------------------|-----------------------------------------------|
| 1 | Camera pose       | `move_camera.py`                              |
| 2 | Object pose       | `randomize_objects.py`                        |
| 3 | Lighting          | `randomize_lighting.py`                       |
| 4 | Materials         | not yet                                       |
| 5 | Distractors       | `randomize_distractors.py`                    |
| 6 | Background        | `randomize_background.py`  **<-- this file**  |

## Why a background plane (and not editing the bench material)

In principle we could call `/world/<world>/material_color` on the
existing bench visual and recolour it directly. That works on
Gazebo Harmonic, but the service isn't in older releases and the
semantics around `<material>` block lookup are version-specific.

Spawning a thin coloured **plane on top of the bench** is portable
across every gz release that ships `UserCommands` (Garden and later)
and uses the same `EntityFactory` plumbing as `randomize_distractors.py`.
From the overhead camera the plane fully fills the bench area — you
never see the wood beneath it — and the labelled objects poke up
through it because they're 3-9 cm tall and the plane is 2 mm thick.

Sources:
- [Gazebo Sim — entity creation tutorial](https://gazebosim.org/api/sim/9/entity_creation.html)
- [`gz-msgs/entity_factory.proto`](https://github.com/gazebosim/gz-msgs/blob/main/proto/gz/msgs/entity_factory.proto)

## The five backgrounds

```python
BACKGROUNDS = [
    ("white_paper",  (0.93, 0.93, 0.93)),   # A4 paper / printer sheet
    ("black_mat",    (0.05, 0.05, 0.05)),   # anti-glare absorbing mat
    ("blue_labmat",  (0.15, 0.30, 0.65)),   # blue lab / anti-static mat
    ("green_cutmat", (0.12, 0.45, 0.22)),   # green cutting / chroma mat
    ("grey_rubber",  (0.40, 0.40, 0.40)),   # neutral grey rubber mat
]
```

These five were chosen to span the colour space typical of real
lab benches:

- **white_paper** — high reflectance, near-white. Tests whether the
  detector relies on dark-vs-light contrast.
- **black_mat** — low reflectance, near-black. The opposite test;
  also stress-tests shadow handling.
- **blue_labmat** — a colour the labelled objects don't share
  anywhere, so the detector can't memorise "blue means background".
- **green_cutmat** — close to chroma-key green, common in CV
  augmentation pipelines.
- **grey_rubber** — neutral middle tone; a control case.

Order is fixed (frame 0 = white, frame 1 = black, …) unless you
pass `--seed`, which shuffles deterministically.

## How it sits in the world

```
                       ┌─── solvent_bottle, beakers (rigid, on bench)
                       │
   z=1.075 ────────────┴─── (top of solvent_bottle cap)
   z=0.970  ────── (top of beaker)
   z=0.902  ── plane top  ◄── 2 mm thick coloured box, spawned per frame
   z=0.901  ── plane bot
   z=0.900  ▓▓▓ bench top (wood)
```

The plane centre sits at `BENCH_TOP_Z + 0.001 = 0.901 m`. The plane
is `0.50 × 0.85 × 0.002 m` — slightly smaller than the bench top
(`~0.54 × 0.94`) so the bench edge still frames the shot.

The labelled objects' bottoms are at `z = 0.900` — the plane's
bottom is just *above* that, so the objects' 2 mm-tall base ring
clips through the plane. From the overhead camera you don't see it
because the cylinders are wider than the clip region.

## Run it — two terminals

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

### Terminal 2 — swap backgrounds + capture

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_background.py
```

Defaults: 5 frames (one per background), 2 s dwell.

Sample output:

```
gz-transport Python: Harmonic (transport13 + msgs10)
subscribing to       /overhead_camera/image_raw
saving PNGs to       /home/.../captured_frames/
camera (fixed)       pos=(0.05, 0.0, 1.5)  aim=(0.05, 0.0, 0.94)
background plane     0.5x0.85 m at z=0.901  (2.0 mm thick)
create service       /world/ketchup_extraction_cell/create  remove: .../remove
backgrounds          ['white_paper', 'black_mat', 'blue_labmat', 'green_cutmat', 'grey_rubber']

parking camera + objects at SDF defaults ...
  set_pose overhead_camera: (+0.050, +0.000, +1.500) -> OK
  ...

waiting for the first frame ...
first frame received after 0.4 s

[frame 00] background = white_paper  rgb=(0.93,0.93,0.93)
  -> /home/.../captured_frames/frame_00.png  (640x480)  labels=4 -> frame_00.txt  overlay=4 -> overlays/frame_00_bbox.png

[frame 01] background = black_mat    rgb=(0.05,0.05,0.05)
  -> ...

...
done. saved 5 PNGs -> /home/.../captured_frames/
      per-frame backgrounds -> /home/.../captured_frames/backgrounds.jsonl
```

Useful flags:

```bash
# Different shuffle order.
python3 .../randomize_background.py --seed 42

# Capture only the first 3 backgrounds in the list.
python3 .../randomize_background.py --frames 3

# Slower render — give the renderer more time.
python3 .../randomize_background.py --dwell 4
```

## Output layout

```
captured_frames/
├── classes.txt
├── frame_00.png       # bench under white paper
├── frame_00.txt       # same labels as every other frame here
├── frame_01.png       # bench under black mat
├── frame_01.txt
├── frame_02.png       # blue lab mat
├── frame_02.txt
├── frame_03.png       # green cut mat
├── frame_03.txt
├── frame_04.png       # grey rubber mat
├── frame_04.txt
├── backgrounds.jsonl  # one JSON line per frame
└── overlays/
    ├── frame_00_bbox.png
    ├── ...
    └── frame_04_bbox.png
```

`backgrounds.jsonl` example:

```
{"frame": 0, "image": "frame_00.png", "background": {
    "slug": "white_paper",
    "rgb": [0.93, 0.93, 0.93],
    "model_name": "__bench_background_plane__",
    "size": [0.5, 0.85, 0.002],
    "centre": [0.0, 0.0, 0.901]
}}
```

## Adding more backgrounds

Just append to `BACKGROUNDS` — the script will use them whenever
`--frames` is large enough. Some easy wins:

```python
("red_felt",     (0.55, 0.10, 0.10)),
("yellow_paper", (0.95, 0.85, 0.15)),
("brown_kraft",  (0.50, 0.35, 0.20)),
("teal_silicone",(0.10, 0.55, 0.55)),
```

For real photographic textures you'd need to:

1. Drop a PNG/JPG into a folder the gz resource path knows about
   (`GZ_SIM_RESOURCE_PATH`).
2. Replace the `<material><ambient>...<diffuse>...</material>`
   block in `build_background_sdf()` with a `<pbr><metal><albedo_map>`
   pointing at that file.

That's straightforward but adds an asset dependency we don't have
in this minimal warm-up.

## Troubleshooting

- **`spawn FAIL: Could not parse SDF`.** Older gz versions only
  accept `<sdf version='1.9'>` or earlier. Edit
  `build_background_sdf()` to drop the version number.
- **Background flashes black for one frame.** The renderer didn't
  finish before the dwell elapsed. Bump `--dwell` from 2 to 4 s.
- **Plane is visible but objects disappear under it.** The plane
  thickness was set too high so the object bottoms are clipped.
  Lower `PLANE_THICKNESS` or raise `PLANE_Z` very slightly (no
  more than 1-2 mm, or the objects appear to float).
- **Background plane lingers after the script exits.** The script
  removes the plane on the last frame; if it crashed mid-run, the
  next invocation removes the previous plane on startup. Worst
  case, hit the GUI's "Delete" button on the model called
  `__bench_background_plane__`.
- **The camera now sees ONLY the plane (no objects).** The plane
  was spawned at the wrong z and is above the object tops. Reset
  by editing `PLANE_Z` back to `BENCH_TOP_Z + 0.001`.

## Next axis (axis #4 — materials)

The remaining axis swaps the **material on existing objects** —
recolouring the beakers, the bench, the solvent bottle every
frame — using either the `/material_color` service (Harmonic+) or
by rewriting the `<material>` block inline via `/world/.../create`
with `replace_existing` semantics. Future PR.
