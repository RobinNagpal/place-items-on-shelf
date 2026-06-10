# Type 6 — Synthetic text and barcode renders

## What it is

Pictures of **labels, screens, and stickers** that the simulator
*paints* with text or codes you already know. Three sub-flavours
that all share the same recipe:

- **Printed-label text** — the sticker on a vial saying
  `KETCHUP_A_R1 / 2026-06-10`. Ground truth = the string we
  typed into the texture generator.
- **1D / 2D barcodes** — Code-128, QR. Ground truth = the
  payload string.
- **LCD / 7-segment readings** — the centrifuge timer panel,
  the balance display. Ground truth = the number we asked the
  texture to draw.

Because *we* drew the text, **we already know the answer**.
That makes the dataset a perfect testbed: feed the image to an
OCR / decoder pipeline and check whether it gives back the same
string.

## When it is useful

Whenever the robot has to **read** something a human would
normally read:

- Step 7 (label OCR) — read the sample ID off the vial label.
- Step 8 (barcode scan) — read the vial's barcode at the scan
  station before placement.
- Step 4 (centrifuge timer) — wait for the displayed remaining
  time to hit `00:00` before opening the lid.
- Step 1 (balance LCD), if Weighing were re-enabled — read the
  mass off a 7-segment display.

## Who uses it

**Off-the-shelf pre-trained models** — no custom training in
most cases. The synthetic dataset is a **smoke test**, not a
training set.

| Sub-flavour | What reads it |
|---|---|
| Printed-label text | `paddleocr`, `easyocr`, `tesseract` — pre-trained OCR. |
| 1D / 2D barcode | `pyzbar`, `zxing-cpp` — pre-trained decoders. |
| LCD / 7-segment | `paddleocr` works decently, but a hand-rolled 5-line decoder ("which segments are lit?") is often more robust and is the lab-bench norm. |

If your synthetic test set shows the pre-trained model getting
< 99 % correct, the realistic fix is to **render the textures
more realistically** (different fonts, blur, glare) — not to
retrain the model.

## How to produce it in Gazebo

This one is mostly **outside** Gazebo: you generate the textures
in Python, then apply them as materials in the SDF.

### 1. Generate the texture in Python

```python
from PIL import Image, ImageDraw, ImageFont

def render_label(sample_id, date, out_path):
    img  = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 28)
    draw.text((10, 10),  sample_id, fill="black", font=font)
    draw.text((10, 60),  date,      fill="black", font=font)
    img.save(out_path)
    return {"path": out_path, "text": f"{sample_id}\n{date}"}
```

For barcodes use the `qrcode` and `python-barcode` libraries:

```python
import qrcode
img = qrcode.make("KB2-20260610").get_image()
img.save("qr_KB2.png")
```

For 7-segment LCDs paint the segments by hand — a 5-line
function that toggles seven black rectangles per digit is
enough.

### 2. Bake the texture into the SDF

Each rendered `.png` lives inside the SDF model as a
`<material><pbr>` texture map. The vial's body is a cylinder; the
label is a thin coloured plane attached to it.

```xml
<model name="vial_with_label_A_r1">
  ... cylinder + cap ...
  <link name="label_link">
    <pose>0 0.006 0.015 0 0 0</pose>
    <visual name="label">
      <geometry>
        <plane>
          <size>0.024 0.015</size>
        </plane>
      </geometry>
      <material>
        <pbr>
          <metal>
            <albedo_map>textures/label_A_r1.png</albedo_map>
          </metal>
        </pbr>
      </material>
    </visual>
  </link>
</model>
```

### 3. Vary the textures across the dataset

For 1 000 randomised stickers, write a short Python loop that
generates 1 000 PNGs (random `sample_id`, random date, random
font and size) and dumps them into `textures/`. Spawn one vial
model per texture; record both the **image** that the Gazebo
camera sees and the **source string** the texture generator
used.

```
synthetic_<step>/
├── images/
│   └── label_close_<N>.jpg          # camera view of the labelled vial
└── labels/
    └── label_<N>.json               # {"source_text": "KETCHUP_A_R1\n2026-06-10",
                                      #  "font": "DejaVuSansMono-Bold",
                                      #  "font_pt": 28,
                                      #  "barcode_payload": "KAR1-20260610"}
```

### 4. Add variety on the camera side too

A texture is just a flat picture. The interesting failures
happen because the *camera* sees it at a tilt, in poor light,
or partially occluded. So also vary:

- Camera pose (slight tilt) so the sticker isn't always
  fronto-parallel.
- Lighting (cool-white vs warm-yellow lab light) to stress the
  OCR's contrast handling.
- Add specular glare on the sticker by inserting a small point
  light at a random angle.

## Pass / fail bar

Feed your generated images through `pyzbar` / `paddleocr`. The
test passes if the decoded string equals the source string in
**≥ 99 %** of frames. If it doesn't, the next step is rendering
more realistically — not training a custom model.

## Existing project reference

[`exercises/14-barcode-reader/`](../../../../exercises/14-barcode-reader/)
already runs `pyzbar` against the v1 autosampler world. The
ketchup-case dataset uses the same decoder against the new
labels; only the textures change.
