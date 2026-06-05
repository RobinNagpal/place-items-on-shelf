# Implementation notes — 06 Tiny classifier, quantized

Engineering decisions that are not obvious from the code.

## Why MobileNetV3-Small and not something else

We picked a small, well-supported classifier with first-class
ImageNet weights and clean ONNX export. The checklist explicitly
mentions MobileNet / EfficientNet-Lite / YOLOv8-nano as candidates.

| Option | Why we passed |
|--------|---------------|
| **MobileNetV2** | Older. Same family, slightly larger and slower than V3-Small at the same accuracy. |
| **MobileNetV3-Large** | Better accuracy but ~3× more compute. We are accuracy-bound by *data*, not capacity. |
| **EfficientNet-Lite (B0–B4)** | Competitive accuracy and ONNX-friendly, but ships via `timm` or TF — adds a dep. |
| **MobileViT** | A vision transformer designed for mobile. Cool, but heavier and quantizes worse than CNNs because attention has large activation ranges. |
| **YOLOv8-nano (cls)** | Possible — Ultralytics has a classify mode. We use a different family on purpose so the exercise is not just "the same model as exercise 3 with one extra step". |
| **SqueezeNet / ShuffleNet** | Smaller still but accuracy lags MobileNetV3-Small by 3–6% on ImageNet, and tooling support is thinner. |

> Rule of thumb: pick the smallest model that clears the accuracy
> bar **and** has solid ONNX Runtime kernel coverage. INT8 only
> helps you if the runtime can actually run INT8 kernels for every
> op in your model.

## Why fine-tune from ImageNet weights

`MobileNet_V3_Small_Weights.IMAGENET1K_V1` carries 1000-class
ImageNet pretraining. We swap the final Linear for a 5-output
layer (random init) and fine-tune the **whole** network at a single
low LR — no head-only warm-up.

Reasons end-to-end fine-tuning is fine for this size of dataset:

- 5 classes, small images. The head is tiny — there is no risk of
  destroying backbone features in a few hundred steps.
- AdamW with `lr=1e-3` + cosine annealing handles both head and
  backbone gradients cleanly. A 2-phase recipe (frozen backbone
  first, then unfreeze) adds complexity for no measurable win at
  this scale.

If the dataset ever grows past ~10 k crops, switch to a 2-phase
recipe: 3 epochs head-only at `lr=1e-3`, then unfreeze the
backbone at `lr=1e-4` for 15 more epochs.

## Why static PTQ and not dynamic / QAT

Three flavours of INT8 from ONNX Runtime:

| Flavour | Activations | Calibration data | Accuracy | Speed |
|---------|-------------|------------------|----------|-------|
| **Dynamic PTQ** | computed at runtime in float, quantized on the fly | none | very close to FP32 | partial speedup (only the matmuls run INT8) |
| **Static PTQ** | recorded as INT8 with fixed scale/zero-point | ~50–200 real images | small drop (well under 1% typical) | full speedup |
| **QAT** (quantization-aware training) | fake-quantized during training | full training set | smallest drop | full speedup |

The checklist bar is "INT8 ≥ 15 FPS on one CPU core". Dynamic PTQ
often misses that on Pi-class CPUs. QAT clears it easily but is
~10× more code and requires re-running training. Static PTQ is the
"goldilocks" choice — one extra script, one extra small data split.

## Why QDQ format with `QInt8` weights + `QUInt8` activations

`QuantFormat.QDQ` inserts `Quantize`/`Dequantize` op pairs around
each weight and activation. This is the modern ONNX-Runtime default
because:

- All major Execution Providers (CPU, CUDA, NNAPI, CoreML, TensorRT)
  understand QDQ.
- The optimiser can fuse Q/DQ into the surrounding op when the
  kernel supports it, falling back to FP32 only where needed.
- The legacy `QuantFormat.QOperator` produces ops like `QLinearConv`
  that EPs without explicit INT8 support cannot run at all.

Weights as **signed** `QInt8` (range −128..127) and activations as
**unsigned** `QUInt8` (range 0..255) is the official ONNX-RT recipe
for MobileNet-class CNNs. Weights are roughly zero-centred, so a
signed range wastes no codepoints. Activations after ReLU/Hardswish
are non-negative, so an unsigned range gives twice the resolution
for the same 8 bits.

Per-tensor (`per_channel=False`) is enough for MobileNetV3-Small —
its convolutions are small enough that per-tensor scales do not
hurt accuracy. Per-channel quantization helps on larger models like
MobileNetV3-Large or ResNet-50.

## Why ImageNet normalization (and a fixed 224×224 input)

The backbone was pre-trained on ImageNet with mean
`(0.485, 0.456, 0.406)` and std `(0.229, 0.224, 0.225)` at
`224×224`. Three knock-on consequences:

1. Every image goes through `Normalize(IMAGENET_MEAN, IMAGENET_STD)`
   before the model sees it — including the calibration set, so the
   activation ranges the quantizer records are **realistic**.
2. Crops are resized to a square 224×224 with no aspect-ratio
   correction. Vials are tall cylinders, so a literal resize
   stretches them; that is intentional — augmentation already
   varies aspect ratios so the model handles it.
3. If you ever want to drop the resolution to 160×160 for more FPS,
   re-fine-tune at that size. Quantizing a model trained at 224 and
   serving at 160 collapses accuracy.

## Why single-thread, single-core for the FPS measurement

`benchmark.py` sets `intra_op_num_threads = 1` and
`inter_op_num_threads = 1` before creating the ORT session. The
checklist asks for FPS "on a single CPU core" specifically because
the autosampler controller is a Pi 4 (4 cores) or a Jetson Nano
(4 cores) — and the other 3 cores are spoken for: ROS 2, MoveIt,
the camera pipeline. The classifier gets one core.

Letting ORT use all cores would produce numbers 3–4× higher that
do not represent how the model performs on the real device.

## Why we hold out a `test` split *and* a `calibration` split

- `train` and `val` are the loop the model sees during training.
  `val` drives the "keep best checkpoint" choice.
- `calibration` is fed to the quantizer to record activation
  ranges. It must be **realistic** (drawn from the same
  distribution as deployment) but **separate** from `test`, or the
  reported accuracy number is fake.
- `test` is touched exactly once, by `benchmark.py`. That is the
  number we trust for the "Done when ≤ 2% drop" check.

Recommended split sizes for a ~1000-crop set: 80 / 10 / 10 / + 100
calibration crops drawn from train.

## Assumptions baked into the script

1. **Data root is relative to the script.** `train.py`,
   `quantize.py`, `benchmark.py` resolve `data/...` next to
   themselves. Run them from inside `exercises/06-tiny-classifier-quantized/`,
   or pass `--data-root <absolute path>`.
2. **CPU is acceptable for training.** MobileNetV3-Small on 5
   classes finishes in minutes on a CPU; GPU is faster but not
   required. `train.py` auto-picks CUDA if available, falls back
   to CPU.
3. **One image per crop, JPEG, in an `ImageFolder` layout.** Other
   formats work (PNG, BMP) but JPEG keeps the dataset small.
4. **Class-name folders are exactly the strings in `CLASS_NAMES`.**
   `dataset.py` asserts on that order so the trained model and the
   quantizer agree on which index means which class.

## Failure modes you will see in practice

- **`expected ImageFolder layout at ...` from `dataset.py`** — you
  ran the script with the data folder missing or named wrong. The
  message includes the expected path; check it matches
  `data/README.md`.
- **`class folders ... expected [...]` from `dataset.py`** — a
  class subfolder is missing or has a typo (`cap-red` vs `cap_red`).
  Fix the folder name, rerun. Never edit `CLASS_NAMES` to match the
  data — that silently re-labels the trained model.
- **`checkpoint not found` from `export_onnx.py`** — `train.py`
  did not complete (likely OOM if you tried `--batch 64` on a 4 GB
  GPU). Drop `--batch` to 16 and rerun.
- **INT8 FPS *lower* than FP32 FPS** — almost always the runtime
  fell back to FP32 kernels for some ops. Open the ONNX file in
  Netron and look for any op that is *not* wrapped in
  Quantize/Dequantize. The usual culprit is `Resize` /
  `AdaptiveAvgPool` — those run FP32 even in a quantized graph,
  but they are tiny so the speedup should survive.
- **INT8 top-1 collapses by > 5%** — calibration set is too small
  or unrepresentative. Increase `--max-calibration-images` to 256
  and rebalance so every class has at least 25 crops in
  `calibration/`.
- **Training loss diverges** — corrupt image file (Pillow cannot
  decode). The traceback names the path; remove the file or rename
  the extension.

## Why no live ROS code here

Same boundary as exercise 3. This exercise is *training and
exporting* only. Bringing the INT8 model into ROS 2 (live camera
crop → INT8 inference → publish class label) belongs in its own
node — a one-page Python file that loads
`mobilenetv3_int8.onnx` and subscribes to the YOLO detections topic
from exercise 4. Keeping that out of this folder lets you iterate
on the model offline and ship a single `.onnx` to the robot.

## Things to revisit later

- Try `EfficientNet-Lite0` (`timm`) once dataset grows past 5k
  crops. It outperforms MobileNetV3-Small on ImageNet but quantizes
  almost as cleanly.
- Add **per-channel quantization** (`per_channel=True`) once the
  dataset grows and the accuracy gap matters at the third decimal.
- Add `cap_blue` and `cap_green` once the LIMS asks for them — same
  recipe, just more folders under `data/`.
- Compile the INT8 ONNX to **ONNX Runtime ExecutionProvider** for
  the actual deployment target (`NNAPI` on Android, `CoreML` on
  iOS, `TensorRT` on Jetson) for another ~2× speedup.
- Investigate **QAT** if static PTQ ever drops more than 2% — the
  recipe is one extra training script that inserts fake-quant ops
  before the existing AdamW loop.
