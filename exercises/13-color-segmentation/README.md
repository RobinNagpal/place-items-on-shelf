# 13 — Classical colour segmentation (no ML)

Implements checklist item **13** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Mapped onto the HPLC autosampler v1 cell defined in exercise 1 —
specifically the three coloured caps already in
[`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf)
(`vial_a1` red, `vial_a3` blue, `vial_a5` green).

## What this exercise does, in plain English

Find every vial cap in a top-down image of the bench and say what
colour each one is — using nothing but a few OpenCV calls. No
neural network, no training data, no GPU. Five lines of HSV
threshold math and a connected-components call.

Then turn those pixel detections into something an autosampler
controller can act on: a `{slot_id: color}` dictionary that answers
LIMS queries like *"load only the red-cap vials next."*

```
Overhead camera image (BGR)
        │
        │  cv2.cvtColor(BGR -> HSV)
        ▼
   HSV image
        │
        │  cv2.inRange(red ranges)
        │  cv2.inRange(blue range)
        │  cv2.inRange(green range)
        ▼
   binary mask per colour
        │
        │  cv2.morphologyEx(CLOSE)
        │  cv2.connectedComponentsWithStats
        │  (drop blobs outside [MIN_AREA, MAX_AREA])
        ▼
   list[CapDetection]   <- one per cap, with centroid + bbox + area
        │
        │  caps_to_slots(num_slots=5, image_width=W)
        ▼
   {1: "red", 2: "red", 3: "blue", 4: "green", 5: "red"}
```

That last dictionary is the whole point. The autosampler controller
takes `[s for s, c in d.items() if c == "red"]` and hands the list
to the pick-and-place script from exercise 21.

## Quick answers (read this first)

**One colour at a time, or many?** Both. `find_caps(image, "red")`
returns only red caps; `find_all_caps(image)` returns red + blue +
green in one call. Add a fourth colour by adding one entry to the
`CAP_HSV_RANGES` dict in [`cap_segmenter.py`](cap_segmenter.py).

**Will it match every red thing in the camera frame?** Yes — the
threshold knows "red pixel", not "cap". Two things keep this from
mattering in our scene: the **area filter** drops noise and
oversize blobs, and the autosampler **bench has nothing else red
on it**. For a busy lab room you would either crop to a rack ROI
first, or run YOLO (exercise 3) and segment only inside the boxes
it finds — same algorithm, smaller input.

**What comes out, and how do I hand it to MoveIt?** A list of
`CapDetection` objects, one per cap:

| Field | What it is |
|---|---|
| `color` | "red" / "blue" / "green" |
| `centroid_xy` | pixel (x, y) of the cap centre |
| `bbox_xywh` | pixel bounding box |
| `area_px` | blob size — closest thing to a confidence score |

Same shape as YOLO's `Detection2DArray`: `color` plays the role of
`class_id`, `area_px` is the rough confidence stand-in (classical
CV has no real confidence — the threshold either matches or not).

To drive MoveIt, two paths:

- **Autosampler v1 (slots in known places):** call
  `caps_to_slots(...)` → `{slot_id: color}` → look up the slot's
  world XYZ from rack geometry → `setPoseTarget(pose)` (exercise 19
  pattern).
- **Rack moved or vial in arbitrary place:** plug in exercise 11
  (intrinsics) + exercise 8 (depth) to convert the pixel centroid
  to a 3D point in the camera frame, then exercise 12 (hand-eye)
  to convert it to the robot's `base_link` frame, then
  `setPoseTarget`.

## Why classical CV is the right answer here

Three reasons we do **not** use a neural network for this:

1. **Colour is reliable.** Lab caps are bright, glossy, and very
   different from the bench, the rack, or the vial body. HSV
   thresholds nail them in two function calls. A YOLO classifier
   would be 1000× more code for the same answer.
2. **Easier to debug.** When the segmenter fails, you can open the
   binary mask in a viewer and see *exactly* which pixels were
   counted. Nothing is hidden.
3. **Cheaper to run.** The whole pipeline is sub-millisecond per
   frame on a Pi-class CPU — no model loading, no inference
   runtime, no `.onnx` files.

The flipside: classical CV breaks the moment colour stops being
reliable (different bulb temperature, glare from a window, dirty
caps). That's why this exercise is *one tool in the toolbox* — the
YOLO detector (exercise 3) and instance segmentation (exercise 7)
handle the cases where colour alone doesn't cut it.

## Core concepts (one paragraph each)

### Why HSV and not RGB

In **RGB**, the same red cap photographed under bright sun and dim
shade has very different `(R, G, B)` values — all three channels
move together when the light changes. In **HSV** (Hue, Saturation,
Value), the *hue* channel only encodes "what colour" — bright red
and dim red have nearly the same H. Brightness moves on the V
channel, saturation on S. So a single HSV threshold like
`H in [0, 10]` matches red caps across a wide range of lighting,
while the equivalent RGB threshold has to drift with the bulb.

The catch with red is that the H axis wraps around: pure red sits
at both H=0 and H=180. So "red" is really *two* ranges OR'd
together; "blue" and "green" each fit in one. See `CAP_HSV_RANGES`
in [`cap_segmenter.py`](cap_segmenter.py).

### Why morphological closing

A glossy cap reflects the overhead light as a small bright spot in
the middle. That bright spot has the wrong V — too high for the
threshold — so it leaves a *hole* in the binary mask. Closing
(`cv2.MORPH_CLOSE` = dilate then erode) fills holes smaller than
the kernel without growing the rest of the blob. Five-pixel kernel
catches typical specular highlights at our camera distance.

### Why connected components

The mask says "this pixel is red". We want "this **cap** is red".
`cv2.connectedComponentsWithStats` walks the mask once and gives
back, for every distinct blob: the bounding box, the centroid, and
the area in pixels. We drop blobs outside a sensible area range
(noise on the small side, the rack body on the large side) and
what's left is one detection per cap. No clustering, no shape
analysis required.

### Why slot-based output for the autosampler

The bare detections are `(color, centroid_xy)` in pixel
coordinates. A LIMS request is "give me all reds". The bridge is
to bucket each centroid by **which rack slot** it falls into.
Since the rack is a horizontal row in the overhead view, we split
the image width into `num_slots` equal bands and assign each
detection to the band that contains its centroid. The result is a
`{slot_id: color}` dictionary — the same shape the rest of the
pick-and-place pipeline already uses.

## Workflow

```
              exercise 1 SDF (or a real overhead camera)
                          │
                          │  render once / capture once
                          ▼
                BGR image (480x640 or similar)
                          │
                          │  cap_segmenter.find_all_caps()
                          ▼
                list[CapDetection]
                          │
                          │  cap_segmenter.caps_to_slots()
                          ▼
                {slot_id: color}    ───►   filter for "red"  ───►  LIMS subset
```

Inputs and outputs at a glance:

| Step | Reads | Writes |
|------|-------|--------|
| `find_caps(bgr, color)` | one BGR image, one colour name | `list[CapDetection]` with centroid + bbox + area |
| `find_all_caps(bgr)` | one BGR image | `list[CapDetection]` across every configured colour |
| `caps_to_slots(caps, num_slots, image_width)` | the detection list | `{slot_id: color}` |
| `annotate(bgr, caps)` | the image + the detection list | a new BGR image with each cap boxed + labelled |

## What "Done when" means here

The checklist asks for **the correct cap is returned under 3
distinct lighting setups**. [`demo.py`](demo.py) covers that bar
without needing Gazebo:

1. It renders three synthetic scenes (`bright`, `normal`, `dim`) of
   the rack's back row, each with five caps in known slots.
2. It runs `find_all_caps` on each scene, builds the
   `{slot: color}` dict, and compares it against the ground truth.
3. The script exits non-zero if any of the three scenes disagrees.

So a `PASS` line for every lighting label *is* the checklist's
"Done when" check.

## Example run

```bash
# 1. install deps (one time)
pip install -r requirements.txt

# 2. run the demo
python demo.py

# expected output (numbers will vary slightly because of the seeded noise):
# [demo] scene size       : 640x360
# [demo] slots (left->right): {1: 'red', 2: 'red', 3: 'blue', 4: 'green', 5: 'red'}
#
# [demo] lighting=bright  found  5 caps  slots={1: 'red', 2: 'red', 5: 'red', 3: 'blue', 4: 'green'}  [PASS]
# [demo] lighting=normal  found  5 caps  slots={1: 'red', 2: 'red', 5: 'red', 3: 'blue', 4: 'green'}  [PASS]
# [demo] lighting=dim     found  8 caps  slots={1: 'red', 3: 'blue', 4: 'green', 5: 'red', 2: 'red'}  [PASS]
#
# [demo] LIMS query example: 'give me all RED caps' -> [1, 2, 5]
# [demo] outputs in: ./output
#
# [demo] PASS — checklist 'done when' bar requires all 3 lighting setups to pass.
```

After the demo, look at `output/annotated_<lighting>.png` to see
the boxes drawn over the caps. The `dim` scene picks up a couple of
spurious blobs at the rack edge — that's classical CV being honest
about a hard scene; the slot mapping still resolves them to the
right answer.

## Using the segmenter on a Gazebo or real-camera frame

The whole library is **pure OpenCV**, so plugging a real frame in
is one extra line:

```python
import cv2
from cap_segmenter import find_all_caps, caps_to_slots

bgr = cv2.imread("/path/to/overhead_camera_frame.png")
caps = find_all_caps(bgr)
print(caps_to_slots(caps, num_slots=5, image_width=bgr.shape[1]))
```

For a live Gazebo camera feed, wrap `find_all_caps` in the same
ROS 2 node pattern exercise 4 uses for YOLO: subscribe to the
camera topic, convert with `cv_bridge`, call the segmenter,
publish the detections. The algorithm doesn't change — only the
input plumbing.

## What this exercise is **not**

| Need | Where it is solved |
|------|--------------------|
| Object detection (where, not what colour) | exercise 3 (YOLO) |
| Pixel-accurate masks | exercise 7 (instance segmentation) |
| 3D position of the cap | exercise 8 (depth) |
| Robust to bad lighting / partial colour | YOLO (exercise 3) or YOLO+seg (exercise 7) |
| Reading the printed barcode on the vial | exercise 14 (`pyzbar`) |

This exercise is the cheapest possible perception for one specific
job: *bucketing caps by colour*. It is intentionally narrow.

## What's next

- **Item 14** — barcode reading. Once the LIMS knows *which* red
  cap (by barcode), the colour filter is only the coarse first
  step.
- **Items 36-40** — replace the synthetic scene with a live Gazebo
  camera feed, and route the `{slot: color}` dict into the
  collision-objects no-fly zones from exercise 20.
