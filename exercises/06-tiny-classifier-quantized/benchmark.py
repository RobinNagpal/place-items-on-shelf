"""Benchmark FP32 vs INT8 — accuracy and single-core CPU FPS.

The checklist "Done when" bar for item 6 has two parts:

    1. INT8 inference >= 15 FPS on a single CPU core.
    2. INT8 top-1 accuracy stays within 2% of the FP32 model.

This script measures both. We run each ONNX model through ONNX
Runtime with the session pinned to one thread (`intra_op_num_threads
= 1`, `inter_op_num_threads = 1`) so the numbers reflect a Pi-class
controller — not a workstation with 16 cores it would never have on
the robot.

Run:
    python benchmark.py
    python benchmark.py --warmup 20 --iters 200
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import onnxruntime as ort

from dataset import CLASS_NAMES, IMAGE_SIZE, build_loader


HERE = Path(__file__).resolve().parent
ARTIFACTS_DIR = HERE / "artifacts"
DEFAULT_FP32 = ARTIFACTS_DIR / "mobilenetv3_fp32.onnx"
DEFAULT_INT8 = ARTIFACTS_DIR / "mobilenetv3_int8.onnx"
DEFAULT_DATA_ROOT = HERE / "data" / "synthetic_autosampler_crops"

# Checklist item 6, "Done when": INT8 must hit >= 15 FPS on one CPU
# core and stay within 2% top-1 of the FP32 baseline.
MIN_FPS = 15.0
MAX_ACC_DROP = 0.02


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fp32", type=Path, default=DEFAULT_FP32,
                   help="Float32 ONNX file from export_onnx.py")
    p.add_argument("--int8", type=Path, default=DEFAULT_INT8,
                   help="INT8 ONNX file from quantize.py")
    p.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT,
                   help="ImageFolder root holding the test/ split")
    p.add_argument("--warmup", type=int, default=10,
                   help="Warm-up iterations (excluded from FPS)")
    p.add_argument("--iters", type=int, default=100,
                   help="Timed iterations on a fixed dummy input")
    return p.parse_args()


def make_session(model_path: Path) -> ort.InferenceSession:
    """ONNX Runtime session pinned to one CPU core."""
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    # Graph optimisations on — these are what makes the INT8 path
    # actually run INT8 kernels instead of falling back to FP32.
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(model_path), sess_options=options,
                                providers=["CPUExecutionProvider"])


def evaluate_accuracy(session: ort.InferenceSession, data_root: Path) -> float:
    """Top-1 accuracy on the held-out test split."""
    loader = build_loader(data_root, "test", batch_size=1, num_workers=0,
                          shuffle=False)
    input_name = session.get_inputs()[0].name

    correct = 0
    total = 0
    for images, labels in loader:
        outputs = session.run(None, {input_name: images.numpy().astype(np.float32)})
        pred = int(np.argmax(outputs[0], axis=1)[0])
        correct += int(pred == int(labels.item()))
        total += 1
    return correct / max(total, 1)


def measure_fps(session: ort.InferenceSession, warmup: int, iters: int) -> Tuple[float, float]:
    """Return `(fps, mean_latency_ms)` on a fixed dummy input."""
    input_name = session.get_inputs()[0].name
    dummy = np.zeros((1, 3, IMAGE_SIZE, IMAGE_SIZE), dtype=np.float32)

    # Warm-up: first call also lazy-allocates kernels; do not time it.
    for _ in range(warmup):
        session.run(None, {input_name: dummy})

    start = time.perf_counter()
    for _ in range(iters):
        session.run(None, {input_name: dummy})
    elapsed = time.perf_counter() - start

    mean_ms = (elapsed / iters) * 1000.0
    fps = iters / elapsed
    return fps, mean_ms


def main() -> int:
    args = parse_args()

    for path in (args.fp32, args.int8):
        if not path.exists():
            print(f"[bench] missing ONNX file: {path}")
            print("[bench] run train.py -> export_onnx.py -> quantize.py first")
            return 2

    print("[bench] thread pinning: intra=1, inter=1 (single CPU core)")
    print(f"[bench] input shape   : 1x3x{IMAGE_SIZE}x{IMAGE_SIZE}")
    print(f"[bench] classes       : {list(CLASS_NAMES)}")
    print()

    fp32_session = make_session(args.fp32)
    int8_session = make_session(args.int8)

    print("[bench] measuring FPS ...")
    fp32_fps, fp32_ms = measure_fps(fp32_session, args.warmup, args.iters)
    int8_fps, int8_ms = measure_fps(int8_session, args.warmup, args.iters)

    print("[bench] evaluating accuracy on test/ ...")
    fp32_acc = evaluate_accuracy(fp32_session, args.data_root)
    int8_acc = evaluate_accuracy(int8_session, args.data_root)

    acc_drop = fp32_acc - int8_acc

    print()
    print("[bench] | model | top-1   | latency (ms) | FPS    |")
    print("[bench] |-------|---------|--------------|--------|")
    print(f"[bench] | FP32  | {fp32_acc:6.3f}  | {fp32_ms:10.2f}   | {fp32_fps:5.1f}  |")
    print(f"[bench] | INT8  | {int8_acc:6.3f}  | {int8_ms:10.2f}   | {int8_fps:5.1f}  |")
    print(f"[bench] speedup INT8 / FP32 = {fp32_ms / max(int8_ms, 1e-9):.2f}x")
    print(f"[bench] accuracy drop FP32 -> INT8 = {acc_drop:.3f}")
    print()

    bar_fps = int8_fps >= MIN_FPS
    bar_acc = acc_drop <= MAX_ACC_DROP

    print(f"[bench] bar (FPS >= {MIN_FPS:.0f})    : {'PASS' if bar_fps else 'FAIL'}"
          f"   ({int8_fps:.1f} FPS)")
    print(f"[bench] bar (acc drop <= {MAX_ACC_DROP:.2f}): {'PASS' if bar_acc else 'FAIL'}"
          f"   ({acc_drop:.3f})")

    return 0 if (bar_fps and bar_acc) else 1


if __name__ == "__main__":
    raise SystemExit(main())
