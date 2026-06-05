"""Inspect — feed a scene + instruction to TinyVLA, log the action, DO NOT execute.

The checklist task is explicit: 'Feed a sim image plus an instruction
to a small VLA model, log the predicted 7-DoF action — do **not**
execute it on the arm.' Done when 'you can explain what each output
channel means and how it maps to your arm's action space.'

This script does exactly that:

  1. Build a scene and render the camera image.
  2. Tokenise an English instruction.
  3. Forward pass through TinyVLA.
  4. Print every action channel with its name, value, units, and
     what it would do if executed.
  5. Write the same data to output/predictions.csv.
  6. Save the scene image to output/scene.png.

Nothing is sent to MoveIt, no motors move. That is the entire point.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import torch

from scene import three_cube_scene
from tiny_vla import (
    ACTION_NAMES,
    build_model,
    count_parameters,
    preprocess_image,
    preprocess_text,
)
from vocab import tokenize


CHANNEL_NOTES: dict[str, str] = {
    "dx":      "translate end-effector along base-frame X (metres, +forward)",
    "dy":      "translate end-effector along base-frame Y (metres, +left)",
    "dz":      "translate end-effector along base-frame Z (metres, +up)",
    "droll":   "rotate end-effector about X (radians)",
    "dpitch":  "rotate end-effector about Y (radians)",
    "dyaw":    "rotate end-effector about Z (radians)",
    "gripper": "0.0 = fully closed, 1.0 = fully open (normalised)",
}


def save_scene_png(rgb: np.ndarray, path: Path) -> None:
    """Write the rendered scene to a PNG without pulling in matplotlib."""
    import struct
    import zlib

    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    compressed = zlib.compress(raw)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main(instructions: list[str] | None = None) -> None:
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    if instructions is None:
        instructions = [
            "pick the red cube",
            "pick the blue cube",
            "pick the green cube",
            "move the red cube to the left",
        ]

    print("[inspect] building TinyVLA ...")
    model = build_model(seed=0)
    n_params = count_parameters(model)
    print(f"[inspect] model has {n_params:,} parameters (real OpenVLA: ~7,000,000,000)")

    scene = three_cube_scene()
    image = scene.render()
    save_scene_png(image, out_dir / "scene.png")
    print(f"[inspect] scene saved to {out_dir / 'scene.png'}")

    img_tensor = preprocess_image(image)

    rows: list[list[str]] = []
    rows.append(["instruction", *ACTION_NAMES])

    for instr in instructions:
        token_ids = tokenize(instr)
        tok_tensor = preprocess_text(token_ids)
        with torch.no_grad():
            action = model(img_tensor, tok_tensor).squeeze(0).numpy()

        print()
        print(f"[inspect] instruction: '{instr}'")
        print(f"[inspect] tokens:      {token_ids[:len([t for t in token_ids if t != 0])]}")
        print(f"[inspect] action shape: {tuple(action.shape)}  (7-DoF, same as OpenVLA)")
        print("[inspect] channel-by-channel:")
        for name, val in zip(ACTION_NAMES, action):
            print(f"           {name:8s} = {val:+.4f}   <- {CHANNEL_NOTES[name]}")

        rows.append([instr, *[f"{v:.6f}" for v in action]])

    csv_path = out_dir / "predictions.csv"
    with csv_path.open("w", newline="") as f:
        csv.writer(f).writerows(rows)
    print()
    print(f"[inspect] predictions saved to {csv_path}")
    print("[inspect] NOTE: model is randomly initialised; numbers are illustrative.")
    print("[inspect] No commands were sent to MoveIt. No motors moved. By design.")


if __name__ == "__main__":
    main()
