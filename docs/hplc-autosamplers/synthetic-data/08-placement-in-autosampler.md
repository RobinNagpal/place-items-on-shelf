# 08 — Synthetic data for Placement in the autosampler

> **Project status: modelled.** This is the project's
> **headline task** — the v1
> [`requirements/00-spec-summary.md`](../requirements/00-spec-summary.md)
> pins ±1 mm placement precision and ≤ 20 s cycle time against
> this routine. The Gazebo world is
> [`gazebo_worlds/08-placement-in-autosampler/`](../../../gazebo_worlds/08-placement-in-autosampler/).
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/08-placement-in-autosampler.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/08-placement-in-autosampler.md).

## What the robot does

For each of 12 capped + labelled vials in the source rack, in
worklist order (controller-supplied):

1. Pick the next vial from the source rack.
2. Move it under the barcode reader's red window — wait for the
   scan to confirm the label matches the controller's
   expectation for this step.
3. Move the vial over the target slot on the destination tray
   (use the ArUco fiducial on the alignment plate to re-zero
   first if needed).
4. Lower it gently into the slot until the cap rests on the
   tray surface.
5. Release the vial and lift the gripper clear.

The destination tray is a 10 × 10 grid of Ø14 mm slot mouths at
18 mm pitch. **Slot accuracy: ±1 mm.**

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Which vial is next?" | Software state (controller's worklist) |
| "Where is the source rack right now?" | Overhead RGB + ArUco fiducial on the rack corner |
| "Is the next source slot full? What cap colour?" | Overhead RGB — HSV / classical CV on cap colour, or YOLO if you want the heavyweight option |
| "What does the barcode on this vial say?" | Side / scan-station RGB → `pyzbar` decode |
| "Does the decoded barcode match the controller's expected value?" | Software — string compare |
| "Where is the destination tray right now?" | Overhead RGB + ArUco fiducial on the alignment plate |
| "Which destination slot for this vial?" | Software — worklist lookup |
| **"Has the vial cap touched the tray surface?"** | **Wrist F/T — Fz crosses ~1 N threshold** |
| "Did the vial seat cleanly or skew?" | RGB + relative pose between vial body and slot |

The headline perception facts:

1. The **rack and tray poses come from ArUco fiducials**, not
   from a learned model. The alignment plate exists specifically
   for this.
2. The **barcode scan** is the only *content* perception
   problem.
3. The **lower-into-slot** decision is a force decision, not a
   vision decision.

This split is why [`../perception-design-decisions.md`](../perception-design-decisions.md)
argues that "simpler than YOLO" is the right call for v1.

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **5 — 6-DoF poses** | The single most important type. Per-frame poses of all 12 vials, the source rack, the destination tray, the alignment plate, the barcode reader stem, the HPLC instrument body, and the gripper. Source rack and tray pose ground truth lets you smoke-test the ArUco-based localisation. |
| **8 — barcode renders** | Per-vial barcode payload renders (Code-128 or QR). Tag each vial's label texture with a known string at SDF-build time; the synthetic dataset's ground truth is that string. Used to validate the `pyzbar`-based reader before deploying it. |
| **3 — keypoint annotations** | (a) ArUco-marker centre and four corners on the alignment plate (sub-cm precision required). (b) Source rack corner keypoints (without ArUco, the four-corner rectangle is the next-cheapest pose proxy). (c) Tray slot centres (one keypoint per slot in the 10 × 10 grid). |
| **6 — F/T traces** | The "lowering into slot" trace: Fz baseline → linear rise as the vial enters → sharp jump when the cap touches the tray surface. The jump threshold is the stop signal. Also the pick-up lift trace (different signature for "full vial" vs "empty slot at the position the worklist expects"). |
| **2 — segmentation masks** | Per-cap-colour mask: `cap_red`, `cap_blue`, `cap_green`, `cap_orange`, `cap_white` (one per worklist colour code). Lets the HSV classifier be smoke-tested against pixel-accurate ground truth. |
| **7 — joint-state traces** | Full-cycle 10 × 10 grid sweeps: 100 placement trajectories per run, joint efforts logged. Used for the "a particular slot consistently shows a torque spike" check from the v1 spec — catches a slightly mis-aligned tray before a vial breaks. |
| **11 — demonstrations** | A scripted "expert" placement loop: 200 + full pick-scan-place trajectories with randomised tray pose (±5 mm shift, ±3° rotation) inside the alignment-plate tolerance window. Behaviour-cloning target: learn the small correction that the v1 hard-coded approach skips. |
| **12 — failure cases** | Wrong barcode (drop and re-pick); slot already occupied; tray rotated > 3° (alignment-plate sanity check fires); cap colour mismatches worklist row; vial dropped during pick; vial tilted in the slot after release. |

## What the Gazebo world already gives you free

Looking at [`ketchup_placement_in_autosampler.sdf`](../../../gazebo_worlds/08-placement-in-autosampler/ketchup_placement_in_autosampler.sdf):

- All 12 vials are named with the worklist position and the
  cap colour (e.g. `vial_pos3_A_r1`), so the ground truth pairs
  (slot index ↔ cap colour ↔ barcode payload) are recorded in
  the SDF directly.
- The alignment plate's ArUco-style fiducial patch is a textured
  visual — you can swap the texture file to vary the marker ID
  per scene.
- The destination tray's 100 slot-mouth rings are flat Ø14 mm
  rings on the tray top; their world coordinates derive
  trivially from the tray pose + the 18 mm pitch + the tray's
  "position 1" corner marker.
- The barcode reader has a small red emissive window — the
  exact scan-trigger pixel-region is the SDF box for that
  emissive, computable per frame.

## Concrete dataset shape

```
synthetic_placement/
├── images/
│   ├── overhead_<traj>_<frame>.jpg
│   ├── overhead_<traj>_<frame>.depth.npy
│   ├── scan_station_<traj>_<frame>.jpg     # side camera near the reader
│   └── tray_close_<traj>_<frame>.jpg       # close-up on the destination slot
├── labels/
│   ├── poses_<traj>_<frame>.json
│   ├── aruco_<traj>_<frame>.json           # plate / rack ArUco IDs + corners
│   ├── barcodes_<traj>.json                # per-vial payload
│   ├── slot_grid_<traj>.json               # 10×10 slot centres in base frame
│   ├── masks_<traj>_<frame>.png            # cap-colour masks
│   └── placement_outcomes_<traj>.json      # per-vial success / failure tag
├── traces/
│   ├── ft_lower_<traj>_<vial_id>.csv       # Fz time-series per placement
│   ├── joints_<traj>.csv
│   └── ft_pick_<traj>_<vial_id>.csv
└── metadata.json
```

## Smallest useful first dataset

For v1 cell, the minimal-but-useful set:

- 100 trajectories at nominal tray pose, full 12-vial worklist
  per trajectory = 1 200 placement events.
- × 5 tray-pose perturbations (within the alignment-plate
  tolerance window) = 6 000 placement events.
- × 3 lighting setups = 18 000 placement events.

For each event you get one **overhead frame**, one **scan-station
frame**, one **tray close-up**, and one **F/T trace**. That is
enough for: ArUco smoke-testing, barcode-decoder validation,
slot-grid regression, and the lowered-into-slot trace
classifier.

## How the synthetic dataset cross-checks against the v1 spec

The v1 spec calls out three measurable bars:

| Spec bar | Synthetic-data check |
|---|---|
| **±1 mm slot precision** | Trajectory log: final vial XY pose vs. nominal slot XY. RMSE across 18 000 placements. |
| **≤ 20 s mean cycle time** | Trajectory log: timestamp between successive pick events. Mean across 100 nominal trajectories. |
| **0 mis-slots per 1 000 vials** | Outcome log: count `wrong_slot` failures across all events. |

Those three numbers fall straight out of the dataset above — no
additional bookkeeping needed. Generating the dataset and
generating the spec-conformance report are the same exercise.
