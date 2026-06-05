# `data/` — where the cropped object images go

This folder is **not** populated yet. Each image here is one
**cropped** bounding box from the synthetic Gazebo frames produced
by exercises 1 + 5, sliced to the box and saved as a small `.jpg`.

We use **classifier-style** data (one folder per class), not
detector-style data (whole-frame images with YOLO label files).
The model in this exercise only has to answer "what is this crop?",
not "where is it in the frame?".

## Expected layout (`torchvision.datasets.ImageFolder` standard)

```
data/synthetic_autosampler_crops/
├── train/
│   ├── cap_red/      *.jpg   # ~160 crops
│   ├── empty_slot/   *.jpg
│   ├── rack_edge/    *.jpg
│   ├── tray_edge/    *.jpg
│   └── vial/         *.jpg
├── val/
│   ├── cap_red/      *.jpg   # ~20 crops
│   └── ...
├── test/
│   ├── cap_red/      *.jpg   # ~20 crops — only used by benchmark.py
│   └── ...
└── calibration/
    ├── cap_red/      *.jpg   # ~25 crops, sampled from train/
    └── ...
```

ImageFolder reads the **class names** from the subfolder names and
assigns integer ids in alphabetical order:

```
0 = cap_red
1 = empty_slot
2 = rack_edge
3 = tray_edge
4 = vial
```

Keep the subfolder names exactly the strings above. `dataset.py`
asserts on this order — renaming a folder will fail loudly rather
than silently misclassify.

## Where the crops come from

For the v1 plan, every crop is a sub-rectangle of a frame rendered
by the overhead camera in
[`../../01-custom-gazebo-world/`](../../01-custom-gazebo-world/),
sliced according to the YOLO labels produced by
[`../../05-score-detections-vs-gazebo/`](../../05-score-detections-vs-gazebo/).

A one-shot helper script (planned, not in this exercise) walks
`exercises/03-tiny-yolo/data/synthetic_autosampler/`, reads each
`.txt` label, and writes the cropped boxes to the layout above.

## Why a separate `calibration/` split

Static INT8 quantization needs ~50–200 **real** images to record
activation ranges at every layer. Reusing `train/` for that would
work but pollutes timing comparisons later — keeping a small,
representative `calibration/` slice (drawn from `train/`, never from
`test/`) keeps the test split untouched, which is the only way the
accuracy bar means anything.

## Why the folder is empty in git

Same reasons as exercise 3:

- Binary blobs balloon the repo.
- Synthetic crops are **re-generable** from the SDF world plus the
  exercise 5 labels — the recipe is what matters.

The `README.md` you are reading keeps this folder tracked without
adding a `.gitkeep`.
