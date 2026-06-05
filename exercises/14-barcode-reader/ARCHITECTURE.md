# Architecture — 14 Barcode / QR-code reader

## Folder tree

```
14-barcode-reader/
├── README.md              # concept + scan station + spin-and-decode workflow
├── ARCHITECTURE.md        # this file
├── IMPLEMENTATION_NOTES.md# decoder choice, scan-station pose math, failure modes
├── requirements.txt       # opencv + qrcode (+ optional pyzbar)
├── barcode_reader.py      # decode_barcode(bgr) + spin_and_decode(provider, max_steps)
├── demo.py                # generate 5 QRs, simulate 5 spin sessions, write LIMS CSV
├── .gitignore             # ignore output/ and __pycache__/
└── output/                # demo writes vial_*_visible.png + lims.csv
    (created at runtime; not in git)
```

The whole exercise is **two Python files** — one library and one
runnable demo. No ROS, no Gazebo, no model weights.

## Per-file responsibility

| File | Owns |
|---|---|
| [`barcode_reader.py`](barcode_reader.py) | The two-decoder strategy (pyzbar primary, `cv2.QRCodeDetector` fallback), the public `decode_barcode(bgr)` function, and the `spin_and_decode(provider, max_steps)` search loop. Nothing else in the project decides which decoder to use — that lives here once. Exposes `DECODER_NAME` for diagnostics. |
| [`demo.py`](demo.py) | Renders five synthetic "scan-station" sessions (one per vial barcode `B-2024-0117 … B-2024-0121`), drives `spin_and_decode` against a callback that fakes a wrist-nudge + camera capture, and writes a `(tray_slot, barcode)` CSV. This is the "Done when 5 codes → 5 mappings" check. |
| [`requirements.txt`](requirements.txt) | Pins `opencv-python`, `numpy`, `qrcode`, `pyzbar`. Notes the `libzbar0` apt dep for pyzbar. |
| `.gitignore` | Keeps `output/` and `__pycache__/` out of git. |

## How the files interact at runtime

```
                barcode_reader.py
                ──────────────────
                _try_load_pyzbar()  -> Callable | None
                _cv2_decoder()      -> Callable
                _DECODE             = pyzbar  if available  else  cv2
                DECODER_NAME        = "pyzbar" or "cv2.QRCodeDetector (fallback)"
                def decode_barcode(bgr_image)
                def spin_and_decode(frame_provider, max_steps)
                        ▲             ▲
                        │             │ imports
                        │             │
                        │       demo.py
                        │       ──────
                        │       VIAL_BARCODES = [5 codes]
                        │       make_qr_image(text) -> BGR numpy
                        │       vial_frame_at(qr, step, vis_step)
                        │       main():
                        │         for slot, code in enumerate(VIAL_BARCODES):
                        │            qr = make_qr_image(code)
                        │            provider = lambda step: vial_frame_at(qr, step, ...)
                        ├──────── decoded, step = spin_and_decode(provider, 12)
                        │            assert decoded == code
                        │            lims_log[slot] = decoded
                        │         write output/lims.csv + per-vial PNGs
                        │
                  (no other consumers — by design)
                        ▼
                  output/vial_*_visible.png
                  output/lims.csv
                  exit 0 / 1
```

The handoff is **the two public functions** of `barcode_reader`.
When exercise 21 (pick-and-place) wires this into a real ROS node,
it will import the same two functions, wrap `frame_provider` around
a `wrist nudge + cv_bridge image read`, and write to a LIMS REST
endpoint instead of a CSV.

## Data flow inside one scan

```
arm holding vial at above_scan_station
            │
            ▼
spin_and_decode(provider, max_steps=12):
   for step in 0..11:                          <- one loop iter = one wrist nudge
       frame = provider(step)
            │   provider:
            │     1. move J6 by 30 deg
            │     2. wait for next /scan_camera/image_raw frame
            │     3. cv_bridge -> BGR numpy
            ▼
       code = decode_barcode(frame)
            │   decode_barcode:
            │     pyzbar.decode(gray)        -> [Decoded(...)]   -> str
            │     OR
            │     cv2.QRCodeDetector.detectAndDecode(bgr) -> str
            │   (returns None on miss)
            ▼
       if code is not None:
           return (code, step)
   return (None, max_steps)              <- timeout
```

## ROS interfaces the integration node will touch (not done here)

This exercise is decoder-only. The integration with ROS lives in
exercise 21. For reference, the scan-station camera should publish
on its own topic so the overhead camera can keep running:

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/scan_camera/image_raw` | topic (`sensor_msgs/Image`) | scan camera → integration node | one BGR frame, 320×320 or similar |
| `/lims_log/barcode` | topic or service | integration node → LIMS bridge | `(tray_slot, barcode)` pair |
| MoveIt action | `/move_action` | integration node → move_group | wrist nudge between frames |

## Dependencies (external to this folder)

- **`opencv-python`** — image arrays, `cv2.QRCodeDetector` (the
  fallback decoder), and image I/O for `demo.py`.
- **`numpy`** — array container.
- **`qrcode`** + transitive **`Pillow`** — generate synthetic QR
  images in `demo.py`. Not used by `barcode_reader.py` itself.
- **`pyzbar`** *(optional)* — pure-python wrapper around
  `libzbar0`. If both are installed the decoder reads QR + 1D
  barcodes. If either is missing, `barcode_reader.py` falls back
  to `cv2.QRCodeDetector` (QR only) at import time.

## What this exercise does NOT touch

| Subsystem | Where it lives |
|-----------|-----------------|
| Picking the vial up | exercise 21 |
| Knowing **which** vials to load | exercise 21 / LIMS upstream |
| The wrist nudge motion | exercise 19 (Cartesian pose goal) |
| Attached collision while holding the vial | exercise 20 (`AttachedCollisionObject`) |
| Cap-colour subset filtering | exercise 13 |

Single responsibility: **decode a label off a held vial**. That's it.
