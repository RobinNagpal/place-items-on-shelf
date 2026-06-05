"""Fine-tune MobileNetV3-Small on the 5 autosampler crop classes.

We start from torchvision's ImageNet-pretrained weights and replace
the final 1000-class classifier head with a fresh 5-class linear
layer. Only the head is fully reset; the backbone is left trainable
but at the same low learning rate (full fine-tune on a tiny set).

Run:
    python train.py
or with overrides:
    python train.py --epochs 30 --batch 32 --lr 5e-4

Outputs:
    artifacts/mobilenetv3_fp32.pt        # state_dict for the trained model
    artifacts/training_log.txt           # per-epoch loss + val top-1

`mobilenetv3_fp32.pt` is the file `export_onnx.py` loads next.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

from dataset import NUM_CLASSES, build_loader


HERE = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = HERE / "data" / "synthetic_autosampler_crops"
ARTIFACTS_DIR = HERE / "artifacts"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT,
                   help="ImageFolder root holding train/val/test/calibration")
    p.add_argument("--epochs", type=int, default=20,
                   help="Training epochs")
    p.add_argument("--batch", type=int, default=32,
                   help="Mini-batch size")
    p.add_argument("--lr", type=float, default=1e-3,
                   help="Initial learning rate")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu",
                   help='Torch device: "cuda", "cpu", or "cuda:0"')
    p.add_argument("--workers", type=int, default=2,
                   help="DataLoader worker processes")
    return p.parse_args()


def build_model(num_classes: int) -> nn.Module:
    """Return MobileNetV3-Small with a fresh `num_classes` head.

    We keep the backbone weights but reset the last Linear so the
    network outputs `num_classes` logits instead of 1000.
    """
    weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
    model = mobilenet_v3_small(weights=weights)

    # MobileNetV3-Small's classifier is `Sequential(Linear, Hardswish,
    # Dropout, Linear)`. We swap the last Linear for our 5-class head.
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


@torch.no_grad()
def evaluate(model: nn.Module, loader, device: torch.device) -> float:
    """Top-1 accuracy on `loader`."""
    model.eval()
    correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        logits = model(images)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
    return correct / max(total, 1)


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)

    train_loader = build_loader(args.data_root, "train", args.batch, args.workers)
    val_loader = build_loader(args.data_root, "val", args.batch, args.workers,
                              shuffle=False)

    model = build_model(NUM_CLASSES).to(device)

    # AdamW is the safe default for fine-tuning small classifiers.
    # The pre-trained backbone tolerates lr=1e-3 because we are also
    # resetting the head — there is no head warm-up phase to worry
    # about on a 5-class task.
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss()

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    log_path = ARTIFACTS_DIR / "training_log.txt"
    best_acc = -1.0
    best_path = ARTIFACTS_DIR / "mobilenetv3_fp32.pt"

    with log_path.open("w") as log:
        log.write("epoch,train_loss,val_top1\n")
        for epoch in range(1, args.epochs + 1):
            model.train()
            running_loss = 0.0
            seen = 0
            for images, labels in train_loader:
                images = images.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)

                optimizer.zero_grad(set_to_none=True)
                logits = model(images)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * images.size(0)
                seen += images.size(0)

            scheduler.step()
            avg_loss = running_loss / max(seen, 1)
            val_acc = evaluate(model, val_loader, device)
            log.write(f"{epoch},{avg_loss:.4f},{val_acc:.4f}\n")
            log.flush()
            print(f"[train] epoch {epoch:>3}/{args.epochs}  "
                  f"loss={avg_loss:.4f}  val_top1={val_acc:.4f}")

            # Keep the checkpoint that scored best on val — it is the
            # one quantization runs against later.
            if val_acc > best_acc:
                best_acc = val_acc
                torch.save(model.state_dict(), best_path)

    print()
    print(f"[train] best val top-1 = {best_acc:.4f}")
    print(f"[train] saved          = {best_path}")
    print(f"[train] log            = {log_path}")


if __name__ == "__main__":
    main()
