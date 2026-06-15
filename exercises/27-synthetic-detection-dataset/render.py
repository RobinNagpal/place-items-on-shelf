"""Rasterise a ``Scene`` into one RGB frame and one mask per object.

The ground-truth labels (bbox + per-instance mask) come straight from
the geometry we drew, not from an image-processing step. That's the
whole point of synthetic data: the simulator already knows the truth.

We apply three of the four methods from
``docs/synthetic-data/how-we-generate-it.md``:

- **Domain randomisation** — random ambient brightness, background
  tint, and rack texture per scene.
- **Procedural scenes** — the layout is generated in ``scene.py``;
  this file just draws whatever it was given.
- **Sensor noise modelling** — a light Gaussian noise layer on the
  RGB to mimic a real camera's read noise.

Photo-real rendering needs a ray tracer (Isaac Sim / Blender / Unreal)
and is out of scope for a tiny self-contained exercise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from scene import (
    CAP_COLORS,
    CAP_DIAM_MM,
    SLOT_SPACING_MM,
    VIAL_DIAM_MM,
    WORKSPACE_H_MM,
    WORKSPACE_W_MM,
    EmptySlot,
    Scene,
    Vial,
)

# Camera resolution. 4 px / mm keeps a 12 mm vial at ~48 px diameter —
# big enough that a YOLO grid cell at stride 8 sees several vial pixels.
IMG_W = 640
IMG_H = 480
PX_PER_MM = 4.0


# Class ids used in the COCO + YOLO labels. Two classes is enough to
# demonstrate the format and to feed exercises 3 and 4. If you need
# ``cap_red`` as its own class, split ``vial`` by cap colour here.
CLASS_NAMES = ["vial", "empty_slot"]
CLASS_VIAL = 0
CLASS_EMPTY_SLOT = 1


@dataclass
class Annotation:
    """One object in the rendered frame, ready to be serialised."""
    class_id: int
    # Bounding box in pixels, (x0, y0, x1, y1), inclusive of edges.
    bbox_xyxy: Tuple[int, int, int, int]
    # Binary mask, ``(IMG_H, IMG_W)`` uint8, 0 or 255.
    mask: np.ndarray
    # Free-form attributes (cap colour, slot id) — written into the
    # COCO JSON so a downstream filter can ask for "all red-cap vials".
    attributes: dict


@dataclass
class RenderResult:
    rgb: np.ndarray              # (H, W, 3) uint8
    annotations: List[Annotation]


def _mm_to_px(x_mm: float, y_mm: float) -> Tuple[float, float]:
    return (x_mm * PX_PER_MM, y_mm * PX_PER_MM)


def _disk_mask(cx: float, cy: float, r_px: float) -> np.ndarray:
    """Filled-disk binary mask, same shape as the image. 255 inside, 0 outside."""
    ys, xs = np.ogrid[:IMG_H, :IMG_W]
    inside = (xs - cx) ** 2 + (ys - cy) ** 2 <= r_px ** 2
    return (inside.astype(np.uint8)) * 255


def _bbox_from_mask(mask: np.ndarray) -> Tuple[int, int, int, int]:
    """Tight (x0, y0, x1, y1) of the non-zero pixels in ``mask``."""
    ys, xs = np.where(mask > 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def _random_rack_texture(rng: np.random.Generator) -> Tuple[int, int, int]:
    """Pick a plausible neutral rack colour each scene (light grey / tan)."""
    base = int(rng.integers(150, 200))
    warm = int(rng.integers(-10, 25))
    return (min(255, base + warm), base, max(0, base - 10))


def _random_background_tint(rng: np.random.Generator) -> Tuple[int, int, int]:
    """Workspace background — a slightly tinted off-white bench top."""
    base = int(rng.integers(200, 240))
    tint = rng.integers(-15, 15, size=3)
    return tuple(int(np.clip(base + t, 180, 255)) for t in tint)


def render(scene: Scene, rng: np.random.Generator) -> RenderResult:
    """Draw ``scene`` into one frame and return all object annotations."""
    bg = _random_background_tint(rng)
    img = Image.new("RGB", (IMG_W, IMG_H), bg)
    draw = ImageDraw.Draw(img)

    # ---- background texture (faint stripes to mimic a benchtop pattern) ----
    stripe_color = tuple(int(np.clip(c - 8, 0, 255)) for c in bg)
    stripe_step = int(rng.integers(20, 50))
    for x in range(0, IMG_W, stripe_step):
        draw.line([(x, 0), (x, IMG_H)], fill=stripe_color, width=1)

    # ---- rack body ----
    rack_color = _random_rack_texture(rng)
    x0_mm, y0_mm, x1_mm, y1_mm = scene.rack_bounds_mm()
    px0, py0 = _mm_to_px(x0_mm, y0_mm)
    px1, py1 = _mm_to_px(x1_mm, y1_mm)
    draw.rounded_rectangle([(px0, py0), (px1, py1)], radius=8, fill=rack_color)

    # ---- distractors (drawn BEFORE slots / vials so vials sit on top) ----
    for d in scene.distractors:
        cx, cy = _mm_to_px(d.x_mm, d.y_mm)
        hw, hh = (d.w_mm * PX_PER_MM) / 2, (d.h_mm * PX_PER_MM) / 2
        draw.rectangle([(cx - hw, cy - hh), (cx + hw, cy + hh)], fill=d.color)

    # ---- empty slots (dark drilled-hole circles in the rack) ----
    annotations: List[Annotation] = []
    slot_r_px = (VIAL_DIAM_MM * PX_PER_MM) / 2 + 1.5
    empty_color = tuple(max(0, c - 80) for c in rack_color)
    for slot in scene.empty_slots:
        cx_mm, cy_mm = scene.slot_center_mm(slot.row, slot.col)
        cx, cy = _mm_to_px(cx_mm, cy_mm)
        draw.ellipse([(cx - slot_r_px, cy - slot_r_px), (cx + slot_r_px, cy + slot_r_px)], fill=empty_color)
        mask = _disk_mask(cx, cy, slot_r_px)
        annotations.append(Annotation(
            class_id=CLASS_EMPTY_SLOT,
            bbox_xyxy=_bbox_from_mask(mask),
            mask=mask,
            attributes={"row": slot.row, "col": slot.col},
        ))

    # ---- vials (body ring, then coloured cap on top) ----
    vial_body_r_px = (VIAL_DIAM_MM * PX_PER_MM) / 2
    cap_r_px = (CAP_DIAM_MM * PX_PER_MM) / 2
    for v in scene.vials:
        cx_mm, cy_mm = scene.slot_center_mm(v.row, v.col)
        cx, cy = _mm_to_px(cx_mm, cy_mm)
        # Vial body (slightly darker than rack so it shows up).
        body_color = tuple(max(0, c - 30) for c in rack_color)
        draw.ellipse(
            [(cx - vial_body_r_px, cy - vial_body_r_px), (cx + vial_body_r_px, cy + vial_body_r_px)],
            fill=body_color,
        )
        # Cap on top.
        cap_rgb = CAP_COLORS[v.cap_color]
        draw.ellipse(
            [(cx - cap_r_px, cy - cap_r_px), (cx + cap_r_px, cy + cap_r_px)],
            fill=cap_rgb,
        )
        # Mask is the entire vial silhouette (body, not just the cap),
        # which is what downstream segmentation models train against.
        mask = _disk_mask(cx, cy, vial_body_r_px)
        annotations.append(Annotation(
            class_id=CLASS_VIAL,
            bbox_xyxy=_bbox_from_mask(mask),
            mask=mask,
            attributes={"row": v.row, "col": v.col, "cap_color": v.cap_color},
        ))

    # ---- domain randomisation: per-scene brightness + slight blur ----
    rgb = np.asarray(img, dtype=np.float32)
    brightness = float(rng.uniform(0.75, 1.15))
    rgb *= brightness
    rgb = np.clip(rgb, 0, 255)

    # Slight blur (some lenses, some focus offset).
    if rng.random() < 0.5:
        blurred = Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=0.6))
        rgb = np.asarray(blurred, dtype=np.float32)

    # ---- sensor noise modelling: Gaussian RGB noise ----
    noise_sigma = float(rng.uniform(2.0, 6.0))
    rgb += rng.normal(0.0, noise_sigma, size=rgb.shape)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    return RenderResult(rgb=rgb, annotations=annotations)
