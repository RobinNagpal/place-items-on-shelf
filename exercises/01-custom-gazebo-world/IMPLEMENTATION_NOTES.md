# Implementation notes — 01 Custom Gazebo world

## Why these dimensions

All numbers are pinned to the requirements:

| Element | Value | Source |
|---|---|---|
| Bench top at z = 0.775 m | bench-height baseline | [`requirements/04`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md) |
| Cell ≤ 40 × 40 cm | working area | [`requirements/04`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md) |
| Vial: 12 mm OD × 32 mm, ~8 g, PP cap | reference vial | [`requirements/01`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md) |
| Source rack: 5 × 10 footprint | MicroSolv 50-position | [`requirements/01`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md) |
| Tray on bench, not in HPLC | Agilent "external tray" pattern | [`requirements/01`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md) |
| Slots ~14 mm with ~1 mm clearance | Agilent 100-position classic tray | [`requirements/01`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md) |

The rack and tray footprints in the SDF are slightly *smaller* than
the catalogue numbers (90 × 180 mm rack, 140 × 140 mm tray) so the
far corner of each peripheral stays inside the myCobot 280's
**280 mm reach** — see [`02-read-and-annotate-urdf/`](../02-read-and-annotate-urdf/)
for the per-slot reach check.

## Why only three vials

The "Done when" check is "drag a vial with the mouse" — one would do.
Three vials with three cap colours also gives a stand-in for
[`requirements/02`](../../docs/hplc-autosamplers/requirements/02-environment.md)
lab convention (cap colour codes sample type), useful when later
exercises start filtering by cap colour.

Spawning all 50 rack slots and all 100 tray slots would clutter the
scene without changing what this exercise tests.

## Why the rack and tray are solid blocks

Modelling the actual cylindrical wells would multiply the link count
by ~150 and run the SDF parser long without changing anything visible
or testable here. Vials sit *on* the rack surface — per
[`requirements/01`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md)
~25–30 mm of vial sits above the rack — so the holes do not need
to be modelled for the pick geometry to be correct.

## Failure modes

- **Arm missing** — `GAZEBO_MODEL_PATH` / `GZ_SIM_RESOURCE_PATH` does
  not include the `mycobot_280` directory. Everything else still
  renders.
- **Vials fall through the rack** — vial pose z is too low. Should be
  `bench_top + rack_height + half_vial = 0.775 + 0.050 + 0.016 = 0.841`.
- **Vials tip over on spawn** — fix by lowering them slightly so they
  rest on the rack rather than drop. The current `z = 0.841` puts
  them flush with the rack surface.
- **Black scene** — `model://sun` failed to load. Classic needs an
  internet connection on first run to populate its model cache.

## Things this exercise does *not* do

No controllers, no MoveIt, no camera, no perception — those are
items 4, 8, 18, and 21. No barcode reader stand (item 14). No
collision objects for MoveIt's planning scene (item 20). The world
is the *canvas*; the other exercises paint on it.
