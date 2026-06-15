"""Procedural scene description for the HPLC autosampler top-down view.

This file is pure data — no rendering, no images. It describes *where*
each vial, empty slot, and distractor sits, in millimetres in the
world frame. ``render.py`` turns that description into pixels.

Keeping geometry and pixels in separate files means we can change the
camera resolution, add new randomisation knobs, or swap the renderer
without touching the procedural-scene logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

# Rack geometry — matches the 54-slot 6x9 variant referenced in
# docs/hplc-autosamplers/requirements/. The exact numbers do not have
# to be physically perfect; what matters is that the slot grid is the
# same shape the real autosampler trays use.
RACK_ROWS = 6
RACK_COLS = 9
SLOT_SPACING_MM = 14.0   # centre-to-centre distance between adjacent slots
VIAL_DIAM_MM = 12.0      # vial body diameter (top-down view)
CAP_DIAM_MM = 10.0       # cap diameter, sits on top of the vial body
RACK_MARGIN_MM = 6.0     # rack outer border around the slot grid

# Workspace = field of view of the simulated overhead camera, in mm.
WORKSPACE_W_MM = 160.0
WORKSPACE_H_MM = 120.0

# Cap colour palette. The names match the ``cap_red`` class hint in
# exercise 3 (the tiny YOLO) and the colour-coded subsets used in
# exercise 13 (HSV segmentation).
CAP_COLORS: dict[str, Tuple[int, int, int]] = {
    "red":    (210, 40, 40),
    "blue":   (40, 70, 210),
    "green":  (50, 180, 70),
    "yellow": (225, 200, 50),
    "white":  (240, 240, 240),
}


@dataclass
class Vial:
    """A filled rack slot."""
    row: int
    col: int
    cap_color: str          # one of CAP_COLORS' keys


@dataclass
class EmptySlot:
    """A visible slot with no vial in it."""
    row: int
    col: int


@dataclass
class Distractor:
    """An off-rack object that should NOT be detected as a vial.

    Distractors exist so the trained model sees more than just the
    rack — every real cell has tools, labels, spilled caps, and the
    occasional gloved hand passing through.
    """
    x_mm: float
    y_mm: float
    w_mm: float
    h_mm: float
    color: Tuple[int, int, int]


@dataclass
class Scene:
    """One concrete scene the renderer will draw."""
    # (x, y) in mm of the centre of slot (row=0, col=0). Randomised
    # per-scene so the rack is not in the exact same pixel every frame.
    rack_origin_mm: Tuple[float, float]
    vials: List[Vial] = field(default_factory=list)
    empty_slots: List[EmptySlot] = field(default_factory=list)
    distractors: List[Distractor] = field(default_factory=list)

    def slot_center_mm(self, row: int, col: int) -> Tuple[float, float]:
        """World-frame centre of one slot in this scene."""
        ox, oy = self.rack_origin_mm
        return (ox + col * SLOT_SPACING_MM, oy + row * SLOT_SPACING_MM)

    def rack_bounds_mm(self) -> Tuple[float, float, float, float]:
        """Outer (x0, y0, x1, y1) of the rack body, including the margin."""
        ox, oy = self.rack_origin_mm
        x0 = ox - SLOT_SPACING_MM / 2 - RACK_MARGIN_MM
        y0 = oy - SLOT_SPACING_MM / 2 - RACK_MARGIN_MM
        x1 = ox + (RACK_COLS - 0.5) * SLOT_SPACING_MM + RACK_MARGIN_MM
        y1 = oy + (RACK_ROWS - 0.5) * SLOT_SPACING_MM + RACK_MARGIN_MM
        return (x0, y0, x1, y1)


def _nominal_rack_origin() -> Tuple[float, float]:
    """Origin that centres the rack inside the workspace when no jitter is added."""
    grid_w = (RACK_COLS - 1) * SLOT_SPACING_MM
    grid_h = (RACK_ROWS - 1) * SLOT_SPACING_MM
    return ((WORKSPACE_W_MM - grid_w) / 2.0, (WORKSPACE_H_MM - grid_h) / 2.0)


def random_scene(
    rng: np.random.Generator,
    fill_prob: float = 0.7,
    rack_jitter_mm: float = 3.0,
    max_distractors: int = 3,
) -> Scene:
    """One random procedural scene.

    ``fill_prob`` is the per-slot probability of containing a vial.
    ``rack_jitter_mm`` simulates a tech bumping the rack a few mm.
    ``max_distractors`` caps how many off-rack objects we throw in.
    """
    nx, ny = _nominal_rack_origin()
    rack_origin = (
        nx + rng.uniform(-rack_jitter_mm, rack_jitter_mm),
        ny + rng.uniform(-rack_jitter_mm, rack_jitter_mm),
    )
    scene = Scene(rack_origin_mm=rack_origin)

    cap_names = list(CAP_COLORS.keys())
    for r in range(RACK_ROWS):
        for c in range(RACK_COLS):
            if rng.random() < fill_prob:
                scene.vials.append(Vial(row=r, col=c, cap_color=str(rng.choice(cap_names))))
            else:
                scene.empty_slots.append(EmptySlot(row=r, col=c))

    # Distractors live outside the rack bounding box so they never
    # overlap a real vial label (which would be ambiguous to score).
    x0, y0, x1, y1 = scene.rack_bounds_mm()
    n = int(rng.integers(0, max_distractors + 1))
    for _ in range(n):
        # Pick a side, then a position along that side's strip.
        side = rng.integers(0, 4)
        w = float(rng.uniform(6.0, 14.0))
        h = float(rng.uniform(6.0, 14.0))
        if side == 0:    # above the rack
            cx = rng.uniform(0, WORKSPACE_W_MM)
            cy = rng.uniform(2.0, max(2.0, y0 - 2.0))
        elif side == 1:  # below the rack
            cx = rng.uniform(0, WORKSPACE_W_MM)
            cy = rng.uniform(y1 + 2.0, WORKSPACE_H_MM - 2.0)
        elif side == 2:  # left of the rack
            cx = rng.uniform(2.0, max(2.0, x0 - 2.0))
            cy = rng.uniform(0, WORKSPACE_H_MM)
        else:            # right of the rack
            cx = rng.uniform(x1 + 2.0, WORKSPACE_W_MM - 2.0)
            cy = rng.uniform(0, WORKSPACE_H_MM)
        color = tuple(int(v) for v in rng.integers(50, 200, size=3))
        scene.distractors.append(Distractor(x_mm=cx, y_mm=cy, w_mm=w, h_mm=h, color=color))

    return scene
