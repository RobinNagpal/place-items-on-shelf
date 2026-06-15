# Synthetic data — Step 5: distractor objects

## TL;DR

- The **camera, every labelled object and the lighting all stay
  fixed** at their SDF defaults.
- Every frame, 2-4 **unlabelled clutter items** (pens, a tape roll,
  a marker, a notebook, a stray cap, a clip) are spawned at random
  positions on the bench using
  `gz service /world/.../create` (gz.msgs.EntityFactory).
- Placements **never touch any labelled object** (a 2D rejection
  sampler enforces a `SAFETY_MARGIN_M = 0.015 m` gap).
- After the frame is captured, the distractors are removed via
  `gz service /world/.../remove` so the next frame starts clean.
- Five frames captured by default → five distinct distractor sets.

This is axis #5 of the six in
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md):

| # | Axis              | Where it lives                                |
|---|-------------------|-----------------------------------------------|
| 1 | Camera pose       | `move_camera.py`                              |
| 2 | Object pose       | `randomize_objects.py`                        |
| 3 | Lighting          | `randomize_lighting.py`                       |
| 4 | Materials         | not yet                                       |
| 5 | Distractors       | `randomize_distractors.py`  **<-- this file** |
| 6 | Background        | see `README_background.md`                    |

## What "distractor" means

The whole point of axis #5 is to teach a future detector that
**"a cylindrical thing on the bench" is not automatically a beaker**.
If every training frame only ever contains beakers + a bottle, the
detector learns to fire on any vertical cylinder. The fix is to put
shape-similar-but-wrong objects in the same scene without labelling
them. Standard published advice: 1-10 distractors per frame.

The catalogue we ship is intentionally small and lab-themed —
extend `DISTRACTOR_TYPES` in the script for more variety.

| slug      | kind     | what it represents             | footprint radius |
|-----------|----------|--------------------------------|------------------|
| `pen`     | cylinder | thin pen                       | 6 mm             |
| `marker`  | cylinder | black permanent marker         | 9 mm             |
| `tape`    | cylinder | roll of masking tape           | 35 mm            |
| `cap`     | cylinder | red bottle cap                 | 18 mm            |
| `notebook`| box      | small notebook lying flat      | ~68 mm half-diag |
| `clip`    | box      | metallic binder clip           | ~26 mm half-diag |

None of these appear in `classes.txt` or in the YOLO labels — they
only show up as **unlabelled pixels** in the image. A detector that
generalises must ignore them.

## How spawning + removing works

The world's `UserCommands` plugin (already loaded in the SDF) serves
two services we need:

```
/world/<world>/create   (gz.msgs.EntityFactory -> gz.msgs.Boolean)
/world/<world>/remove   (gz.msgs.Entity        -> gz.msgs.Boolean)
```

Per frame the script:

1. Picks N distractor types from `DISTRACTOR_TYPES` with the seeded
   RNG.
2. For each, rejection-samples an `(x, y)` on the bench until one
   is at least `footprint_r_self + footprint_r_other + SAFETY_MARGIN_M`
   away from every existing labelled object **and** every earlier
   distractor.
3. Builds a tiny inline SDF (a single `<visual>` + `<collision>`
   with the geometry block from the catalogue) and posts it via
   `EntityFactory.sdf`.
4. After the dwell, captures the frame and writes the labels (which
   are the same as every other frame because the labelled objects
   haven't moved).
5. Calls `/remove` on every spawned name so the next frame's RNG
   starts from an empty bench.

Sources:
- [Gazebo Sim — entity creation tutorial](https://gazebosim.org/api/sim/9/entity_creation.html)
- [`gz-msgs/entity_factory.proto`](https://github.com/gazebosim/gz-msgs/blob/main/proto/gz/msgs/entity_factory.proto)
- [`gz-msgs/entity.proto`](https://github.com/gazebosim/gz-msgs/blob/main/proto/gz/msgs/entity.proto)

## Run it — two terminals

Same recipe as the sibling scripts.

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

### Terminal 2 — spawn + capture + clean up

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_distractors.py
```

Defaults: 5 frames, 2-4 distractors per frame, 2 s dwell, seed 0.

Sample output:

```
gz-transport Python: Harmonic (transport13 + msgs10)
subscribing to       /overhead_camera/image_raw
saving PNGs to       /home/.../captured_frames/
distractor catalog   6 entries: pen, marker, tape, cap, notebook, clip
create service       /world/ketchup_extraction_cell/create  remove: .../remove
random seed          0  n_distractors per frame in [2, 4]

parking camera + objects at SDF defaults ...
  set_pose overhead_camera: (+0.050, +0.000, +1.500) -> OK
  ...

waiting for the first frame ...
first frame received after 0.4 s

[frame 00] target 3 distractor(s)
  spawned __distractor_00 (cap) at (+0.186, -0.011, +0.909)
  spawned __distractor_01 (pen) at (+0.167, +0.264, +0.970)
  spawned __distractor_02 (tape) at (+0.187, -0.114, +0.913)
  -> /home/.../captured_frames/frame_00.png  (640x480)  labels=4 -> frame_00.txt  overlay=4 -> overlays/frame_00_bbox.png

[frame 01] target 2 distractor(s)
  spawned __distractor_00 (notebook) at (-0.087, +0.205, +0.906)
  spawned __distractor_01 (marker) at (+0.164, +0.386, +0.965)
  -> ...
...
done. saved 5 PNGs -> /home/.../captured_frames/
      per-frame distractor placements -> /home/.../captured_frames/distractors.jsonl
```

Useful flags:

```bash
# Capture 20 frames.
python3 .../randomize_distractors.py --frames 20

# Try a denser scene (3-6 distractors per frame).
python3 .../randomize_distractors.py --n-distractors 3 6

# Different deterministic sequence.
python3 .../randomize_distractors.py --seed 42

# Spend longer per frame so the renderer catches up.
python3 .../randomize_distractors.py --dwell 4
```

## Output layout

```
captured_frames/
├── classes.txt                # 'solvent_bottle' and 'beaker' — distractors are NOT in here
├── frame_00.png
├── frame_00.txt               # 4 lines, same every frame (objects are static)
├── frame_01.png
├── frame_01.txt
├── frame_02.png ... frame_04.txt
├── distractors.jsonl          # one JSON line per frame — what distractor went where
└── overlays/
    ├── frame_00_bbox.png      # green boxes hug the labelled objects only
    ├── frame_01_bbox.png
    └── ...
```

`distractors.jsonl` makes the dataset reproducible from disk alone:

```
{"frame": 0, "image": "frame_00.png", "distractors": [
  {"slug": "cap", "x": 0.186, "y": -0.011, "z": 0.909, "footprint_r": 0.018, "color_rgb": [0.85, 0.1, 0.1]},
  {"slug": "pen", "x": 0.167, "y":  0.264, "z": 0.970, "footprint_r": 0.006, "color_rgb": [0.2, 0.2, 0.65]},
  {"slug": "tape","x": 0.187, "y": -0.114, "z": 0.913, "footprint_r": 0.035, "color_rgb": [0.85, 0.75, 0.3]}
]}
```

## Tuning knobs

```python
SAFETY_MARGIN_M = 0.015      # at least 1.5 cm of empty pixels between objects
BENCH_X_RANGE   = (-0.20, 0.20)
BENCH_Y_RANGE   = (-0.40, 0.40)
# DISTRACTOR_TYPES: add (slug, kind, geometry_block, footprint_r, z_offset, color_rgb)
```

To make the catalogue richer, drop new entries into `DISTRACTOR_TYPES`.
A new entry only needs:

- a **slug** for logging (`"screwdriver"`)
- a `kind` of `"cyl"` or `"box"` (used in the JSONL log; the geometry
  is whatever you write next)
- the `<geometry>` XML block (`<cylinder>...` or `<box>...`)
- a **footprint radius** in metres for the rejection sampler
- a **z offset** so the bottom of the object sits exactly on the bench
- an `(r, g, b)` colour in [0, 1]

## Troubleshooting

- **Every frame looks identical and the bench has no clutter.**
  gz-sim's *reserved-name* rule: any model name starting with
  double underscores (`__...`) is silently rejected by
  `/world/.../create` — the server replies `data: false` and writes
  `Error Code 3: ... is reserved` to Terminal 1's gz sim log, not
  to the Python script. Distractors here use plain names
  (`distractor_00`, `distractor_01`, ...) for that reason. If you
  rename them, keep the new names plain too.
- **Every spawn FAILs with `Could not find requested service`.**
  Either gz sim isn't running, or the `UserCommands` plugin isn't
  loaded. `gz service -l | grep create` must list
  `/world/<world>/create`.
- **`spawn FAIL` with `Could not parse SDF`.** Your gz version's SDF
  parser doesn't accept `version='1.10'`. Try `'1.9'` or `'1.8'` —
  edit `build_distractor_sdf()`.
- **The script crashes saying "no free spot found in 200 tries".**
  Either the bench is now too crowded for the requested distractor
  count, or you reduced the bench range too far. Drop
  `--n-distractors` or widen `BENCH_*_RANGE`.
- **A distractor stays around after the script exits.** A previous
  run probably crashed before cleanup. Run the script once more —
  it removes `__distractor_00..__distractor_19` at startup as a
  best-effort sweep.
- **Distractor sinks through the bench.** `<static>true</static>` is
  meant to prevent this. If you removed it, make sure the spawn
  pose has the centre at `BENCH_TOP_Z + z_offset` (object bottom
  exactly at the bench top).

## Next axis

Axis #4 — **materials / textures** — is the remaining one. That
requires either swapping `<material>` blocks at runtime via the
`/world/<world>/material_color` service in newer gz versions, or
attaching a per-frame texture map to the bench / floor. Future PR.
