# 03 — Synthetic data for Dilution

> **Project status: modelled.** The Gazebo world is
> [`gazebo_worlds/03-dilution/`](../../../gazebo_worlds/03-dilution/).
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/03-dilution.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/03-dilution.md).

## What the robot does

Take 1 mL of cloudy ketchup extract from Step 2, transfer it into
a 10 mL volumetric flask, top up with water (or mild acid) to the
**etched fill-mark ring** at the flask neck, cap, and invert to
mix. If the result is still too strong, repeat with the 100 mL
flask for a 1:100 dilution.

The action sequence is:
**fresh tip → aspirate 1 mL → dispense into flask → eject tip →
pour solvent to fill-mark → cap → invert.**

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Did the new tip seat properly on the pipette?" | Wrist F/T (press-down force when seating) + RGB (silhouette of tip on shaft) |
| "Is the tip touching the extract surface?" | Depth camera (tip-z vs liquid-surface-z) |
| "Did the pipette aspirate the right 1 mL?" | RGB inside the tip (liquid column length) **or** trust the pipette dial (open-loop) |
| "Where is the flask neck centre?" | Overhead RGB + depth — the narrow Ø8 mm or Ø12 mm neck opening is a sub-cm target |
| **"Has the liquid reached the etched fill-mark line?"** | **Macro-RGB at the flask neck — the meniscus crossing the etched line is the hardest visual cue in the whole cell** |
| "Did the cap go on?" | RGB (cap pose change vs body) + F/T (twist torque) |
| "Did the invert mix work?" | Series of RGB frames — colour gradient flatness |

The make-or-break perception problem is **finding the etched
ring on the flask neck and detecting the moment the meniscus
crosses it**. This is sub-mm visual precision, in glass, with
specular reflections, on a thin engraved feature.

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **3 — keypoint annotations** | Per-frame pixel coordinates of the two endpoints of the **etched fill-mark line** on each flask neck. This is the single most valuable synthetic label in this whole step. The simulator knows the ring is at flask-z = 70 mm (10 mL) or 140 mm (100 mL), so the pixel coordinates fall out of the projection automatically. |
| **9 — fluid-level frame sequences** | A close-up time-series of the flask neck as the solvent bottle tilts. Each frame is labelled with the scripted `liquid_height_mm` and a binary `reached_mark`. Trains "stop pouring NOW" classifiers. |
| **2 — segmentation masks** | Per-pixel masks for `flask_body`, `flask_neck`, `meniscus_surface`, `cap`, `pipette_body`, `pipette_tip`. The meniscus mask is the one that's hardest and most useful. |
| **5 — 6-DoF poses** | Per-frame poses of both flasks, the pipette, the tip rack, the solvent bottle, the waste beaker, and the source beaker. Lets the pick-and-place planner ground-truth every object. |
| **6 — F/T traces** | (a) tip-seating press-down trace; (b) cap-on twist torque; (c) invert-mix torque pattern. Each one has a recognisable signature for a learned classifier. |
| **8 — text renders** | If you choose to print volume labels (`10 mL`, `100 mL`) on the flask bulb, render the texture with known text → OCR ground truth. |
| **12 — failure cases** | Over-fill (meniscus past the mark), under-fill (meniscus below mark), wrong-flask-used (1 mL transferred to the 100 mL flask, giving 1:100 instead of 1:10), cap not seated, pipette tip not seated, dropped tip on the bench. |

## What makes Dilution hard for synthetic data

Two problems are unique to this step:

1. **Specular reflections from glass.** Real photos of a
   volumetric flask have bright glints that the simulator does
   not produce out-of-the-box. Domain-randomised lighting
   (random HDR environment maps, random point-light positions)
   is the standard fix.
2. **Sub-pixel meniscus thickness.** The etched fill-mark ring
   is ~0.3 mm wide. At a 40 cm camera distance with a typical
   1280×720 sensor, that is ~0.5 px. Two practical answers:
   (a) render at higher resolution (3840×2160) and downsample
   with labels intact; (b) train on a region-of-interest crop
   around the neck instead of full frames.

Both are standard sim-to-real techniques but it's worth
flagging — the same dataset that works fine for "find the
beaker" is *not* enough for "did the meniscus cross the line."

## Concrete dataset shape

```
synthetic_dilution/
├── images/
│   ├── overhead_<traj>_<frame>.jpg
│   ├── overhead_<traj>_<frame>.depth.npy
│   └── neck_close_<traj>_<frame>.jpg     # tight crop on the flask neck
├── labels/
│   ├── poses_<traj>_<frame>.json
│   ├── masks_<traj>_<frame>.png
│   ├── keypoints_<traj>_<frame>.json     # fill-mark endpoints, neck centre
│   └── state_<traj>_<frame>.json         # {"liquid_height_mm": 69.4,
│                                         #  "reached_mark": false,
│                                         #  "target_volume_ml": 10}
├── traces/
│   ├── ft_tip_seat_<traj>.csv
│   ├── ft_cap_twist_<traj>.csv
│   └── joints_<traj>.csv
└── metadata.json
```

The `neck_close_*` crop is what the meniscus-detection model
actually trains on. The full overhead frame is mostly for
scene-level pose ground truth.

## Smallest useful first dataset

For the meniscus question specifically, **variety beats volume**:
~2 000 trajectories of the pour with randomised lighting and
liquid colour give more useful signal than 200 000 frames of one
canned pour. Plan the budget around the meniscus model first;
everything else (scene poses, F/T traces) comes along for free.

## Open question

The Gazebo world does **not** currently render the etched
fill-mark ring on the flask neck because SDF primitives don't
support engraved geometry. The realistic options are: (a) emit
a thin coloured ring as a translucent visual that approximates
the look; (b) post-process the rendered frame with a
shader / OpenCV pass that adds the ring at known pixel
coordinates. Option (b) is more flexible — same code can also
generate explicit keypoint labels.
