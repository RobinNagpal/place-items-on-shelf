# 14 — Barcode / QR-code reader at the scan station

Implements checklist item **14** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Mapped onto the HPLC autosampler v1 cell — the autosampler spec
*requires* logging `(barcode → tray slot)` for every vial loaded, so
this exercise is the step that produces that log.

## What this exercise does, in plain English

Each vial has a tiny QR code printed on its body. The arm has
already decided which vials to load to the tray (item 21 logic).
When the arm picks one of those vials, it carries it to a **fixed
scan station** — a small second camera positioned between the
source rack and the destination tray — and **spins the vial in the
gripper** until the camera can see the QR. The decoder reads the
text (e.g. `"B-2024-0119"`), the controller writes
`(tray_slot → "B-2024-0119")` to LIMS, then the arm continues to
the tray slot and releases.

```
       source rack                    scan station                   destination tray
       (overhead camera)              (side camera, fixed)            (overhead camera)
            │                                │                                ▲
            │ pick                           │ spin + decode                  │ place
            ▼                                ▼                                │
   above_source -> grasp -> lift -> above_scan -> [spin in place] -> above_dest -> lower -> release
                                                       │
                                                       │  decoded barcode
                                                       ▼
                                                  LIMS log
                                                  (tray_slot, barcode)
```

The whole thing is *one extra waypoint* in the pick-and-place
sequence from exercise 21 — and a tiny library this exercise
provides.

## Quick answers (read this first)

**Does the arm have to take the vial to a camera?**
**Yes.** The overhead camera that finds vials from above (exercise
4) can't reliably see the side label — labels are wrapped around
the cylinder, and from straight up they're foreshortened or
occluded. So we add a second, small, **fixed** "scan-station"
camera mounted to the side, and the arm brings the vial to it.
That station is just a known pose in `base_link` frame — one
waypoint in the pose sequence.

**The barcode can be on any side of the vial. How does the arm
know which side?**
**It doesn't, and it doesn't have to.** The wrist (joint J6 on a
6-DoF arm) rotates the gripper about the vial's own vertical axis
*without* moving the vial's centroid. So at the scan station the
arm just **spins in place** in small steps (~30°), tries the
decoder on each camera frame, and stops the moment a code reads.
One full rotation guarantees the label faces the camera at some
point. The `spin_and_decode` helper in
[`barcode_reader.py`](barcode_reader.py) does exactly this loop.

**Why scan only the vials going to the tray, not every vial in the
source rack?**
Two reasons:

1. **It would be wasteful.** Spinning every vial in the rack to
   read its label takes ~1 second each — 100+ s for a full rack
   the controller may not even load.
2. **The LIMS only wants `(barcode → tray_slot)`.** Source-rack
   slot identity is irrelevant — what matters is what's in the
   tray when the run is done. So scanning happens *on the path*
   from source to tray, only for the vials we are actually
   loading. This is the order the spec calls for.

## More common questions

**What kind of gripper does the spinning?**
No special gripper — the **wrist joint (J6)** does it. Every 6-DoF
arm (including the myCobot 280) has J6 as a wrist rotate; nudging
it spins whatever the gripper is holding around its own axis
without moving the rest of the arm. Use a normal parallel-jaw
gripper with rubber / silicone fingertips so the vial doesn't
slip. A 4-DoF arm without a wrist rotate would need either a
rotating gripper, or a scan station with 4 cameras (one per side).

**How long does one scan take?**
About **250 ms per spin step**: ~200 ms wrist nudge + ~30 ms
camera frame wait + ~10 ms decode. The barcode is found at a
random angle, so on average it reads after ~6 steps:
**~1.5 seconds per vial average**, **~3 seconds worst case**.
That comfortably fits the 10-20 second autosampler cycle.

**Should the arm spin all 12 angles every time, or stop early
when the barcode is detected?** Two valid designs:

- **Option A — always spin all 12.** Deterministic timing
  (~3 s per vial), no signalling needed between the camera and
  the arm. Pick this when you want predictable cycle times — easy
  to plan a batch around.
- **Option B — stop early on first detection.** The arm decodes
  after each step; the moment a code reads it leaves the scan
  station for the tray. Saves ~half the scan time per vial
  (~1.5 s average vs ~3 s). Pick this when throughput matters
  more than predictability.

The library we ship implements Option B: `spin_and_decode`
breaks out of the loop the moment `decode_barcode` returns a
code. So in a single-node setup (arm node runs the decoder
itself) you get early-stop for free. For a two-node setup where
a separate scanner node publishes `/barcode/decoded` and the arm
subscribes, the arm leaves on the first published message —
same early-stop behaviour, more wiring.

**What information do we get from the barcode, and can we store
it in a database with timestamps?**
You get back **the exact text printed on the label** — a vial ID
like `"B-2024-0117"`, a URL, a JSON blob, or whatever the lab
chose to print. **Yes, store it.** Typical row:

| Column | Example |
|---|---|
| `run_id` | `"run-2026-06-05-001"` |
| `tray_slot` | `3` |
| `barcode` | `"B-2024-0119"` |
| `scanned_at` | `2026-06-05 11:32:47.812 UTC` |

In production the arm controller does an HTTP POST / SQL insert
the moment the spin loop returns success. The demo writes the
same shape to `output/lims.csv` — same data, smaller plumbing.

## How it ties into other exercises

- **Exercise 19** — `setPoseTarget` to drive the arm to
  `above_scan_station`. The scan-station pose is just one more
  Cartesian goal.
- **Exercise 18 / SRDF** — alternatively, name the scan-station
  pose in the SRDF and use `setNamedTarget("above_scan")`.
- **Exercise 20** — `AttachedCollisionObject` while the vial is in
  the gripper, so the planner knows there's a vial-sized cylinder
  attached to `link6_flange` and avoids brushing it against the
  scan-station housing.
- **Exercise 21** — the orchestrator that strings the whole
  sequence together (`pick → scan → place`). This exercise plugs
  one extra step in between `pick` and `place`.
- **Exercise 13 (HSV colour)** — colour is the coarse "this is one
  of the red vials"; barcode is the precise *which* red vial.
  Often used together: HSV picks subsets, barcode identifies
  individuals.

## What comes out, and how the orchestrator uses it

`barcode_reader` exposes **two functions**:

| Function | Returns |
|---|---|
| `decode_barcode(bgr_image)` | the decoded text as a string, or `None` if no code was found in this frame |
| `spin_and_decode(frame_provider, max_steps)` | `(text, step_found)` on success, `(None, max_steps)` on time-out |

`frame_provider(step)` is a callback the **arm controller** writes.
It does three things every call:

1. Nudge the wrist by `360 / max_steps` degrees.
2. Capture one frame from the scan-station camera.
3. Return that frame as a BGR `numpy` array.

Real code in the arm node looks roughly like this:

```python
import rclpy
from barcode_reader import spin_and_decode
# arm = MoveGroupInterface("arm"); bridge = CvBridge();
# scan_image_sub = ...latest scan-station camera frame stored as self._latest_bgr...

def frame_provider(step):
    arm.set_joint_value_target({"joint6": step * (2 * math.pi / 12)})
    arm.move()                          # tiny wrist rotation
    rclpy.spin_once(node, timeout_sec=0.2)
    return self._latest_bgr             # latest frame from the scan camera

code, step = spin_and_decode(frame_provider, max_steps=12)
if code is None:
    log.warn("vial timed out at scan station; flag for manual check")
else:
    lims.write(tray_slot=current_tray_slot, barcode=code)
```

## Workflow (data flow only)

```
arm at above_scan_station, holding the vial
            │
            ▼
   spin_and_decode(frame_provider, max_steps=12)
            │
            │  for step in 0..11:
            │      frame_provider(step):
            │          nudge wrist by 30 deg
            │          grab one frame from scan camera
            │          return BGR numpy image
            │      code = decode_barcode(frame)
            │      if code is not None: STOP
            ▼
   (decoded_text, step_found)   <-- or (None, max_steps) on timeout
            │
            ▼
   if decoded_text is not None:
       LIMS log: (tray_slot, decoded_text)
   else:
       flag vial as "unidentified", skip it
```

## What "Done when" means here

The checklist asks for **5 different codes correctly mapped to 5
objects**. [`demo.py`](demo.py) covers it without needing Gazebo:

1. Generate 5 QR codes (`B-2024-0117` … `B-2024-0121`) with the
   `qrcode` library.
2. For each code, render 12 synthetic "scan-station" frames at 12
   spin angles. The QR is visible at only one angle (and the two
   neighbours); the other 9 frames show only the vial body.
3. Run `spin_and_decode` and confirm all 5 codes are read and
   logged to `output/lims.csv` as `(tray_slot, barcode)` pairs.

A `PASS` line for every vial *is* the checklist's "Done when".

## Example run

```bash
# 1. install deps
pip install -r requirements.txt
# pyzbar also wants libzbar0 from apt; the demo falls back to
# cv2.QRCodeDetector if it's missing (no install needed for QR-only).
#   sudo apt install libzbar0     # only if you want pyzbar / 1D barcodes

# 2. run
python demo.py

# expected:
# [demo] decoder         : pyzbar           (or "cv2.QRCodeDetector (fallback)")
# [demo] spin steps      : 12 (every 30 deg)
# [demo] vials to scan   : 5
#
# [demo] tray slot 1: decoded 'B-2024-0117' on spin step 0 (visibility was at 0)  [PASS]
# [demo] tray slot 2: decoded 'B-2024-0118' on spin step 2 (visibility was at 3)  [PASS]
# [demo] tray slot 3: decoded 'B-2024-0119' on spin step 5 (visibility was at 6)  [PASS]
# [demo] tray slot 4: decoded 'B-2024-0120' on spin step 8 (visibility was at 9)  [PASS]
# [demo] tray slot 5: decoded 'B-2024-0121' on spin step 0 (visibility was at 11) [PASS]
#
# [demo] LIMS log written to ./output/lims.csv
# [demo] 5/5 vials successfully scanned
#
# [demo] PASS — checklist 'done when' bar requires 5 codes -> 5 mappings.
```

Then open `output/vial_*_visible.png` to see the frame the
controller actually decoded for each vial.

## What this exercise is **not**

| Need | Where it is solved |
|------|--------------------|
| Picking up the vial | exercise 21 (pick-and-place) |
| Knowing **where** the vial is on the bench | exercise 8 (depth centroid) |
| Telling vials apart by **cap colour** (coarse subset) | exercise 13 (HSV) |
| Driving the wrist nudge | exercise 19 (Cartesian pose goal) |
| Logging the result somewhere real | out of scope — `demo.py` writes a CSV; production hits a LIMS REST API |

This exercise is one self-contained slice — *the scan step* — that
plugs into exercise 21's pose sequence.

## What's next

- **Exercise 21** now grows from 5 poses to 7 poses per vial:
  `above_source → grasp → lift → above_scan → above_dest → lower
  → release`, with `spin_and_decode` called between `above_scan`
  and `above_dest`.
- The dim `output/lims.csv` becomes a real LIMS REST call once
  there is a controller wrapper for it.
