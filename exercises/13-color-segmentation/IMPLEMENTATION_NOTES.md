# Implementation notes — 13 Colour segmentation (no ML)

Engineering decisions that are not obvious from the code.

## Why HSV and not RGB

In **RGB**, a "red cap" is something like `(R≈200, G≈30, B≈30)` —
but only at one specific brightness. Move to a dimmer bulb and the
whole triple drops to `(R≈100, G≈20, B≈20)`; move to a bright window
and it climbs to `(R≈250, G≈80, B≈80)`. Any threshold has to drift
with the lighting, which means it's not really one threshold.

In **HSV**, the **hue** channel encodes *what colour* almost
independently of brightness. Red caps sit at H ≈ 0 (or 180 — see
below) under any normal light. Brightness moves on **value**;
washed-out vs vivid moves on **saturation**. So one HSV threshold
`(H in [0,10], S >= 70, V >= 50)` matches red across the
"lighting variation" the autosampler bench actually sees.

That's why every classical CV recipe in the literature converts to
HSV first — there is no good RGB equivalent.

## Why red needs two ranges

OpenCV's H axis is 0..179 (not 0..359 — H is divided by 2 so it
fits in a uint8). Red sits at *both ends*: pure red is H≈0 and also
H≈180. A single threshold `[0, 10]` misses anything that wraps
around to ~178; a single threshold `[170, 179]` misses anything at
H=2. So we OR two ranges together:

```python
"red": [
    ((0,   70, 50), (10,  255, 255)),
    ((170, 70, 50), (179, 255, 255)),
],
```

Blue and green don't wrap, so each fits in one range. This trick is
specific to red (and to a lesser extent orange/magenta if you ever
add them).

## Why morphological closing instead of opening

Two failure modes for the binary mask:

- A glossy cap has a **bright glare spot** in the middle. That
  pixel has too-high V for the threshold, so it shows up as a hole
  *inside* the cap's blob.
- A speckle of noise on the bench passes the threshold and shows
  up as a tiny stray blob *outside* any cap.

`MORPH_OPEN` (erode then dilate) removes the speckles — useful in
some cases, but we don't need it because the area filter
(`MIN_AREA_PX`) already drops them.

`MORPH_CLOSE` (dilate then erode) fills holes smaller than the
kernel without growing the rest of the blob. That fixes the glare
issue without changing anything else. Net win: we use CLOSE only.

A 5×5 kernel handles ~5-pixel glare spots; bumps that up to 7×7 if
your real-world caps have bigger highlights.

## Why `connectedComponentsWithStats` and not `findContours`

Two reasonable choices for "label every blob":

| | `findContours` | `connectedComponentsWithStats` |
|---|---|---|
| Output | nested list of contour points | array of label ids + a stats table |
| Area / bbox / centroid | computed per contour via extra calls | already in `stats` / `centroids` |
| Speed | slightly slower for our case | faster, one call |
| Holes | needs `RETR_EXTERNAL` to skip them | automatic |

Both work. We use `connectedComponentsWithStats` because it returns
the bbox + centroid + area we need *as a single numpy array* — no
extra `cv2.moments(...)` calls per blob.

## Why these area bounds

A 9 mm screw cap at the overhead camera distance projects to a disc
of roughly **20-50 px diameter** → **300-2500 px area**. So:

- `MIN_AREA_PX = 300` cleanly drops per-pixel sensor noise blobs
  (the dim scene's noise blobs all live in 80-250 px, which I
  measured before raising the threshold).
- `MAX_AREA_PX = 8000` drops the rack body and any wall that leaks
  through the threshold (e.g. tan rack hitting a wide hue band).

These numbers are tied to the camera distance from exercise 1. If
you change the camera height (different focal length, different
mount), re-measure the cap area first.

## Why slot indexing by x-band

The autosampler tie-in is `caps_to_slots(caps, num_slots,
image_width)` — divide the image width into `num_slots` equal
bands, assign each detection to the band that contains its
centroid x.

This is the simplest possible mapping. It assumes:

1. The rack is roughly **horizontal** in the image (the overhead
   camera from exercise 1 satisfies this).
2. There are no other colour-matching objects outside the rack
   strip (the bench is dark grey, the housing is matte — no false
   matches).
3. Slot 1 is leftmost, slot N is rightmost (the LIMS convention).

For the real cell you would replace this with a **rack ROI** — an
explicit rectangle measured from the calibration step — and bucket
the centroids inside that rectangle only. Same idea, smaller
domain. Doing it that way is exercise-12 territory (hand-eye
calibration), so we don't pull it in here.

## Why we render synthetic scenes instead of needing Gazebo

The "Done when 3 lighting setups" check has to be repeatable in
under five seconds, with `python demo.py` and nothing else
running. Spinning up Gazebo + headless rendering + saving frames
would be 10× the code and 30× the runtime for the same test.

The synthetic scenes (`render_scene` in `demo.py`) match the
*important* properties of the Gazebo overhead view: dark grey
bench, tan rack strip, ~40-px coloured circles for caps, a
brightness shift to simulate the bulb, and small additive noise so
nothing looks like a stencil. They are deliberately *not* a
beautiful render — the segmenter shouldn't need one.

For users who DO want a real Gazebo frame: save a PNG of the
camera topic to disk, then `cv2.imread` it in your own script and
call `find_all_caps`. The library doesn't care.

## Picking HSV ranges in the real world

When you bring real images in, the current ranges almost certainly
won't fit. The recipe:

1. Save a representative frame as `sample.png`.
2. Open it in any HSV picker (GIMP "Pointer" dialog, or a 10-line
   OpenCV `cv2.setMouseCallback` script).
3. Click on a clean part of each cap colour and write down the
   `(H, S, V)` triple. Do this for 5-10 caps per colour, across
   the lighting you expect.
4. Set the range to roughly `(H_min - 10, S_min - 20, V_min - 30)`
   to `(H_max + 10, 255, 255)`. The lower bound on S/V matters
   most — too high and you lose dim caps; too low and the rack
   itself gets matched.
5. Re-run `demo.py` swapped to read `sample.png` instead of the
   synthetic scene.

A wrong range is the #1 cause of all real-world failures here.
Always inspect the binary mask before blaming the rest of the
pipeline.

## Failure modes you will see in practice

- **`scene_dim.png` returns 8 caps instead of 5.** Three of those
  are noise blobs at the rack edge that scrape past `MIN_AREA_PX`
  because their pixels happen to align. `caps_to_slots` still maps
  them to the correct slots (the real cap dominates the band), so
  the demo `PASS`es. In real images you'd bump `MIN_AREA_PX` to
  500 and they go away.
- **A blue cap is found as "green" (or vice versa).** The H ranges
  overlap. Tighten `green` to `(50, …, 80, …)` and `blue` to
  `(100, …, 130, …)` — the safe gap is around H=90.
- **The whole rack lights up as red.** Your bulb is too warm. The
  tan rack now has a hue near 15-20 and passes the red range.
  Raise the S floor on red from 70 to 110 — the rack has lower
  saturation than the cap.
- **A cap is missed entirely.** Open the binary mask
  (`cv2.imwrite("mask.png", mask)` inside `find_caps`) — almost
  always you'll see a hole through the middle of the cap where the
  glare is. Raise the CLOSE kernel size from 5 to 7.
- **The centroid lands on the cap's edge, not centre.** The mask
  has a horseshoe shape from one-sided glare. CLOSE with a bigger
  kernel, or accept it — the slot mapping uses centroid x only, so
  a 2-3 px y error doesn't matter.

## Assumptions baked into the code

1. **Image is BGR uint8** — OpenCV's default. RGB-ordered images
   (e.g. straight from PIL) will see red caps as blue. Convert
   first.
2. **Caps are bright and saturated.** Lab caps satisfy this; faded
   or matte caps wouldn't.
3. **The rack is roughly horizontal in the frame.** If you mount
   the camera at a 30° tilt, the slot bucketing by x-band breaks —
   replace `caps_to_slots` with a calibrated ROI.
4. **One image per call.** The library is stateless; no temporal
   smoothing across frames. For a live video feed where caps
   sometimes flicker in and out of the mask, average the last N
   frames at the caller side.

## Why this is in the toolbox, not the main path

Classical CV is the right answer when colour is reliable. Most
real autosampler cells have **mixed** workflows — some racks have
plain caps, some have colour-coded caps, some have neither.
Production code typically:

- Runs YOLO (exercise 3) as the primary "where is the vial"
  detector — works regardless of cap colour.
- Runs HSV colour segmentation (this exercise) **only on the
  bounding boxes YOLO already found**, as a tiny second pass that
  attaches a colour label to each detection.

This exercise is the standalone version so you understand the
classical recipe end-to-end. The two-pass version is exercise 21
territory and beyond.

## Things to revisit later

- Add an HSV picker helper script (`hsv_picker.py`) so a new user
  can re-tune the ranges on a real frame without writing custom
  callback code.
- Move the synthetic scene generator into a separate
  `synthetic_scene.py` once it has more than one consumer. Right
  now it lives inside `demo.py` because that's the only caller.
- Wrap `find_all_caps` in the exercise-4 ROS 2 node pattern —
  subscribe to `/overhead_camera/image_raw`, publish
  `vision_msgs/Detection2DArray`. Algorithm doesn't change, only
  the plumbing.
- Replace `caps_to_slots`'s equal-band bucketing with a calibrated
  rack-ROI rectangle once exercise 12 (hand-eye) is in play.
