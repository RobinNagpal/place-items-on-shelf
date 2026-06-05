# Architecture — 06 Tiny classifier, quantized

## Folder tree

```
06-tiny-classifier-quantized/
├── README.md              # concept + workflow + 5-class crop layout
├── ARCHITECTURE.md        # this file
├── IMPLEMENTATION_NOTES.md# why MobileNetV3-Small, why static PTQ, trade-offs
├── requirements.txt       # torch, torchvision, onnx, onnxruntime
├── dataset.py             # ImageFolder loader + transforms + class-order check
├── train.py               # fine-tune MobileNetV3-Small head + backbone
├── export_onnx.py         # .pt -> .onnx (float32, opset 17)
├── quantize.py            # FP32 .onnx -> INT8 .onnx via static PTQ
├── benchmark.py           # accuracy + single-core FPS for FP32 and INT8
└── data/
    └── README.md          # expected ImageFolder layout (5 class subfolders × 4 splits)
```

Two artefact folders are **created at runtime** and intentionally not in git:

```
artifacts/
├── mobilenetv3_fp32.pt        # PyTorch state_dict, written by train.py
├── mobilenetv3_fp32.onnx      # written by export_onnx.py, read by quantize.py
├── mobilenetv3_int8.onnx      # written by quantize.py, read by benchmark.py
└── training_log.txt           # one epoch per line: loss, val top-1

data/synthetic_autosampler_crops/
├── train/<class>/*.jpg
├── val/<class>/*.jpg
├── test/<class>/*.jpg
└── calibration/<class>/*.jpg
```

`.gitignore` should exclude `artifacts/` and
`data/synthetic_autosampler_crops/` — both are re-generable and bulky.

## Per-file responsibility

| File | Owns |
|---|---|
| [`dataset.py`](dataset.py) | Single source of truth for the **5 class names**, their alphabetical order, and the **ImageNet normalization** the backbone expects. `build_loader(...)` is what every script calls; it also asserts the on-disk folder names match `CLASS_NAMES`. |
| [`train.py`](train.py) | Builds MobileNetV3-Small with ImageNet weights, swaps in a 5-class head, fine-tunes end-to-end with AdamW + cosine LR. Keeps the best checkpoint by val top-1. |
| [`export_onnx.py`](export_onnx.py) | Loads `mobilenetv3_fp32.pt` into the same model factory used in training, exports to opset-17 ONNX with `dynamic_axes` so batch size is not baked in. |
| [`quantize.py`](quantize.py) | Drives `onnxruntime.quantization.quantize_static`. Feeds the `calibration/` split through a `CalibrationDataReader` so activation ranges come from real images, not random noise. |
| [`benchmark.py`](benchmark.py) | Pins ONNX Runtime to **one CPU thread**, times 100 forward passes on a fixed dummy, computes top-1 on the held-out `test/` split, prints a comparison table and exits 0 only if FPS ≥ 15 and accuracy drop ≤ 0.02. |
| [`requirements.txt`](requirements.txt) | Pins `torch`, `torchvision`, `onnx`, `onnxruntime`, `numpy`, `pillow`. No `ultralytics` here — this exercise does not depend on the detector code. |
| [`data/README.md`](data/README.md) | Documents the per-class `ImageFolder` layout and where the crops are expected to come from (exercises 1 + 5). |

## How the files interact at runtime

```
                dataset.py  (CLASS_NAMES, build_loader, build_transforms)
                       │
        ┌──────────────┼─────────────────┬────────────────┐
        │              │                 │                │
        ▼              ▼                 ▼                ▼
   train.py       export_onnx.py    quantize.py      benchmark.py
   ────────       ──────────────    ───────────      ────────────
   ImageNet               loads             reads FP32 ONNX,    runs FP32 + INT8
   MobileNetV3   ─pt──►  build_model         feeds calibration  through ORT @ 1 thread,
   fine-tune              same factory        loader to onnxrt,  measures accuracy + FPS
        │                       │                    │                  │
        ▼                       ▼                    ▼                  ▼
   artifacts/                   artifacts/        artifacts/         stdout report,
   mobilenetv3_fp32.pt          mobilenetv3_fp32.onnx mobilenetv3_int8.onnx exit code
```

The handoff between scripts is **one artefact each**:

- train.py  →  `mobilenetv3_fp32.pt`
- export_onnx.py  →  `mobilenetv3_fp32.onnx`
- quantize.py  →  `mobilenetv3_int8.onnx`
- benchmark.py  →  exit code 0 / 1

## Data layout the scripts expect

```
data/synthetic_autosampler_crops/
├── train/
│   ├── cap_red/    *.jpg
│   ├── empty_slot/ *.jpg
│   ├── rack_edge/  *.jpg
│   ├── tray_edge/  *.jpg
│   └── vial/       *.jpg
├── val/
│   ├── ... (same 5 folders)
├── test/
│   ├── ... (same 5 folders)
└── calibration/
    ├── ... (same 5 folders, smaller — 25 each is plenty)
```

`dataset.py` checks the discovered folder list against `CLASS_NAMES`
and raises if it does not match. Missing folder → loud failure, not
a silently mis-labeled run.

## Dependencies (external to this folder)

- **`torch` + `torchvision`** — ImageFolder, transforms,
  MobileNetV3-Small with ImageNet weights.
- **`onnx`** — graph format; `torch.onnx.export` writes it.
- **`onnxruntime` + `onnxruntime.quantization`** — INT8 PTQ and the
  inference runtime we time against.
- **Cropped image dataset.** Not in git. Planned to be generated by
  cropping the YOLO labels produced by exercise 5.

## What this exercise does NOT touch

| Subsystem | Where it lives |
|-----------|-----------------|
| Gazebo world / camera | exercise 1 |
| YOLO detector training | exercise 3 |
| Live YOLO inference in ROS | exercise 4 |
| YOLO scoring against Gazebo GT | exercise 5 |
| Instance segmentation | exercise 7 |
| 3D centroid (depth) | exercise 8 |
| MoveIt / arm motion | exercises 18–22 |

This exercise is pure ML — Python, PyTorch under the hood, no ROS.
That isolation is on purpose: the model is **portable**. Train on a
workstation, ship one 2.5 MiB `.onnx` to the Pi, and only the
inference half (the ORT session in `benchmark.py`) runs on the
robot side.
