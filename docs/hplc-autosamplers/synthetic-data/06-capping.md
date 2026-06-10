# 06 — Synthetic data for Capping

> **Project status: skipped.** A small cobot gripper cannot
> reliably twist a screw cap or operate a manual crimper, so the
> project's [`gazebo_worlds/`](../../../gazebo_worlds/) folder
> deliberately omits this step. The notes below exist for anyone
> later adding a wrist-mounted screw-cap fixture or a powered
> capper.
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/06-capping.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/06-capping.md).

## What the robot would do

Two physical sub-types:

- **Screw cap.** Pick a loose cap from a cap tray, align over
  the vial neck, twist down ~3 turns until snug. Torque limit
  ~0.4 N·m so the septum is not crushed.
- **Crimp cap.** Place a thin aluminium cap loosely on the
  neck, place a manual or pneumatic crimper over it, fire the
  crimper. Crimp force ~50 N for a couple hundred ms.

Either way, the end state is "cap seated flush on the vial,
septum intact, no leak."

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Where is the loose cap on the cap tray?" | Overhead RGB + depth |
| "Did I pick the cap right-side-up?" | Side / overhead RGB on the gripper |
| "Is the cap aligned over the vial neck?" | Wrist camera (eye-in-hand) — the alignment is the make-or-break moment |
| **"Did the cap engage the threads or just spin on top?"** | **Wrist F/T — distinct torque signatures for "engaged + tightening" vs "skipping threads"** |
| "Have I reached the right torque?" | Wrist F/T — Tz threshold |
| "Is the crimper closed all the way?" | RGB or a limit switch in the crimper assembly |

This step lives in the world of **force-feedback robotics**.
Vision is necessary but secondary; F/T is the primary sensor.

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **6 — F/T traces** | The headline asset. Three trace categories: (a) good screw-on — Tz ramps smoothly to ~0.4 N·m and plateaus. (b) cross-threading — Tz oscillates sharply, never plateaus. (c) crimp fire — Fz pulse for ~200 ms then drops. Each trace is short (1-2 s) and labelled with the outcome. |
| **5 — 6-DoF poses** | The cap pose throughout the screw-on, especially the *relative* `T_cap_to_vial_neck` pose. Tells you whether the cap is centred, tilted, or already engaged. |
| **3 — keypoint annotations** | The vial-neck centre pixel (same as Step 5's vial-mouth keypoint, just with an empty mouth) and the cap rim keypoints for sub-cm alignment from the wrist camera. |
| **2 — segmentation masks** | Cap, vial neck, gripper fingers — useful for the wrist-camera "is the cap aligned" classifier. |
| **11 — demonstrations** | If the screw-on is learned (rather than scripted), expert demos in sim of "good screw-on" trajectories are the natural training set for a Diffusion-Policy / ACT-style policy. |
| **12 — failure cases** | Cross-threaded cap; cap dropped during pick; cap upside-down (septum-side up); over-torqued (Tz overshoots, septum-crush flag); under-torqued (Tz never reaches plateau); vial cracked under force (a flag in the SDF physics model). |

## What is NOT worth generating here

- **Full-scene RGB pose datasets.** Capping is a wrist-camera
  task once the cap is picked. Overhead frames have almost no
  signal.
- **Fluid-level data.** Liquid does not move during capping.
- **OCR data.** No text on the cap that matters.

## Concrete dataset shape

```
synthetic_capping/
├── images/
│   ├── wrist_<traj>_<frame>.jpg            # eye-in-hand view of the neck
│   └── wrist_<traj>_<frame>.depth.npy
├── labels/
│   ├── relative_poses_<traj>_<frame>.json  # cap-to-neck offset + tilt
│   ├── keypoints_<traj>_<frame>.json       # neck centre, cap rim points
│   └── outcome_<traj>.json                 # {"result": "good" | "cross_thread"
│                                            #                | "under_torque" |
│                                            #                | "over_torque",
│                                            #  "final_torque_nm": 0.38}
└── traces/
    ├── ft_screw_<traj>.csv                 # Fxyz Txyz at 1 kHz
    └── joints_<traj>.csv
```

Notice the **trace files dominate** here — RGB is small, the
useful data is high-frequency force.

## Why simulation is harder here than for other steps

Gazebo's contact-force simulation is rigid-body and approximate.
Modelling the *threading* of a screw cap — the small Tz ripple
as the threads engage — needs either a hand-written plugin that
fakes the ripple from the cap's vertical position, or moving to
a higher-fidelity simulator (Isaac Sim with PhysX 5, or
MuJoCo's contact-force traces).

For a first pass, the F/T traces can be **scripted in software**
(not actually simulated): pick a clean exponential ramp +
plateau for "good," add a noisy oscillation for "cross-thread,"
add a flat-line for "missed threads." This is enough for a
3-class classifier and matches the project's pragmatic style
elsewhere (see how the solvent bottle "pours" by shrinking a
visual prop instead of simulating fluid).
