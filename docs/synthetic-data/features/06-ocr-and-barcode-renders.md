# Feature 6 — OCR and Barcode Renders

> **Poster wording.** "Camera frames with generated text, codes, and
> labels at random fonts, glare, and angles. The training data OCR
> and barcode pipelines need."

## What it is, in simple words

Many robots have to **read something** off a product — a serial
number, a lot code, a QR code on a vial, a barcode on a shipping box.
A model that does this is called an **OCR model** (for text) or a
**barcode decoder** (for barcodes / QR codes).

To train one you need thousands of pictures of the text or codes
**under realistic conditions** — different fonts, different angles,
glare on the surface, partial occlusion, varying lighting. Real-world
collection of this data is painful: you need to physically print
thousands of variants and photograph each one.

In sim we **render** the text or code directly onto the object's
surface as a texture, then re-render the scene. Free, automatic,
perfectly labelled.

```
ocr_<project>/
├── images/         frame_00001.png
├── labels/         frame_00001.json   ({text: "ABC-12345", bbox: […], lang: "en"})
└── codes/          frame_00001.json   ({code: "9780201379624", type: "EAN13", bbox: […]})
```

## Who will use it

The customer's **perception engineer** working on identification /
traceability. Common in pharma, logistics, food packaging.

Job titles: *Perception Engineer*, *Computer Vision Engineer*,
*Robotics Engineer (Traceability)*.

## What models the customer trains / uses with it

- **PaddleOCR** — the most-used open OCR engine in 2025–2026, by far.
- **EasyOCR** — simpler Python OCR.
- **TrOCR** (Microsoft) — transformer-based, very strong on printed
  text.
- **DocTR (Mindee)** — modern OCR pipeline.
- **pyzbar / ZXing** — barcode and QR decoders (these are
  *non-ML*; we still help the customer prove their pipeline works on
  the worst-case images we render).
- **Custom small CNN** — when the customer's text follows a fixed
  format (e.g. exactly 7 digits) and a small model is faster than
  PaddleOCR.

## Libraries and frameworks involved

**On our side:**

- **Pillow (PIL)** — generates the text image at random fonts /
  sizes / colours.
- **python-barcode, qrcode** — generates EAN, UPC, Code128, QR, Data
  Matrix textures.
- **Blender / Gazebo / Isaac Sim** — applies the texture to the
  product's surface and re-renders the scene with random glare,
  curl, perspective.
- **Isaac Sim Replicator** — has a built-in randomised text
  generator if the customer prefers a single platform.

**On the customer's side:**

- **PaddleOCR** for OCR fine-tuning.
- **pyzbar / ZXing** for barcode evaluation.
- **OpenCV** for any pre-processing the customer does first.

## What we ship (the formats)

| Output | Default format |
|--------|----------------|
| Images | PNG |
| Per-frame text labels | One JSON per frame: `{text, bbox, font, size, language, lighting_condition}` |
| Per-frame barcode labels | One JSON per frame: `{decoded_value, code_type, bbox, decoded_ok}` |
| Bundled | COCO JSON if the customer wants one big file |

For text we follow the **PPOCRLabel** format when the customer trains
PaddleOCR.

## How we generate it (the methods)

- **Domain randomisation.** Every frame randomises font (we ship a
  small library of common product fonts), size, colour, kerning,
  background colour, surface curl, camera angle, lighting, and
  glare.
- **Photo-real rendering.** OCR fails on glare and shadow. Isaac
  Sim's path tracer is the main reason we pick it for OCR-heavy
  projects.
- **Procedural scenes.** Different products on different parts of
  the table, different orientations, varying clutter.
- **Sensor noise modelling.** Optional. JPEG compression artefacts,
  motion blur, and camera noise are layered on top so the model
  trains on what production cameras actually produce.

We deliberately render the **worst cases** — half-blocked text,
extreme tilt, sun glare on the label — because that is where real
OCR models fail and the customer needs the most help.

## Pain points this solves

- **"Our OCR works on pristine labels but fails on the line."** Glare
  and motion blur are the killers. Both are easy to add in sim.
- **"We can't print 50 000 product variants just to train."** Print
  costs vanish in sim; texture changes are instant.
- **"Our barcode decoder fails on damaged boxes."** We render the
  barcode on a wrinkled / torn surface and prove the new decoder
  passes.

## What to say in a sales conversation

- "What exact codes / text does the robot read?" *Pure numeric? QR
  code? EAN-13? Free-form text? Each has its own pipeline.*
- "What does the surface look like?" *Glossy plastic? Matte
  cardboard? Curved bottle? Drives the rendering and the glare
  patterns.*
- "What model do you run today, and what is its failure rate?"
  *Sets the bar — we have to beat their current numbers on a held-
  out test set.*
- "Do you also need the bounding box of the text region, or just
  the decoded string?" *Detection + recognition needs the box;
  pure-recognition tasks just need the string.*

## Typical scope and delivery

- **Inputs we need:** the alphabet / code format, examples of real
  labels (a dozen photos is enough), the surface CAD or texture
  reference, the camera and lighting setup.
- **What we ship:** 10 000–100 000 labelled images, the
  text-generation config so the customer can regenerate more
  themselves, and (if they use PaddleOCR) a ready-to-run
  fine-tuning recipe.
- **Typical timeline:** 2–3 weeks.
