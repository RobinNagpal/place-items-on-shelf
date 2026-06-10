# 07 — Synthetic data for Labelling

> **Project status: not modelled** — there is no Gazebo world
> for this step. The current project assumes vials arrive at
> Step 8 already labelled. The notes below cover what would be
> needed if labelling were re-added.
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/07-labeling.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/07-labeling.md).

## What the robot would do

For each filled, capped vial:

1. Pick the printed sticker label from the label-printer tray
   (or peel it off a backing roll).
2. Hold the sticker so the printed face is visible to the wrist
   camera.
3. Move the sticker to the vial body.
4. Press the sticker onto the vial cylinder, rolling slightly to
   smooth out bubbles.
5. Verify the label is square to the vial axis.

The label carries: the **sample ID** (LIMS), the **barcode** (1D
or 2D, e.g. Code-128 or QR), the **date / batch**, and
sometimes a colour band.

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Is the printer ready and a label visible?" | RGB on the printer tray |
| "Does this label's text match the LIMS entry for this vial?" | OCR on the printed label (wrist camera close-up) |
| "Is the label peeled clean from the backing?" | RGB on the sticker silhouette + backing edge |
| "Is the sticker on straight?" | Wrist RGB on the vial — edge angle vs vial axis |
| "Are there bubbles or wrinkles under the sticker?" | Wrist RGB after press — local irregularity detector |

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **8 — synthetic text and barcode renders** | The headline asset. **Render** the sticker texture from a string template (`{sample_id}\n{date}\n{barcode}`) and save the source string alongside. Provides an unlimited supply of OCR + barcode-decode training pairs. Cheap because you control the typeface, contrast, lighting, and partial-occlusion regime. |
| **3 — keypoint annotations** | Per-frame pixel coordinates of: the four label corners (rectangle), the vial axis (top / bottom of the vial body), and the printer-output slot. Useful for the "is the label square" angle calculation and for the peel detector. |
| **5 — 6-DoF poses** | Per-frame poses of the printer, the vial being labelled, and the sticker itself (during pick / move / press). |
| **2 — segmentation masks** | Sticker, vial body, vial cap. The sticker mask after press gives a "label silhouette on vial" shape that the wrinkle detector consumes. |
| **6 — F/T traces** | The press-roll trace — Fz when pressing on the vial wall, and a small lateral Fx pattern when rolling. Useful for "did I actually press it on" closed-loop logic. |
| **11 — demonstrations** | Scripted "press and roll" trajectories with randomised vial radii. Behaviour cloning learns the roll rate that flattens bubbles without lifting an edge. |
| **12 — failure cases** | Crooked label (angle vs axis > 5°); double-printed (two stickers stuck); wrong text (label says batch B but vial is batch A — a *cross-modal* failure caught only by matching OCR against the LIMS expected value); peeled-and-fallen on the bench; bubble under the sticker. |

## Why OCR-and-barcode dominate here

This step has the **simplest perception story** of all 8: it's
mostly an OCR + barcode-decoding problem. Both have mature
open-source models (`paddleocr`, `easyocr`, `pyzbar`) that work
out of the box. Synthetic data is useful mostly as a
**smoke-test set**: render 1 000 sticker textures with known
strings, run the OCR + decoder on them, verify the parsed
string matches the source string in ≥ 99% of cases.

That alone validates the perception pipeline end-to-end without
ever printing a real sticker.

## Concrete dataset shape

```
synthetic_labeling/
├── images/
│   ├── printer_<traj>_<frame>.jpg            # printer-output close-up
│   ├── wrist_label_<traj>_<frame>.jpg        # label close-up in gripper
│   └── wrist_vial_<traj>_<frame>.jpg         # vial after press
├── labels/
│   ├── text_<sticker_id>.json                # {"sample_id": "KETCHUP_B_R2",
│                                              #  "date": "2026-06-10",
│                                              #  "barcode": "Code128",
│                                              #  "payload": "KB2-20260610"}
│   ├── keypoints_<traj>_<frame>.json         # label corners, vial axis
│   ├── poses_<traj>_<frame>.json
│   └── masks_<traj>_<frame>.png
└── traces/
    ├── ft_press_<traj>.csv
    └── joints_<traj>.csv
```

## Smallest useful first dataset

- 1 000 distinct sticker textures (vary font, size, contrast,
  partial occlusion, lighting) → OCR smoke test.
- 5 000 wrist-camera frames with the sticker in the gripper at
  randomised tilt → label-alignment regression model.
- 200 press-and-roll trajectories → behaviour-cloning target.
