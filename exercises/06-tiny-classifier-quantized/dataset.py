"""Shared dataloader for exercise 06.

The classifier is trained on **cropped object images**, one per box
in the YOLO detection set from exercises 3 and 5. The layout follows
the standard `torchvision.datasets.ImageFolder` convention:

    data/synthetic_autosampler_crops/
    ├── train/<class_name>/*.jpg
    ├── val/<class_name>/*.jpg
    ├── test/<class_name>/*.jpg
    └── calibration/<class_name>/*.jpg   (for INT8 PTQ)

Every script in this folder reads from here so the class order stays
in one place. The order is alphabetical (ImageFolder default), which
locks the index → class-name mapping for export, quantization, and
benchmarking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from torch.utils.data import DataLoader
from torchvision import datasets, transforms


# Five classes, same as exercise 3. ImageFolder picks them in
# alphabetical order, so the class_id mapping is:
#   0 = cap_red, 1 = empty_slot, 2 = rack_edge, 3 = tray_edge, 4 = vial
# We keep the *names* aligned with exercise 3 (same words) but the
# *indices* differ — classifier vs detector tasks do not share a head.
CLASS_NAMES: Tuple[str, ...] = (
    "cap_red",
    "empty_slot",
    "rack_edge",
    "tray_edge",
    "vial",
)
NUM_CLASSES = len(CLASS_NAMES)

# MobileNetV3 was trained on ImageNet at 224x224. Keep the same input
# size so the COCO/ImageNet backbone weights stay useful.
IMAGE_SIZE = 224

# ImageNet mean / std — required for the backbone to interpret pixel
# values the way it was pre-trained on.
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def build_transforms(train: bool) -> transforms.Compose:
    """Return the torchvision transform pipeline for one split.

    Training applies light augmentation (flip + colour jitter) so the
    backbone does not memorise the small synthetic set. Eval / val /
    test / calibration use the deterministic resize + normalise path.
    """
    if train:
        return transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    return transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_loader(
    data_root: Path,
    split: str,
    batch_size: int,
    num_workers: int = 2,
    shuffle: bool | None = None,
) -> DataLoader:
    """Build a DataLoader for one split under `data_root`.

    `split` must be one of {"train", "val", "test", "calibration"}.
    The directory must exist and contain one subfolder per class.
    """
    if split not in {"train", "val", "test", "calibration"}:
        raise ValueError(f"unknown split: {split!r}")

    split_dir = data_root / split
    if not split_dir.is_dir():
        raise FileNotFoundError(
            f"expected ImageFolder layout at {split_dir} — see data/README.md",
        )

    dataset = datasets.ImageFolder(
        root=str(split_dir),
        transform=build_transforms(train=(split == "train")),
    )

    # Sanity check: the discovered class order must match what every
    # other script in this folder assumes. Catches the common bug of
    # accidentally renaming a class folder.
    if tuple(dataset.classes) != CLASS_NAMES:
        raise RuntimeError(
            f"class folders under {split_dir} are {dataset.classes!r}; "
            f"expected {list(CLASS_NAMES)!r}",
        )

    if shuffle is None:
        shuffle = split == "train"

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=False,
        drop_last=False,
    )
