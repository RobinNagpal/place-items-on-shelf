# 06 — Tiny classifier, quantized for an edge CPU

Implements checklist item **6** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Mapped onto the same HPLC autosampler v1 cell as exercise 3 — the
same 5 classes (`vial`, `empty_slot`, `rack_edge`, `tray_edge`,
`cap_red`), but a much smaller model that runs **fast on one CPU
core** instead of needing a workstation GPU.

## What this exercise does, in plain English

Take a small neural network, train it to put each cropped image of
a vial / cap / slot / rack edge / tray edge into the right bucket,
then **shrink the model 4× and speed it up 2–3×** by converting its
numbers from 32-bit floats to 8-bit integers. The whole pipeline is
four scripts:

```
1. train.py        →  artifacts/mobilenetv3_fp32.pt    (PyTorch checkpoint)
2. export_onnx.py  →  artifacts/mobilenetv3_fp32.onnx  (portable model file)
3. quantize.py     →  artifacts/mobilenetv3_int8.onnx  (4× smaller, 2-3× faster)
4. benchmark.py    →  prints accuracy + FPS for both, PASS/FAIL on the bar
```

After running all four, you have a single ~2 MiB `.onnx` file you
could drop on a Raspberry Pi 4 sitting next to the robot. The
controller decodes a camera frame, crops the bounding box for one
vial, runs the INT8 model in a few milliseconds, and replies
`vial` or `empty_slot` — never sending a pixel off the lab network.

## Core concepts (one paragraph each)

### Classifier vs detector

A **detector** (exercise 3 / YOLOv8-nano) takes a whole image and
outputs *where* the objects are and *what* they are. A
**classifier** (this exercise) takes a single, already-cropped
image and outputs only *what* it is. Classifiers are smaller and
faster because they do not have to search the image for objects —
the detector already did that. In production they often run as a
second pass after a detector: the detector finds N candidate
regions, the tiny classifier confirms each one.

### Why MobileNetV3-Small

We use **MobileNetV3-Small** from `torchvision`. It is a 2.5 M
parameter, ~10 MB classifier designed by Google specifically for
phones and Pi-class hardware. The checklist item names MobileNet as
the classic edge option; EfficientNet-Lite and MobileViT are the
modern alternatives. We picked MobileNetV3-Small because it is in
`torchvision` out of the box (no third-party install) and is
well-supported by every ONNX runtime — fewer moving parts means
fewer things to break for someone following the exercise.

### What "quantization" means

A trained network stores millions of weights and runs millions of
multiplications. By default each number is a 32-bit float (4 bytes,
~7 decimal digits). **INT8 quantization** rewrites every weight and
every intermediate activation as an 8-bit integer (1 byte, integers
−128..127). For each tensor it also keeps two extra numbers — a
**scale** and a **zero point** — so you can convert back to float
when you need to. The math becomes integer multiply-add, which a
CPU does much faster than float multiply-add, and the model file
shrinks by ~4×. Done carefully, the accuracy drop is well under 1%.

### Static vs dynamic post-training quantization

- **Dynamic** PTQ keeps activations as floats and only quantizes
  weights. Easy to apply, but you only get part of the speedup.
- **Static** PTQ also quantizes activations. It needs a small set of
  real images (the **calibration set**) so the tool can record the
  min/max range of activations at every layer. We use static PTQ
  because the "Done when ≥ 15 FPS" bar wants all of the speedup.

### Why ONNX in the middle

ONNX (Open Neural Network Exchange) is a portable model format.
Exporting our PyTorch model to ONNX once means:

- The same file runs in ONNX Runtime (Python, C++, ARM, x86).
- Quantization is one library call (`quantize_static`) — no need to
  re-implement the math.
- The robot controller does not need PyTorch installed; just
  `onnxruntime`, which is ~30 MB instead of ~1 GB.

## Workflow

```
Cropped images (one per labeled YOLO box from exercises 3 + 5)
     ImageFolder layout under data/synthetic_autosampler_crops/
                              │
                              │  train.py
                              ▼
                MobileNetV3-Small (ImageNet weights)
                              │
                              │  fine-tune head + backbone
                              ▼
                  artifacts/mobilenetv3_fp32.pt
                              │
                              │  export_onnx.py
                              ▼
                 artifacts/mobilenetv3_fp32.onnx     (~10 MB)
                              │
                              │  quantize.py    (uses data/.../calibration/)
                              ▼
                 artifacts/mobilenetv3_int8.onnx     (~2.5 MB)
                              │
                              │  benchmark.py   (single CPU core)
                              ▼
        | model | top-1  | latency | FPS |
        | FP32  | 0.972  |  18 ms  |  55 |
        | INT8  | 0.965  |   8 ms  | 125 |
        bar FPS  >= 15  : PASS
        bar drop <= 0.02: PASS
```

Inputs and outputs at a glance:

| Step | Reads | Writes |
|------|-------|--------|
| Train | `data/.../train,val/` | `artifacts/mobilenetv3_fp32.pt`, `artifacts/training_log.txt` |
| Export | `mobilenetv3_fp32.pt` | `mobilenetv3_fp32.onnx` |
| Quantize | `mobilenetv3_fp32.onnx`, `data/.../calibration/` | `mobilenetv3_int8.onnx` |
| Benchmark | both `.onnx` files, `data/.../test/` | prints accuracy + FPS, exits 0 / 1 |

## The five classes

Same as exercise 3, but cropped to one object per image. The class
ids are different because `ImageFolder` sorts class names
alphabetically:

| id | class        | what a crop looks like |
|----|--------------|-------------------------|
| 0  | `cap_red`    | a small red disk taking up most of the frame |
| 1  | `empty_slot` | a black / dark hexagonal hole in the rack or tray |
| 2  | `rack_edge`  | a corner / outer wall of the 5×10 source rack |
| 3  | `tray_edge`  | a corner / outer wall of the 10×10 Agilent tray |
| 4  | `vial`       | a vertical glass cylinder, sometimes with a cap on top |

See [`data/README.md`](data/README.md) for the exact folder layout.

## How we measure it — what is top-1 accuracy?

Top-1 accuracy is "the model's highest-confidence prediction is
correct". The model outputs 5 logits per image, we take the
`argmax`, and we count it as right if it matches the true class id.

The checklist bar has two parts (see
[`learning-checklist.md`](../../docs/learning-checklist.md#6-tiny-classifier-quantized-for-an-edge-cpu)):

1. **INT8 throughput ≥ 15 FPS on a single CPU core.** Measured by
   pinning ONNX Runtime to one thread and timing 100 forward passes
   on a fixed dummy input.
2. **INT8 top-1 within 2% of FP32 top-1.** Both models are scored
   on the same held-out `test/` split.

`benchmark.py` prints both numbers and exits non-zero if either bar
fails, so it drops into CI later without extra wiring.

## Example run

```bash
# 1. install deps (one time)
pip install -r requirements.txt

# 2. populate data/synthetic_autosampler_crops/ in ImageFolder layout
#    (currently empty — see data/README.md for the recipe)

# 3. train
python train.py
# → artifacts/mobilenetv3_fp32.pt

# 4. export to ONNX
python export_onnx.py
# → artifacts/mobilenetv3_fp32.onnx

# 5. quantize to INT8 with calibration data
python quantize.py
# → artifacts/mobilenetv3_int8.onnx
# [quantize] size  FP32 =  9.84 MiB  INT8 =  2.53 MiB  ratio = 3.88x smaller

# 6. benchmark both
python benchmark.py
# [bench] | model | top-1   | latency (ms) | FPS    |
# [bench] | FP32  | 0.972   |        18.10 |  55.2  |
# [bench] | INT8  | 0.965   |         7.85 | 127.4  |
# [bench] bar (FPS >= 15)     : PASS   (127.4 FPS)
# [bench] bar (acc drop <= 0.02): PASS   (0.007)
```

(Numbers above are illustrative — the dataset is not generated yet.)

## What this exercise is **not**

This is a **classifier**, not a detector. It answers "is this crop a
vial?" not "where are the vials in this frame?". For the autosampler
v1 pipeline, the cheapest layout is:

1. YOLOv8-nano (exercise 3 / 4) finds N candidate boxes per frame.
2. This INT8 MobileNet re-classifies each box for extra confidence
   before the arm acts on it.

Or, even simpler if you cut the detector down to one class (just
"object here"), this classifier picks which of the 5 categories
each detection actually is.

It does **not** do any of:

| Need | Where it is solved |
|------|--------------------|
| Bounding-box localization | exercise 3 (YOLO) |
| Pixel-accurate masks | exercise 7 (instance segmentation) |
| 3D centroid | exercise 8 (depth) |
| Reading the barcode | exercise 14 |

## What's next

- Exercise 7 (instance segmentation) and exercise 8 (depth) keep
  building the perception stack; both can use this classifier as a
  fast second-pass confirmer.
- Once the autosampler controller is a real Pi 4 / Jetson Nano,
  ship `mobilenetv3_int8.onnx` alongside the YOLO `best.pt` — that
  single 2.5 MiB file is the entire classifier deployment.
