# 05 — Synthetic data for Transfer to vial

> **Project status: modelled.** The Gazebo world is
> [`gazebo_worlds/05-transfer-to-vial/`](../../../gazebo_worlds/05-transfer-to-vial/).
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/05-transfer-to-vial.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/05-transfer-to-vial.md).

## What the robot does

For each of the 6 empty vials (`b1_r1`, `b1_r2`, `b2_r1`, `b2_r2`,
`b3_r1`, `b3_r2` — 3 batches × 2 replicates):

1. Pick up the Pasteur transfer pipette.
2. Dip its tip into the source beaker (the clean filtered
   ketchup from Step 4).
3. Squeeze the bulb gently to **draw clean liquid up** into the
   stem.
4. Move the tip over the opening of the target vial.
5. Squeeze the bulb gently to **dispense ~1.5 mL** into the vial.
6. Repeat for the next vial.
7. Put the pipette back on the bench.

The vial mouth is **9 mm wide**. Miss it and liquid spills onto
the rack.

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Where is the source beaker mouth?" | Overhead RGB + depth |
| "Is the pipette tip in the liquid?" | Depth (tip-z vs liquid-surface-z) |
| **"Where is the centre of the next vial mouth?"** | **Overhead RGB — sub-cm precision on a 9 mm target** |
| "Did the bulb squeeze actually draw liquid up?" | RGB looking at the transparent pipette stem — visible liquid column |
| **"Has the vial reached 1.5 mL?"** | **Side / overhead RGB — meniscus level inside the vial** |
| "Did I dispense over the vial mouth or miss?" | Overhead RGB — droplet trajectory + final liquid distribution |
| "Which vial is next in the sequence?" | Software state (vial-naming convention `b<batch>_r<replicate>`) |

The two **hard visual problems** are the vial-mouth centre
keypoint and the in-vial fill level. Everything else is
either pose tracking or software state.

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **3 — keypoint annotations** | Per-frame pixel coordinates of all 6 **vial-mouth centres** and the **source-beaker mouth centre**. The label format is `{vial_id: (u_px, v_px, conf)}`. Sub-pixel accuracy matters because the mouth is small. |
| **9 — fluid-level frame sequences** | Per-vial time-series during one dispense, frame-labelled with `vial_fill_ml` from 0 to 1.5 (with overflow labels at 1.8, 2.0 to capture the failure regime). |
| **5 — 6-DoF poses** | Per-frame poses of all 6 vials, the vial tray, the pipette (and its bulb), the source beaker. The pipette's tip pose is the same data the keypoint label is computed from, just before projection. |
| **2 — segmentation masks** | Pipette stem (so the "liquid column inside the stem" can be a sub-mask), vial bodies, vial tray slots (Ø14 mm rings), source-beaker liquid surface. |
| **6 — F/T traces** | The bulb-squeeze action is *external* (the operator's hand, not the wrist), so wrist F/T is less informative here than in Step 4. Still useful: (a) pipette-pick lift force; (b) overshoot detection during the move-between-vials transition. |
| **11 — demonstrations** | A scripted-expert dataset for the **last 10 cm** of the dispense move. Observation: vial-mouth pixel + tip pixel + depth. Action: small XY corrections to centre the tip. Behaviour cloning is well-suited here because the policy is short, repetitive, and 6 vials means each demo trajectory is naturally short. |
| **12 — failure cases** | Tip aimed at the *side* of the vial mouth (drip onto rim → onto rack); over-fill (vial > 2 mL → meniscus visible above rim); under-fill (< 1 mL); pipette picked from wrong end (bulb in the liquid); vial knocked over (cap-down event). |

## What the Gazebo world already gives you free

Looking at [`ketchup_transfer_to_vial.sdf`](../../../gazebo_worlds/05-transfer-to-vial/ketchup_transfer_to_vial.sdf):

- The 6 vials are named `vial_b<X>_r<Y>` so they appear in
  `/gazebo/model_states` with stable identifiers. The 2 × 3 grid
  positions are pinned in SDF coordinates, so the **mouth-centre
  keypoint per vial is computable from the SDF directly** — no
  hand labelling.
- The vial tray's six Ø14 mm slot mouths are explicit visuals in
  the SDF, which means a segmentation mask for "slot ring vs vial
  body vs cap" lands for free.
- The pipette is a single named model with stem + bulb sub-links;
  the bulb's compression state can be exposed as a joint angle if
  you wire it as a prismatic joint.

## Concrete dataset shape

```
synthetic_transfer/
├── images/
│   ├── overhead_<traj>_<frame>.jpg
│   ├── overhead_<traj>_<frame>.depth.npy
│   ├── vial_close_<traj>_<vial_id>_<frame>.jpg   # zoom on each vial mouth
│   └── source_close_<traj>_<frame>.jpg           # zoom on source-beaker mouth
├── labels/
│   ├── poses_<traj>_<frame>.json
│   ├── keypoints_<traj>_<frame>.json   # all 7 mouth centres + pipette tip
│   ├── masks_<traj>_<frame>.png        # per-instance masks
│   └── fill_levels_<traj>_<frame>.json # per-vial volume_ml
├── traces/
│   ├── ft_pick_pipette_<traj>.csv
│   └── joints_<traj>.csv
└── metadata.json
```

A second per-vial close-up render is what makes the vial-mouth
keypoint training tractable. Reusing one overhead frame for 7
keypoints works in principle but the spatial resolution is too
low for sub-cm accuracy on a 9 mm target.

## Smallest useful first dataset

For the vial-mouth keypoint:

- 6 vials × 50 randomised camera positions × 10 lighting setups
  × 10 trajectories = **30 000 frames** in the worst case, but
  realistically you train a single keypoint model on the
  per-vial close-up crops and re-use it across all 6 → about
  5 000 close-up frames is sufficient.

For the fill-level question, 100 trajectories × 60 fps × 5 s of
dispense = 30 000 labelled-frames; that's a comfortable training
set for a 1D-regression model (`pixel-y of meniscus →
volume_ml`).

## Why this step is the **ideal first proof-of-concept**

The source workflow doc specifically identifies the Transfer
step as the right place to start because:

- The vial geometry is fixed and well-known (HPLC standard).
- The targets are static (vials sit in a tray).
- The action is a single short open-loop motion, not a complex
  closed-loop one.
- Failure is visible and easy to score (spill / not spill).

That means the **synthetic-data shape above is the right shape
to commit to** even before the other steps are simulated — it
generalises directly to the Step 8 placement task and the Step 2
swirl task.
