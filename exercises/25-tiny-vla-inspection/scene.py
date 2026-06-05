"""Synthetic 'sim image' generator for the inspection scripts.

Draws a small workspace from above with one or more coloured cubes
on a tabletop. The image is the visual input the VLA receives; the
`Scene` dataclass also holds ground-truth positions for the
optional verification step in inspect.py.

We never train on these images. They exist so the inspection script
has something to feed the VLA's image encoder that looks like a
plausible robot-camera observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


IMAGE_HW = 96  # 96x96 RGB — small enough to keep the demo fast


COLOR_RGB: dict[str, tuple[int, int, int]] = {
    "red":    (220,  40,  40),
    "blue":   ( 40,  60, 220),
    "green":  ( 40, 200,  60),
    "yellow": (240, 220,  40),
}

TABLE_RGB = (200, 200, 210)  # light grey table


@dataclass
class CubeOnTable:
    color: str
    x: int  # pixel column of the cube centre
    y: int  # pixel row of the cube centre
    side_px: int = 18


@dataclass
class Scene:
    image_hw: int = IMAGE_HW
    cubes: list[CubeOnTable] = field(default_factory=list)

    def render(self) -> np.ndarray:
        """Return an (H, W, 3) uint8 RGB image of the scene."""
        img = np.full((self.image_hw, self.image_hw, 3), TABLE_RGB, dtype=np.uint8)
        for cube in self.cubes:
            half = cube.side_px // 2
            r0, r1 = cube.y - half, cube.y + half
            c0, c1 = cube.x - half, cube.x + half
            img[r0:r1, c0:c1] = COLOR_RGB[cube.color]
        return img


def three_cube_scene() -> Scene:
    """One red, one blue, one green cube — the standard inspection scene."""
    return Scene(
        cubes=[
            CubeOnTable(color="red",   x=24, y=48),
            CubeOnTable(color="blue",  x=48, y=48),
            CubeOnTable(color="green", x=72, y=48),
        ]
    )
