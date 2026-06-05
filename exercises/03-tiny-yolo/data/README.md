# `data/` — where the training images go

This folder is **not** populated yet. Exercise 5 (auto-label from
Gazebo ground truth — see
[`../../../docs/learning-checklist.md`](../../../docs/learning-checklist.md))
is the planned source. The scripts in the parent folder read from
the path declared in [`../dataset.yaml`](../dataset.yaml), so as long
as the layout below is correct, the same `train.py` and
`validate.py` keep working.

## Expected layout (YOLO standard)

```
data/synthetic_autosampler/
├── images/
│   ├── train/    *.jpg     # ~160 images (80%)
│   ├── val/      *.jpg     # ~20  images (10%)
│   └── test/     *.jpg     # ~20  images (10%) — held-out, only used by validate.py
└── labels/
    ├── train/    *.txt     # one .txt per image, same stem as the .jpg
    ├── val/      *.txt
    └── test/     *.txt
```

Each `.txt` file contains **one detection per line** in normalised
YOLO format:

```
<class_id> <cx> <cy> <w> <h>
```

- `class_id` is the integer from the `names:` block in
  [`../dataset.yaml`](../dataset.yaml). 0 = `vial`, 1 = `empty_slot`,
  2 = `rack_edge`, 3 = `tray_edge`, 4 = `cap_red`.
- `cx, cy, w, h` are the bounding box centre and size as **fractions
  of image width and height**, all in `[0, 1]`.

Example `labels/train/scene_0001.txt` for an image with one vial in
the upper-left and one red cap:

```
0 0.21 0.18 0.04 0.10
4 0.21 0.13 0.03 0.03
```

## What "image" means here

For the v1 plan, every image is a single RGB frame rendered from the
overhead camera in the autosampler Gazebo world built in
[`../../01-custom-gazebo-world/`](../../01-custom-gazebo-world/). The
camera sees the bench, the 5×10 source rack on the left, and the
10×10 Agilent tray on the right.

## Why the folder is empty in git

We do not check in training images:

- Binary blobs balloon the repo.
- Synthetic data is **re-generable** at any time from the SDF world
  plus exercise 5's auto-labeller — having the recipe is enough.

A `.gitkeep` would keep this folder tracked, but the `README.md` you
are reading already does that.
