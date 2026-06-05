# Implementation notes — 14 Barcode / QR-code reader

Engineering decisions that are not obvious from the code.

## Why a second, fixed scan camera (and not the overhead one)

The overhead camera (exercise 4) sees vial caps from straight up.
Vial labels are wrapped around the side of the cylinder — from
above they're foreshortened, partly self-occluded by the cap, and
at the wrong distance for the camera's focus. Trying to make one
camera do both "find vials" and "read labels" is a losing trade:
either the lens is tuned for the wide overhead view and labels are
unreadable, or it's tuned for the close label view and the rack
disappears off the edges.

A small **side-facing** scan-station camera, mounted on a fixed
arm or housing wall at a known distance, lets the optics be
optimised for the label only. It's also cheap: ~£15 for a USB
machine-vision camera and a 3D-printed mount.

The trade-off is one extra waypoint in the arm's path. That's
~1 second per loaded vial. The autosampler cycle time spec
(10-20 s per vial) absorbs that without strain.

## Why spin-in-place and not "rotate the vial to face the camera"

In the abstract you could try to estimate the label's orientation
from the camera image and rotate the wrist by the exact angle to
face it. Two problems:

1. The label might not be in view *at all* to estimate from.
2. If the camera already sees the label well enough to find an
   angle, it has already decoded it — the orientation-search
   problem disappears.

So the strategy is to **assume nothing about where the label is**
and just spin in fixed steps until any frame decodes. 12 steps =
30° each = 1 full rotation. The decoder runs once per step (~5-20
ms with cv2, ~1-5 ms with pyzbar). The expected number of spins
before success is 6 (uniform distribution); worst case 12.

This is the brute-force search and it is the right answer when
the test is cheap and the search space is small.

## Why pyzbar primary, cv2.QRCodeDetector fallback

| | pyzbar (libzbar) | cv2.QRCodeDetector |
|---|---|---|
| QR codes | yes | yes |
| 1D barcodes (Code 128, UPC, ...) | yes | **no** |
| Data Matrix (the lab favourite) | yes | no |
| Robustness on partial / blurred / glare | better | OK |
| Install cost | needs `apt install libzbar0` on Linux | shipped with `opencv-python` |
| API | `pyzbar.decode(gray)` → list of `Decoded` | `detector.detectAndDecode(bgr)` → `(text, bbox, _)` |

Lab vials in practice carry **Data Matrix** codes (smaller than QR,
fit on a screw cap). pyzbar reads them; cv2 doesn't. The checklist
also explicitly names pyzbar. So pyzbar is the default *when the
system library is present*.

But pyzbar without `libzbar0` raises an `OSError` at *import time*,
which would break the whole module. So `barcode_reader.py` does a
**guarded import**: try pyzbar, catch both `ImportError` (no python
package) and `OSError` (no system library), and fall back to
`cv2.QRCodeDetector` if either fails. The arm code never sees the
difference.

The `DECODER_NAME` constant is exported for the demo to print which
decoder ran — useful when debugging "why does this code fail in
production but pass in the demo".

## Why the demo uses synthetic frames instead of Gazebo

Same reason as exercise 13. The "Done when 5 codes" check has to
be repeatable in under five seconds with one command. Spinning up
Gazebo, attaching a scan camera, rendering, capturing, decoding,
and tearing down would be 10× the code and 30× the runtime for
the same test.

`demo.py` generates each QR at runtime with `qrcode`, pastes it on
a fake "vial body" image (a near-white vertical rectangle on a
dark background), and provides 12 such frames per vial — visible
at exactly one spin angle (plus its two neighbours, to fake the
"partially visible at +/- 30°" case). The decoder fails on the
hidden frames and succeeds on the visible ones; the spin loop
finds the first success and stops.

For users who want to test against real Gazebo: render the scan
camera frame to PNG, then call `decode_barcode(cv2.imread("..."))`.
The library is identical.

## Why the vial body is wider than the QR in the demo

QR codes need a **quiet zone** (a blank white margin) on all
sides for the detector to find the finder patterns at the
corners. If the QR sticks out past the (near-white) vial body
into the dark background, the right-edge finder patterns lose
their quiet zone and `cv2.QRCodeDetector` silently fails to lock
on. We saw this fail on 1/5 codes during initial bring-up.

Fix: sized the synthetic vial body (160 px wide) to fully contain
the QR (120 px wide) plus margin. pyzbar (when available) is more
forgiving and wouldn't have hit this — but the demo defaults to
the strictest decoder, so the rendering has to satisfy both.

In real life, the *physical* vial is much wider than a Data
Matrix sticker — this is only a demo-rendering issue.

## Failure modes you will see in practice

- **All 12 spins time out.** The label is occluded (gripper finger
  covering it, the camera angle clipped) or the QR is too small
  for the camera resolution. Two responses in the arm controller:
  retry once with the gripper offset by 10 mm (frees a covered
  label), or mark the vial "unidentified" and flag for a human.
- **One spin reads garbage text.** A scratch on a different vial
  visible in the background got OCR'd as a barcode. Mitigation:
  validate against the expected barcode format (`re.match`); reject
  anything that doesn't match `B-\d{4}-\d{4}`. Easy to add to
  `decode_barcode` if you find this happening.
- **Decoder picks up the wrong code.** Two vials adjacent in the
  scan-station view (e.g. a queue) and pyzbar returns the closer
  one's text. Tighten the scan-station baffles so only one vial
  is ever in frame.
- **Glare / shadow hides the label.** Add a small ring light at
  the scan station. ~£20 fix; turns a 1% failure rate into
  ~0%.
- **`OSError: Unable to find zbar shared library`** at import — the
  fallback should kick in automatically. If you see it, the
  guarded import in `barcode_reader.py` needs to be widened to
  catch your platform's error (e.g. macOS sometimes raises
  `RuntimeError`).

## Assumptions baked into the code

1. **One vial in frame.** The library returns `found[0]` — the
   first code pyzbar reports. In normal scan-station geometry only
   one vial is ever visible. If you stack two, the result is
   nondeterministic.
2. **QR / Data Matrix only on the cv2 fallback.** 1D barcodes
   (UPC, EAN, Code 128) need pyzbar. If the demo prints
   `cv2.QRCodeDetector (fallback)` and you're trying to read a 1D
   barcode, you need libzbar0.
3. **BGR uint8 input.** Same as exercise 13. If your camera
   subscriber gives RGB, convert first.
4. **Frame provider returns *one* fresh frame per call.** No
   buffering, no average over N frames. The spin loop relies on
   "this is the latest frame at this wrist angle". A caching
   provider would decode the same stale frame 12 times.
5. **No retry on timeout.** Returning `(None, max_steps)` is the
   final answer. The arm controller is responsible for flagging
   the vial; this library doesn't know what to do about it.

## Why no live ROS code here

Same pattern as exercises 3, 13. This library is offline /
synchronous so it can be tested end-to-end in `python demo.py`.
Wrapping it in a ROS node is one short file:

```python
# scan_station_node.py — sketch, lives in exercise 21
class ScanStationNode(Node):
    def __init__(self):
        self.bridge = CvBridge()
        self.create_subscription(Image, "/scan_camera/image_raw",
                                 self._cb, 10)
        self._latest_bgr = None

    def _cb(self, msg):
        self._latest_bgr = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def scan(self, arm, tray_slot):
        from barcode_reader import spin_and_decode
        def provider(step):
            arm.nudge_wrist(2 * math.pi * step / 12)
            rclpy.spin_once(self, timeout_sec=0.2)
            return self._latest_bgr
        return spin_and_decode(provider, max_steps=12)
```

The algorithm doesn't change. Keeping it library-only here means
exercise 21 stays the orchestrator and this folder stays focused.

## Things to revisit later

- Add a regex-validated `decode_barcode` variant — refuses any
  decoded text that doesn't match the expected vial-id pattern.
  Useful when scratches on background vials trigger false reads.
- Add an `average over last N frames` mode for stationary
  pre-checks (e.g. you want to read the rack's own ArUco tag —
  see exercise 10 — without rotating).
- Replace the `qrcode` library with `cv2.QRCodeEncoder` (added
  in OpenCV 4.8) once we want to drop the Pillow transitive dep.
- Add a small `record_frames.py` helper that walks the spin loop
  and saves every frame to disk for offline analysis — handy when
  diagnosing why one specific vial always times out in production.
