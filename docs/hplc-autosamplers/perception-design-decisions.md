# Perception design decisions for the autosampler cell

Four practical questions that come up when deciding how the autosampler
cell should "see" vials. The answers below are written for the v1 cell
(5×10 source rack, 10×10 destination tray, single myCobot 280 Pi).

---

## 1. How accurate is YOLO + depth camera, and does industry use it?

### Accuracy

For a typical setup (Intel RealSense D435, ~40 cm working distance, a
well-trained YOLO/SAM mask, a decent hand-eye calibration), expect:

| Source of error | Typical contribution |
|---|---|
| YOLO mask edges (a few pixels) | ±1–2 mm at 40 cm |
| Depth camera noise (RealSense @ 40 cm) | ±1–3 mm |
| Hand-eye calibration residual | ±1–2 mm |
| Camera intrinsic calibration residual | ±0.5 mm |
| **Combined (RSS)** | **~3–5 mm total position error** |

Rule of thumb: **"good to about half a centimetre"** end-to-end. Enough
for picking warehouse boxes, fruits, lab tubes (with a forgiving
gripper). **Not** enough for inserting a pin into a hole or screwing a
cap on without a compliance mechanism.

If you need sub-mm accuracy you stop using YOLO+depth as the final step
and layer something more precise on top — ArUco fiducials, a vision
servoing loop near the goal, or a touch / force probe that searches for
the exact spot.

### Industry use

**Yes — extremely widely.** YOLO (and equivalent detectors: Detectron2,
Mask R-CNN, SAM, PaddleDetection) plus a depth sensor is the dominant
recipe for modern pick systems. Common deployments:

- **Warehouse / logistics bin-picking** — Amazon Robotics, Berkshire
  Grey, Symbotic, Covariant. They pick mixed-SKU items from totes.
- **Parcel sorting** — FedEx, UPS, DHL automated sortation lines.
- **Food handling** — Soft Robotics, Pickle Robot for produce sorting,
  salad-line assembly, fish processing.
- **Light assembly** — automotive (kitting screws/connectors),
  electronics (placing parts onto trays).
- **Lab automation** — Opentrons, Hamilton, Tecan are mostly
  fixed-coordinate, but newer "flexible" liquid handlers use YOLO+depth
  to find user-placed labware.
- **Agriculture** — strawberry, apple, tomato pickers (FFRobotics,
  Tortuga).

Where industry **doesn't** use it: precision assembly (chip placement,
watchmaking), surgery, anything where a 5 mm error is catastrophic.
Those use precise jigs + force feedback + sub-mm metrology.

---

## 2. Best camera position for the autosampler?

Three viable mounting choices and their trade-offs:

| Mount | Pros | Cons | Verdict |
|---|---|---|---|
| **Overhead fixed** (looking down at the rack from ~40–50 cm above) | sees the whole rack at once, no inter-vial occlusion, depth gives cap-top Z, simple wiring | can't read side labels, slightly lower pixel density per vial | **Yes — primary camera** |
| **Side fixed** (looking horizontally at the rack) | sees labels easily | front vials occlude back vials, ambiguous depth for things behind | bad for finding vials; **good as a scan-station camera** (exercise 14) |
| **Eye-in-hand** (on the wrist) | can move close for fine accuracy | slow (move arm before every measurement), no scene-wide view, more calibration work | use only when overhead isn't enough |

**Recommended layout for v1 of the cell:**

- **Camera A** — overhead RGBD camera (RealSense D435 or D455)
  ~40–50 cm above the source rack, looking straight down. Used by
  exercises 04 / 07 / 08 for "which slots are full, what colour, and
  where exactly is each cap in base frame."
- **Camera B** — small side-mounted RGB camera at a fixed pose between
  the source rack and the destination tray. Acts as the scan station
  from exercise 14.

40–50 cm is a sweet spot: a RealSense at that range gets ~0.5–1 mm
per pixel, more than enough resolution for a 12 mm vial cap. Higher
→ less resolution. Lower → can't fit the full 5×10 rack in one frame.

---

## 3. Is the depth-camera centroid the centre of the vial? And what does MoveIt actually need?

**Short answer: the centroid you get is the centre of the cap's top
surface, not the centre of the whole vial body.** Why:

- With an overhead camera, the cap is the only thing the camera can
  see — the vial body is underneath the cap and hidden.
- The YOLO / seg mask only labels cap pixels, so the `(u̅, v̅)` centroid
  is the geometric centre of the cap *as seen from above*.
- The median depth is the depth to the *top of the cap* (~the highest
  visible surface).

Raw output of exercise 08 is therefore:

```
(X_cap_centre, Y_cap_centre, Z_cap_top)   in robot base frame
```

That's **not** the pose you give MoveIt for picking. You need the pose
where the **gripper closes**, which is on the vial body, just below the
cap. Convert with a fixed offset from the vial datasheet (HPLC vials
are standardised — cap height ~6 mm, body diameter 12 mm):

```
target.x = X_cap_centre
target.y = Y_cap_centre
target.z = Z_cap_top - cap_height - body_grip_offset
        ≈ Z_cap_top - 8 mm   (grip ~2 mm below the cap shoulder)
target.orientation = "approach straight down" (quaternion pointing -Z)
```

Also decide the **TCP frame** (tool centre point) — usually the point
between the gripper fingers. MoveIt's `setPoseTarget` plans to put
**the TCP**, not the wrist flange, at that pose. So the offset above is
"where the TCP should be when the fingers close on the vial body."

**Rack-constraint check.** Vials sit in well-known rack slots. So
`(X, Y)` from YOLO+depth should be **within 1–2 mm of the rack-slot
centre** (which is geometry, not perception). If it's not, the rack has
shifted or the calibration is off. Two policies:

- **Trust perception**, use the raw `(X, Y, Z)` — simplest.
- **Snap to grid**, treat YOLO+depth as "which slot is occupied," then
  use the nominal slot-centre coordinates for X, Y — more accurate when
  the rack is securely fixtured.

The autosampler v1 spec assumes the rack is in a known fixture, so the
**snap-to-grid** option is usually the safer one in practice.

---

## 4. Is there a better approach than YOLO for this case?

**For the autosampler specifically: yes, several — and they're all
simpler than YOLO.** The reason is that the autosampler has *strong
priors* that general-purpose pick systems don't:

1. The rack is in a **known fixed location** (bolted into a fixture).
2. There are **only 50 possible vial positions** (5×10 grid).
3. Vials are **all the same size and shape** (HPLC standard).
4. The only variation is **cap colour** and **which slots are
   occupied**.

Given those, simpler-than-YOLO options:

### Option A — pure geometry, no perception at all

If the rack is fixtured, every slot's `(X, Y, Z)` is **known in
advance** in base frame. Picking becomes:

> "Go to slot (3, 7). Pick. Done."

No YOLO, no depth camera, no calibration of the camera-to-arm
transform. You only need to know whether a slot is occupied (a single
photoresistor under the slot, or a microswitch, would do it).

This is how **commercial HPLC autosamplers actually work** — they
don't have cameras at all. Rack identity and slot occupancy come from
the user telling the system "I loaded vials in slots 1–25."

### Option B — ArUco on the rack + geometry

Stick an ArUco marker on the corner of the rack. One RGB frame finds
the marker, gives you the rack's 6-DoF pose, then every slot follows
from rack geometry. Works even if the rack shifts a bit between runs.

- Per-frame compute cost: trivial (faster than YOLO by 1000×).
- Accuracy: 1–3 mm at our working distance.
- Implemented in [`../../exercises/10-aruco-pose/`](../../exercises/10-aruco-pose/).

**Recommended for autosampler v1.** The rack is fixtured, so an ArUco
gives both pose and a slot grid for free.

### Option C — HSV cap segmentation + geometry

The caps come in a handful of colours (red / blue / green). HSV
thresholding + connected components (exercise 13) tells you "slot 3
has a red cap, slot 7 has blue, slot 12 is empty." Combine that with
the geometric rack positions and you have everything MoveIt needs.

- Way cheaper than YOLO (no model, no GPU, no training).
- More robust on the colour question (YOLO trained on 5 classes can
  confuse pink with red; HSV doesn't).
- Doesn't handle the "is the cap there at all" question as well as
  YOLO — fixed by using cap area threshold or a single classical blob
  detector on greyscale.

### When YOLO is still the right answer

YOLO + depth is the right tool when the priors above **don't** hold:

- Vials placed in arbitrary positions on a bench (not in a rack).
- Mixed labware (vials of different sizes, plates, tubes) on the same
  surface.
- Vials might be tipped over, crowded, partially hidden.
- You don't know in advance which racks / slots are in the scene.

For the autosampler v1 cell, none of those are true — so a simpler
approach (ArUco + HSV + geometry) gives more accuracy with less code
than YOLO + depth, and is what we'd actually deploy. The YOLO
exercises are still valuable in the curriculum because they teach the
general pipeline, which you'll need the moment the cell stops being
"neat rows in a known fixture."

---

## Quick summary

| Question | Short answer |
|---|---|
| YOLO+depth accuracy | ~3–5 mm; good for picking, not for assembly |
| Industry use | Yes, dominant recipe for warehouse / logistics / agri / lab pick |
| Best camera spot for autosampler | Overhead fixed RGBD at 40–50 cm above the rack + side scan-station camera |
| Centroid = vial centre? | No — it's the cap-top centre. Subtract ~8 mm in Z to get the grip pose |
| Better than YOLO here | Yes — ArUco on the rack + HSV cap detection + rack geometry is simpler and more accurate for v1 |
