# 27 — Implementation notes

## Why a top-down 2D render and not Isaac Sim / Gazebo

The synthetic-data offering in `docs/synthetic-data/` recommends Isaac
Sim Replicator as the production tool. We did not use it here for
three reasons:

1. **Exercise scope.** The CLAUDE.md rule is "keep the code as small
   as possible — just enough to satisfy the Done when check." Isaac
   Sim is a multi-gigabyte download with a GPU dependency. Pillow +
   numpy is two `pip install` lines and runs anywhere.
2. **Concept-first.** The point is to teach **domain randomisation +
   procedural scenes + ground-truth labels in standard formats**.
   That concept does not need ray tracing or rigid-body physics. A
   contributor reading this exercise should understand the
   synthetic-data product *before* they meet Replicator.
3. **The real autosampler camera is overhead.** A top-down 2D render
   is not a cartoon shortcut here — it is what the production camera
   actually sees. The pixels look reasonably close to a real
   overhead photo of a vial rack.

The path to production is to swap `render.py` for an Isaac Sim
Replicator script. `scene.py`, `writers.py`, and the verify gate stay
the same. That is deliberate — see "Separation of concerns" in
`ARCHITECTURE.md`.

## Why numpy + Pillow instead of OpenCV

Both work, but Pillow's `ImageDraw` is the simplest API for drawing
shapes onto a blank canvas. OpenCV is shape-first too but pulls in
~40 MB and a BGR/RGB gotcha. Numpy alone is used for masks (`np.ogrid`
gives a one-line filled-disk mask), the noise sample
(`rng.normal`), and brightness scaling.

If a future contributor wants OpenCV-style augmentations
(Albumentations, perspective warp, JPEG simulation), point them at
`render.py` — that's the only file that touches pixels.

## Why ground-truth bboxes from the geometry, not from the mask

We could have rendered the image first and then *measured* each
object's bbox from the mask afterwards. Instead we know the bbox at
draw time (we picked the disk centre and radius). This avoids a
class of synthetic-data bugs where:

- A vial gets accidentally clipped by the image edge and its mask
  becomes a half-moon, but its bbox in the label is the full disk.
- Overlapping vials produce a single connected component but two
  separate annotations.
- Anti-aliasing changes the edge of the mask by a pixel, so the
  IoU vs. "intended" geometry drops below 1.0.

Computing the bbox from the mask we just drew (`_bbox_from_mask`)
sidesteps both issues, and `verify.py` confirms it: the dataset's
worst bbox-vs-mask IoU is `1.000` on every run we have tried.

## Why the YOLO and COCO segmentation polygons agree

`writers._polygon_from_disk_mask` uses the **bbox** of the mask, not
a contour-finding routine. Since every object in this exercise is a
true geometric disk, the bbox plus a regular 16-vertex polygon
matches the mask within sub-pixel error — there is nothing to be
gained from `cv2.findContours` here, and it would have added an
OpenCV dependency.

If a future contributor renders an object whose silhouette is *not* a
disk (a rectangular tube, an irregular cap), they must replace
`_polygon_from_disk_mask` with a proper contour finder. The function
is named to make that obvious.

## Which of the four methods this exercise implements

| Method | Used here? | How |
|---|---|---|
| Domain randomisation | yes | per-scene brightness, background tint, rack colour, optional blur, cap colours |
| Procedural scenes | yes | random rack offset (±3 mm), random fill probability per slot, 0–3 distractors |
| Photo-real rendering | no | needs Isaac Sim / Blender / Unreal; out of scope |
| Sensor noise modelling | yes (light) | Gaussian RGB noise per pixel, sigma 2–6 |

`metadata.json` records exactly which methods ran so the customer's
ML engineer can reproduce the distribution.

## Class choices

Two classes: `vial` (any cap colour) and `empty_slot`.

Two is the minimum that lets a downstream model answer the
autosampler's central question — "which slots in the inbound rack
still have vials, and which slots in the destination tray are free?"
— from one camera frame.

Cap colour is encoded as an **attribute** in COCO, not as a separate
class. That keeps the YOLO label simple (one class per box) while
still letting a smarter downstream filter ask for "all red caps" in
COCO. Splitting `vial` into `cap_red`, `cap_blue`, ... is a one-line
change in `render.py` if a customer asks for it.

## Failure cases we deliberately don't cover

The exercise prioritises *correctness of labels* over *visual
realism*. Things we intentionally skip:

| Skipped | Why |
|---|---|
| Specular highlights on the cap | needs photo-real rendering |
| Occlusion by gloves / pipettes | adds geometric complexity without changing the format story |
| Camera intrinsic distortion | belongs in exercise 11, not here |
| Per-vial tilt | would break the "bbox = disk bbox" guarantee |
| Realistic shadows | needs a ray tracer |
| Cap rotation / label print | belongs in exercise 14 |

If a customer cares about any of these, the answer is "we move to
Isaac Sim Replicator" — exactly the upgrade path the synthetic-data
offering describes.

## Assumptions and failure modes

| Assumption | What breaks if it's wrong |
|---|---|
| `_polygon_from_disk_mask` is only called on disk-shaped masks | non-circular silhouettes get bad COCO segmentations |
| The mask filename order matches the annotation order | `verify.py` would pair the wrong (box, mask) together |
| Distractors never overlap a rack slot | otherwise their bbox might overlap a vial bbox and confuse training |
| Image resolution and PX_PER_MM are constants | downstream consumers of the dataset would have to be re-told the scale |
| RNG seed is fixed in `generate.py` | otherwise two runs produce different "frame 5" |

## Performance

- ~3.5 frames / second on a laptop CPU (single-threaded).
- 100-frame default run: ~35 s.
- The dataset is dominated by the per-instance PNG masks — most
  frames have ~54 objects, so ~54 small PNGs per frame. If you need
  to skip those (e.g. you only train YOLO, not Mask R-CNN), comment
  out the `write_instance_masks` call in `generate.py`.

## Debugging tips

- **`PASS` but the overlay looks wrong** → check that
  `verify._read_yolo_labels` and `writers.write_yolo_labels` agree
  on the `xywh` normalisation. Off-by-half-pixel is a classic.
- **`FAIL` with IoU just under 0.95** → likely a rounding error
  between the bbox computed at draw time and the bbox computed from
  the saved PNG. `_disk_mask` is rasterised at integer pixel
  centres, so the bbox is integer-valued by construction; if you
  change to anti-aliased drawing you must round consistently.
- **COCO `iscrowd` warnings from MMDetection** → we always set it
  to 0 because vials are individuals, not crowds. Don't change this
  unless you actually have a crowd category.
- **Ultralytics complains about `dataset.yaml` paths** → the
  `path:` field is absolute (`dataset_root.resolve()`). Move the
  dataset folder and Ultralytics will fail until you re-write the
  yaml.

## How this would change for a real customer

1. Swap `render.py` for an Isaac Sim Replicator script. Output
   format stays the same.
2. Add the customer's CAD files in `scene.py` (`USDFile` references
   on the rack and on each vial type).
3. Add their real-world camera intrinsics (`cv2.calibrateCamera`
   output) and apply them to the render frustum.
4. Add their cell's specific distractor library (tools, label
   printers, gloved hands) — same `Distractor` dataclass, just
   richer geometry.
5. Add a Albumentations-style training-time augmentation pipeline
   on the customer's side. This exercise produces *clean* edges on
   purpose — augmentation is the consumer's job, not ours.

Items 2–4 are why the synthetic-data offering quotes "2–3 weeks for
the first 10 000-frame batch" in
[`features/01-detection-images-and-masks.md`](../../docs/synthetic-data/features/01-detection-images-and-masks.md):
most of the work is per-customer customisation, not the rendering
pipeline itself.
