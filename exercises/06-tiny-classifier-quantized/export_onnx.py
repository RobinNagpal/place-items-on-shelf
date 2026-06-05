"""Export the fine-tuned MobileNetV3-Small to ONNX (float32).

ONNX (Open Neural Network Exchange) is the cross-framework model
format every modern inference runtime understands. Once the model is
ONNX, we can run it through ONNX Runtime on a Pi / Jetson without
PyTorch installed — and the same file is what `quantize.py` turns
into INT8.

Run:
    python export_onnx.py
    python export_onnx.py --weights artifacts/mobilenetv3_fp32.pt

Outputs:
    artifacts/mobilenetv3_fp32.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from dataset import IMAGE_SIZE, NUM_CLASSES
from train import build_model


HERE = Path(__file__).resolve().parent
ARTIFACTS_DIR = HERE / "artifacts"
DEFAULT_WEIGHTS = ARTIFACTS_DIR / "mobilenetv3_fp32.pt"
DEFAULT_OUT = ARTIFACTS_DIR / "mobilenetv3_fp32.onnx"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS,
                   help="Trained .pt produced by train.py")
    p.add_argument("--output", type=Path, default=DEFAULT_OUT,
                   help="Path to write the .onnx file to")
    p.add_argument("--opset", type=int, default=17,
                   help="ONNX opset version (17 is the safe modern default)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.weights.exists():
        raise SystemExit(
            f"[export] checkpoint not found: {args.weights}\n"
            "        run train.py first or pass --weights <path>",
        )

    args.output.parent.mkdir(exist_ok=True)

    model = build_model(NUM_CLASSES)
    state = torch.load(args.weights, map_location="cpu")
    model.load_state_dict(state)
    model.eval()

    # Static batch=1 is fine for the autosampler pipeline — one frame,
    # one inference. We still mark batch as dynamic so the same file
    # works if a downstream user wants to batch.
    dummy = torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE)
    torch.onnx.export(
        model,
        dummy,
        str(args.output),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=args.opset,
        do_constant_folding=True,
    )

    print(f"[export] wrote {args.output}")
    print(f"[export] opset = {args.opset}, input = 1x3x{IMAGE_SIZE}x{IMAGE_SIZE}")


if __name__ == "__main__":
    main()
