"""Quantize the float32 ONNX classifier to INT8.

We use **static post-training quantization** (PTQ) from ONNX Runtime:
the script feeds a small "calibration" set of real images through
the FP32 model, records the min/max activations at every layer, then
rewrites the graph with INT8 ops and per-tensor scale/zero-point
constants.

Static PTQ keeps activations as integers throughout the network
(faster than dynamic PTQ, which keeps activations float). MobileNetV3
tolerates static PTQ well because it does not have the kind of long
residual chains that amplify quantization error.

Run:
    python quantize.py
    python quantize.py --max-calibration-images 200

Outputs:
    artifacts/mobilenetv3_int8.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator

import numpy as np
from onnxruntime.quantization import (
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    quantize_static,
)

from dataset import IMAGE_SIZE, build_loader


HERE = Path(__file__).resolve().parent
ARTIFACTS_DIR = HERE / "artifacts"
DEFAULT_FP32 = ARTIFACTS_DIR / "mobilenetv3_fp32.onnx"
DEFAULT_INT8 = ARTIFACTS_DIR / "mobilenetv3_int8.onnx"
DEFAULT_DATA_ROOT = HERE / "data" / "synthetic_autosampler_crops"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fp32", type=Path, default=DEFAULT_FP32,
                   help="Input float32 ONNX file from export_onnx.py")
    p.add_argument("--output", type=Path, default=DEFAULT_INT8,
                   help="Path to write the quantized INT8 ONNX file to")
    p.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT,
                   help="ImageFolder root with a calibration/ split")
    p.add_argument("--max-calibration-images", type=int, default=128,
                   help="Cap on the number of images fed to the calibrator")
    return p.parse_args()


class FolderCalibrationReader(CalibrationDataReader):
    """Feed pre-processed images to ONNX Runtime's calibrator.

    The reader yields one `{"input": <numpy array>}` dict per
    `get_next()` call and returns `None` when exhausted — the exact
    contract `quantize_static` expects.
    """

    def __init__(self, data_root: Path, max_images: int) -> None:
        # Batch size 1: the calibrator records activation ranges, it
        # does not benefit from larger batches.
        loader = build_loader(data_root, "calibration", batch_size=1,
                              num_workers=0, shuffle=False)
        self._iter: Iterator = self._stream(loader, max_images)

    @staticmethod
    def _stream(loader, max_images: int) -> Iterator:
        seen = 0
        for images, _labels in loader:
            if seen >= max_images:
                return
            # `images` is a torch tensor in NCHW with ImageNet
            # normalization already applied — exactly the input shape
            # the exported ONNX graph wants.
            yield {"input": images.numpy().astype(np.float32)}
            seen += 1

    def get_next(self) -> dict | None:
        return next(self._iter, None)


def main() -> None:
    args = parse_args()

    if not args.fp32.exists():
        raise SystemExit(
            f"[quantize] FP32 ONNX not found: {args.fp32}\n"
            "          run export_onnx.py first",
        )

    args.output.parent.mkdir(exist_ok=True)

    reader = FolderCalibrationReader(args.data_root, args.max_calibration_images)

    # QuantFormat.QDQ inserts Quantize/Dequantize ops around each
    # weight + activation — the modern ONNX-Runtime default and what
    # the EP optimisers (CPU, NNAPI, CoreML) understand best.
    # QInt8 / QUInt8 split: signed for weights, unsigned for
    # activations is the recipe ONNX Runtime recommends for
    # MobileNet-class architectures.
    quantize_static(
        model_input=str(args.fp32),
        model_output=str(args.output),
        calibration_data_reader=reader,
        quant_format=QuantFormat.QDQ,
        per_channel=False,
        weight_type=QuantType.QInt8,
        activation_type=QuantType.QUInt8,
    )

    fp32_size = args.fp32.stat().st_size / (1024 * 1024)
    int8_size = args.output.stat().st_size / (1024 * 1024)
    print(f"[quantize] wrote {args.output}")
    print(f"[quantize] size  FP32 = {fp32_size:5.2f} MiB"
          f"  INT8 = {int8_size:5.2f} MiB"
          f"  ratio = {fp32_size / max(int8_size, 1e-9):.2f}x smaller")
    print(f"[quantize] calibrated on {IMAGE_SIZE}x{IMAGE_SIZE} images,"
          f" cap = {args.max_calibration_images}")


if __name__ == "__main__":
    main()
