# 04 — Synthetic data for Filtering

> **Project status: modelled.** The Gazebo world is
> [`gazebo_worlds/04-filtering/`](../../../gazebo_worlds/04-filtering/).
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/04-filtering.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/04-filtering.md).

## What the robot does

The most multi-stage step in the whole workflow. **Spin → draw →
filter:**

1. Pick up the source flask (dilution from Step 3).
2. Tilt it over the pre-spin Falcon tube to pour the dilution in.
3. Put the flask back.
4. Pick up the pre-spin Falcon tube from the rack.
5. Place it in the centrifuge rotor well.
6. Close the centrifuge lid and start the spin. Wait.
7. Open the lid. Take the post-spin tube out.
8. Pick up the **bare syringe**.
9. Dip its Luer tip into the top of the post-spin tube and pull
   the plunger back to draw up the **clear supernatant** —
   carefully, avoiding the pellet.
10. Pick up the 0.45 µm syringe filter (sitting separately on
    the bench, **not** pre-attached) and screw it onto the
    syringe's Luer tip.
11. Hold the filter outlet over the receiving beaker.
12. Push the plunger down — clean filtrate drips into the beaker.
13. Set the syringe + filter down.

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Where is the centrifuge well opening?" | Overhead RGB + depth |
| "Is the centrifuge lid open or closed?" | RGB classifier on the lid pose |
| "Has the spin finished?" | Centrifuge timer LCD (OCR) **or** a topic the centrifuge driver publishes |
| **"Where is the pellet / supernatant boundary inside the post-spin tube?"** | **Side-view RGB + segmentation — the hardest visual question in this step** |
| "Is the syringe Luer tip in the supernatant or in the pellet?" | Depth + the boundary line from above |
| "How full is the syringe?" | RGB on the barrel (graduations + plunger position) |
| "Did the filter screw on?" | RGB (filter pose relative to syringe tip) + F/T (twist torque) |
| "Has the filter clogged?" | Wrist F/T while pushing — push force rising sharply means clog |
| "How much filtrate is in the receiving beaker?" | RGB liquid-level on the beaker side |

The **pellet / supernatant boundary** is the make-or-break
perception problem. Reach in too low and the pellet contaminates
the syringe. Reach in too high and you don't pull enough liquid.

## Useful synthetic-data types

| Type | Purpose here |
|---|---|
| **2 — segmentation masks** | The headline asset. Per-pixel masks of `pellet`, `supernatant`, `tube_wall`, `tube_cap`, `headspace_air`. The pellet-supernatant boundary mask is what teaches a model to find the safe draw depth. |
| **3 — keypoint annotations** | A single horizontal line keypoint at the pellet-supernatant interface, expressed as a `(left_pixel, right_pixel)` pair so the slope of the meniscus is captured too (centrifuge tubes are usually held vertical so this is straight, but useful sanity check). |
| **5 — 6-DoF poses** | Per-frame poses of `source_flask`, `pre_spin_tube`, `post_spin_tube`, `tube_rack`, `centrifuge_lid`, `syringe`, `syringe_filter`, `receiving_beaker`. The separate-filter pose matters — Step 9 of the workflow is specifically "filter is not pre-attached." |
| **6 — F/T traces** | Three time-series that matter: (a) **plunger draw force** — should be low and steady; a sudden jump means the tip hit the pellet. (b) **plunger push force through filter** — rises gradually; a sharp rise means clog. (c) **filter-screw torque** — should plateau when the threads bottom out. |
| **8 — text renders** | The centrifuge timer display (e.g. `02:47` remaining) and the speed setting (e.g. `4000 rpm`) as a small OCR set. Beginner-friendly because the digits are 7-segment. |
| **9 — fluid-level frame sequences** | The supernatant column height inside the syringe barrel as the plunger pulls back, frame-labelled with `syringe_volume_ml`. Also the drip-by-drip fill of the receiving beaker, labelled with `beaker_volume_ml`. |
| **11 — demonstrations** | A scripted "good draw" set: 100+ trajectories where a sim-only expert lowers the Luer tip to exactly 5 mm above the pellet boundary, draws 5 mL, raises. The boundary depth is randomised per trajectory. Behaviour-cloning target: learn the safe-margin policy. |
| **12 — failure cases** | Tip too low (drew pellet — supernatant inside syringe contains pellet specks); over-tightened filter (cracked Luer); clogged filter (forced-push trace + filter back-pressure); dropped filter on the bench; lid still closed when arm reached in. |

## What the Gazebo world already gives you free

Looking at [`ketchup_filtering.sdf`](../../../gazebo_worlds/04-filtering/ketchup_filtering.sdf):

- The world ships **both** a pre-spin tube (cloudy throughout)
  and a post-spin tube (pellet + supernatant layers visible).
  That means the **boundary** is hard-coded in the SDF — the
  exact pixel-line in the rendered frame is computable from the
  SDF geometry, no manual labelling.
- The syringe and the syringe filter are two *separate* models
  with two separate poses. Their attached / detached state is
  ground truth (boolean per frame: is the filter screwed on?).
- The centrifuge lid is a child link with a hinge joint, so its
  angle is exposed and "is lid closed" is one threshold away.

## Concrete dataset shape

```
synthetic_filtering/
├── images/
│   ├── overhead_<traj>_<frame>.jpg
│   ├── overhead_<traj>_<frame>.depth.npy
│   ├── side_view_<traj>_<frame>.jpg        # second camera at tube height
│   └── side_view_<traj>_<frame>.mask.png   # pellet / supernatant mask
├── labels/
│   ├── poses_<traj>_<frame>.json
│   ├── boundary_<traj>_<frame>.json        # {"pellet_top_pixel_y": 412}
│   ├── filter_state_<traj>_<frame>.json    # {"attached": true / false,
│                                            #  "clog_severity": 0.3}
│   └── lcd_<traj>_<frame>.json             # centrifuge timer text
├── traces/
│   ├── ft_plunger_draw_<traj>.csv
│   ├── ft_plunger_push_<traj>.csv
│   ├── ft_filter_screw_<traj>.csv
│   └── joints_<traj>.csv
└── metadata.json
```

Two cameras matter here, **not** the usual one: the overhead
camera for scene-wide pose ground truth, and a **side-view
camera** at tube height for the pellet-boundary problem. A third
"barrel close-up" camera helps for the syringe-volume question
but is optional in v1.

## Smallest useful first dataset

For the pellet-boundary mask specifically, aim for:

- 5 randomised pellet heights (15, 20, 25, 30, 35 mm above the
  conical bottom)
- × 5 randomised supernatant clarities (clear → very cloudy)
- × 5 lighting conditions
- × 100 trajectories per combination = **12 500 frames** total

For the F/T traces, 200 nominal "clean draw" + 200 "tip
hit-pellet" + 200 "clogged filter" trajectories is enough to
train a 3-class classifier that fires the right alarm.

## Open question

The "filter clog" trace is the most physically interesting and
the hardest to get right in Gazebo. The simulator can fake a
clog by inserting a synthetic spring force on the plunger that
ramps up over the push duration, but a realistic clog is
non-linear (pressure → flow rate → time). Two options:

- **Fake it cheaply** — linear ramp with a random clog onset
  time per trajectory. Good enough for the binary "is it
  clogging" classifier.
- **Add a small physical model** — explicit `dV/dt = k * dP / R`
  in a plugin where `R` grows over time. Worth doing only if a
  flow-rate-conditioned policy is on the roadmap.
