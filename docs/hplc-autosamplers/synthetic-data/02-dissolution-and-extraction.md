# 02 — Synthetic data for Dissolution / extraction

> **Project status: modelled.** The Gazebo world is
> [`gazebo_worlds/02-dissolution-and-extraction/`](../../../gazebo_worlds/02-dissolution-and-extraction/).
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md).

## What the robot does

For each of three beakers in a row (the world contains beakers
1 / 2 / 3, each already holding a ~5 g ketchup blob on the
bottom):

1. Pick the beaker from its rest spot.
2. Place it at the pour station in the bench centre.
3. Pick up the solvent bottle.
4. Tilt the bottle to pour ~50 mL of solvent into the beaker.
5. Set the solvent bottle back on the bench.
6. Pick the beaker from the pour station.
7. **Swirl** the beaker in a small circle for ~10 seconds so
   the ketchup blob disperses into the solvent.
8. Place the beaker back at its rest position.

End state: cloudy reddish liquid in each of the three beakers.

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Which beaker is next? Where is it on the bench?" | Overhead camera (RGB + depth) |
| "Did I pick the beaker cleanly?" | Wrist F/T (lift signature) + contact sensors |
| "Is the solvent bottle's cap on or off?" | Overhead RGB (cap pose) — and a pre-check, since the arm can't open a real screw cap easily |
| "How much have I poured so far?" | RGB (liquid level inside beaker) **or** time-of-tilt (open-loop) |
| "Is the ketchup blob fully dispersed yet?" | RGB — colour homogeneity / cloudiness over time |
| "Did I spill any solvent?" | RGB (bench surface for puddles) + F/T (sudden weight loss in the bottle) |

Note the **two failure modes** the camera has to catch: spill
detection and "blob still on the bottom of the beaker."

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **5 — 6-DoF poses** | Per-frame pose of `beaker_1 / _2 / _3 / solvent_bottle / ketchup_blob_1..3`. Lets the pick-and-place planner use ground truth or score against perception. |
| **2 — segmentation masks** | Per-pixel masks for `beaker`, `solvent_bottle`, `liquid_inside_beaker`, `ketchup_blob`, `bench_top`. The liquid-inside-beaker mask is the one that matters: it shrinks / grows as the bottle tilts. |
| **9 — fluid-level frame sequences** | A *time-stamped* sequence of frames during one pour, each frame labelled with the scripted `volume_ml` value of the solvent inside the beaker. Trains "have I reached 50 mL yet?" classifiers and is the **most important** type for this step. |
| **6 — F/T traces** | Two interesting traces: (a) lift force when picking the beaker — heavier-than-expected force = forgot to lift the bottle first, lighter-than-expected = beaker still empty. (b) Torque pattern during the swirl — a clean circular swirl has a predictable sinusoidal trace; a jerky swirl spills. |
| **9 — dissolution progress** | Same idea as the pour but labelled with a scripted `dispersed_fraction` in `[0, 1]`. Frame 0 = blob untouched; frame 600 = fully mixed. |
| **11 — demonstrations** | A scripted swirl-loop demo set: 50+ short trajectories of "beaker centre + swirl radius + swirl frequency" → joint sequence. Behaviour cloning learns the swirl shape that mixes without spilling. |
| **12 — failure cases** | Spilled-solvent frames (puddle visible on bench), tipped-over beaker, blob still visible at the bottom after the swirl. Each one tagged with the failure-mode string. |

## What the Gazebo world already gives you free

Looking at [`ketchup_extraction.sdf`](../../../gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf):

- The 3 beakers, the solvent bottle, the ketchup blobs, and the
  bench are all named SDF models. Their poses come straight off
  `/world/<name>/pose/info` — that **is** the 6-DoF dataset.
- The solvent bottle has a **static water-level visual** prop
  inside it. A small "fake pour" plugin can shrink that prop's
  height on tilt — and the same plugin script that controls the
  shrink writes the per-frame `volume_ml` label.
- Lighting and overhead-camera intrinsics are already defined
  in the SDF, so randomising them per frame is one tweak.

## Concrete dataset shape

```
synthetic_dissolution/
├── images/
│   ├── overhead_<traj>_<frame>.jpg        # 1280x720 RGB
│   └── overhead_<traj>_<frame>.depth.npy  # depth, metres
├── labels/
│   ├── poses_<traj>_<frame>.json          # per-object 6-DoF
│   ├── masks_<traj>_<frame>.png           # instance mask
│   └── state_<traj>_<frame>.json          # {"pour_volume_ml": 32.5,
│                                          #  "dispersed_fraction": 0.0,
│                                          #  "spill": false}
├── traces/
│   ├── ft_swirl_<traj>.csv                # wrist F/T during swirl
│   └── joints_<traj>.csv                  # joint states
└── metadata.json                          # world name, random seed,
                                          # lighting param, etc.
```

`<traj>` is one full pick-pour-swirl run, `<frame>` is the
frame index inside that run.

## Smallest useful first dataset

For a first round you do **not** need 10 000 frames. Aim for:

- 3 randomised lighting setups × 3 random camera nudges × 100
  trajectories = **900 trajectories**.
- Each trajectory ~10 s at 30 fps = 300 frames, so ~270 000
  frames — but you can **subsample** to 1 fps for most labels
  (pour level changes slowly) and keep full 30 fps only for
  F/T traces and short events (spill, swirl).

That cuts the labelled-image set to a manageable ~30 000.
