# 25 — Architecture

## Folder tree

```
25-tiny-vla-inspection/
├── README.md                # high-level concept + I/O explanation
├── ARCHITECTURE.md          # this file
├── IMPLEMENTATION_NOTES.md  # design choices, trade-offs, gotchas
├── WHERE_REAL_VLAS_LIVE.md  # how to find / run OpenVLA, RT-2, pi_0
├── requirements.txt         # numpy, torch
├── vocab.py                 # 35-word fixed vocabulary + tokeniser
├── scene.py                 # synthetic workspace generator
├── tiny_vla.py              # the TinyVLA model (3 blocks)
└── inspect_vla.py           # the demo: scene + instruction -> action -> print
```

`output/` is created at runtime and contains `scene.png` and
`predictions.csv`. It is `.gitignore`'d.

## File-by-file

### `vocab.py` — instruction tokeniser

Owns the text-side input pipeline.

- **`VOCAB`** — 35 hand-listed words covering the instructions used
  in this exercise: verbs, articles, colours, object nouns,
  position nouns. Two special tokens: `<pad>` (id 0) and `<unk>`
  (id 1).
- **`tokenize(text) -> list[int]`** — lowercase, split on `[a-z]+`,
  map to ids, pad/truncate to `MAX_LEN = 12`.

Real VLAs use a learned subword tokeniser over 30 k+ tokens. The
*mechanism* (string → fixed-length integer sequence) is identical.

### `scene.py` — synthetic camera image

- **`COLOR_RGB`** — fixed RGB for red / blue / green / yellow.
- **`CubeOnTable`** dataclass — colour + pixel-space `(x, y)` of the
  cube centre + side length.
- **`Scene.render() -> np.ndarray (H, W, 3)`** — draws a grey
  tabletop with the listed cubes painted on top.
- **`three_cube_scene()`** — the canonical 3-cube scene used by
  `inspect_vla.py`.

No physics, no shadows, no perspective. The renderer exists so the
vision encoder has a *shape* of input to consume; it does not need
to be photorealistic for an inspection-only exercise.

### `tiny_vla.py` — the model

Three blocks plus a glue forward pass.

- **`TinyVisionEncoder`** — three conv layers (3 → 8 → 16 → 32
  channels), stride-2 each, ReLU, ending in
  `AdaptiveAvgPool2d(1)` and `Flatten`. Output: 32-dim vector.
- **`TinyTextEncoder`** — `nn.Embedding(vocab_size, 16)` + mean-pool
  across the sequence + linear projection. Output: 16-dim vector.
- **`TinyActionHead`** — two-layer MLP (48 → 64 → 7), ReLU between.
- **`TinyVLA.forward(image, tokens)`** — concatenate vision and
  text embeddings, feed to the head, then squash:
  - channels 0–2 (`dx`, `dy`, `dz`): `tanh * 0.05` → ±5 cm.
  - channels 3–5 (`droll`, `dpitch`, `dyaw`): `tanh * 0.3` → ±0.3 rad.
  - channel 6 (`gripper`): `sigmoid` → [0, 1].
- **`build_model(seed)`** — deterministic random init. `eval()`.

`ACTION_NAMES` (the canonical channel order) is exported as a tuple
so the inspection script doesn't have to re-list it.

### `inspect_vla.py` — the demo

- **`CHANNEL_NOTES`** — what each channel means, in one line each,
  for the printed report.
- **`save_scene_png(rgb, path)`** — writes the rendered scene to a
  PNG using only `struct` + `zlib`. Avoids pulling matplotlib in
  just for image I/O.
- **`main(instructions)`** — for each instruction:
  1. tokenise,
  2. forward through TinyVLA,
  3. print every action channel with name + value + units +
     meaning,
  4. append the row to `predictions.csv`.

`main` is invoked when the script is run directly.

## Data flow

```
scene.py ──► Scene.render()  ──► np.ndarray(96, 96, 3)  ──► tiny_vla.preprocess_image
                                                                    │
vocab.py ──► tokenize(str)   ──► list[int] of length 12  ──► tiny_vla.preprocess_text
                                                                    │
                                                                    ▼
                                                       tiny_vla.TinyVLA.forward
                                                                    │
                                                                    ▼
                                                        np.ndarray (7,)
                                                                    │
                                              ┌─────────────────────┼─────────────────────┐
                                              ▼                     ▼                     ▼
                                       stdout print          output/predictions.csv   output/scene.png
                                                                    │
                                                                    ▼
                                              [no execution — never reaches MoveIt]
```

No ROS, no MoveIt, no Gazebo — the exercise is pure
"feed-forward-and-look-at-the-output". The action vector is the
*same shape* MoveIt would consume in a real deployment, which is
the point.

## Where a real VLA would slot in

Replacing `tiny_vla.TinyVLA` with OpenVLA would mean:

- vision encoder: SigLIP / DINO ViT-Large (instead of 3 conv layers)
- text encoder: Llama-2-7B (instead of an embedding + mean-pool)
- action head: a few-layer MLP (same as ours — this part stays small)

The interface is identical: `model(image, tokens) -> action(7,)`.
Everything else in this folder — `scene.py`, `vocab.py`,
`inspect_vla.py` — would work unchanged in front of a real VLA, just
slower.
