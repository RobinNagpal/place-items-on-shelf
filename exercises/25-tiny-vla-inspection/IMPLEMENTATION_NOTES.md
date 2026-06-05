# 25 — Implementation notes

## Why a stand-in instead of OpenVLA

OpenVLA is the smallest "real" open VLA at the time of writing. It
is **7 billion** parameters and ~14 GB of weights to download. It
requires a 24 GB GPU to run inference at reasonable latency, and
the SigLIP + Llama backbones it depends on are themselves big
downloads.

The checklist task is *inspection*:

> "log the predicted 7-DoF action — do **not** execute it"
> "Done when you can explain what each output channel means and
>  how it maps to your arm's action space."

That goal is served by **showing the I/O shape and channel meaning
of a VLA, with confidence that the meaning is correct.** It is not
served by burning an hour downloading weights and another hour
making CUDA happy.

So we built TinyVLA: same three-block architecture, same 7-DoF
action space, same final squashing convention, ~7 **million** times
smaller. The numbers it produces are not learned; the *channels*
they live in are exactly right.

If you want to run a real VLA, see
[`WHERE_REAL_VLAS_LIVE.md`](WHERE_REAL_VLAS_LIVE.md). The inspection
script `inspect_vla.py` can be repointed at OpenVLA with about ten
lines of change (call its `predict_action` instead of TinyVLA's
forward pass) — but it will still print the same 7 channels with
the same names.

## Why ~10k parameters and not 100k or 1k

Three constraints:

- **Big enough** to demonstrate the three-block architecture
  faithfully. 1 k parameters can't fit a real conv-net feature
  extractor.
- **Small enough** to load and run instantly on any CPU, with no
  pretraining required. 100 k+ would start to depend on careful init.
- **Honest** about being a stand-in. A 10 M-parameter model
  randomly initialised would look like it could do something
  useful; a 10 k-parameter one obviously can't.

10 871 parameters is exactly enough to show all three blocks and
nothing more.

## Why the action squashing happens in the model

OpenVLA, RT-2, and π0 all squash their action outputs into a fixed
physical range — typically `tanh` for translations and rotations,
`sigmoid` for the gripper. This is so the model's raw logits never
produce a 5-metre arm jump.

We do the same:

```python
action[..., 0:3] = torch.tanh(raw[..., 0:3]) * 0.05      # dx, dy, dz
action[..., 3:6] = torch.tanh(raw[..., 3:6]) * 0.3       # droll, dpitch, dyaw
action[..., 6]   = torch.sigmoid(raw[..., 6])             # gripper
```

The `0.05` and `0.3` constants are the per-step deltas the model
*could* produce, not what it *would* produce after training. They
are picked so that, even with random weights, the predicted action
is in a physically plausible range you could safely talk about
executing.

## Why deterministic random init

`build_model(seed=0)` calls `torch.manual_seed(0)` before
constructing the model. This makes the output bit-stable across
runs. Two readers of the exercise will see the same numbers, the
docs can quote specific values, the CSV can be diffed.

If you change the seed and re-run, **the channel meanings stay the
same** — only the numerical values change. That is exactly the
property a real, trained VLA has (different checkpoints produce
different values, same channels).

## Why a 35-word vocabulary

Big enough to tokenise every instruction the script tries; small
enough to fit on screen. A real VLA uses a tokeniser inherited from
its language-model backbone (Llama's 32 k tokens for OpenVLA). The
mechanism — string → fixed-length integer sequence — is identical;
the size differs by 3 orders of magnitude.

Words outside the vocabulary map to `<unk>`. The tokeniser is
case-insensitive and ignores punctuation. That covers the simple
instructions in this exercise; for a real cell you'd use a real
tokeniser.

## Why we don't pull in `transformers` or HuggingFace

Two reasons:

- The point of the exercise is **understanding** the shape of a VLA,
  not running one. Adding HuggingFace masks the architecture
  behind `AutoModel.from_pretrained`.
- The dependency is heavy (~1 GB once SigLIP and a tokeniser are
  pulled in) and slow to install in CI / on a fresh laptop.

`WHERE_REAL_VLAS_LIVE.md` covers HuggingFace pointers if you do
want to swap in the real thing.

## Why a custom PNG writer instead of matplotlib

Matplotlib pulls in ~25 MB of extra dependencies just to write one
PNG. The PNG file format is small enough to encode by hand in
20 lines of `struct` + `zlib`, which is what
`inspect_vla.save_scene_png` does. The output is byte-identical to
what any standard tool would write.

This is the kind of micro-decision that keeps the exercise's
install footprint to "numpy + torch" and nothing else.

## Assumptions and failure modes

| Assumption | What breaks if it's wrong |
|---|---|
| Action space is 7-DoF `(dx, dy, dz, droll, dpitch, dyaw, gripper)` | true for OpenVLA and most modern VLAs; π0 and others may differ — check the model card before copying our channel notes |
| Translations and rotations are **deltas**, not absolutes | some older policies output absolute targets; check the model card |
| End-effector frame is the model's reference | varies between models — RT-2 vs OpenVLA differ slightly |
| Gripper channel is normalised [0, 1] | true for OpenVLA; some models use a binary {0, 1} |

In an inspection setting, getting the assumptions *wrong* matters a
lot — that's why the channel notes in `inspect_vla.py` and this file
are explicit. A real deployment would also include a calibration
script that runs the VLA on a few known scenes and confirms the
output sits in the documented ranges.

## Debugging tips

- **Model outputs are constant across instructions** → the text
  embedding is being swamped by the image embedding. Confirm by
  running with the same image and different instructions; if
  outputs barely change, the text branch is under-weighted. A real
  trained VLA solves this with bigger language-model capacity; the
  tiny untrained version cannot.
- **The CSV has more columns than expected** → check `ACTION_NAMES`
  in `tiny_vla.py`. Order of channels is the source of truth.
- **Scene image looks empty** → `Scene.render` paints cubes at
  integer pixel coordinates. If a cube's coordinates are off the
  edge of the image it silently won't be drawn. Add an assertion in
  `Scene.__init__` to guard.
- **You want to plug in a real VLA** → the only function to replace
  is `model(...)` in `inspect_vla.main`. Everything else
  (tokenisation, image rendering, CSV writing) stays the same.
