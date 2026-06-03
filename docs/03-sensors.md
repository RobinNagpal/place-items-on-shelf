# 03 — Sensors: The Rest Of The Hardware

> **Who this is for:** You have a Layer-1 task spec and a Layer-2 shortlist of
> arm + gripper candidates. Before declaring the hardware decision finished,
> you need to pick the **sensors** that will let the arm *see, feel, and
> measure* its world. Still no code in this doc.

## Why this is "Layer 3" — sensors are hardware

Layer 02 covered the arm and the gripper. That is not the entire hardware
story. A blind, deaf arm can move precisely to coordinates you give it, but it
cannot:

- Know that the cup is *there* (not somewhere else, not knocked over).
- Notice that the gripper is *actually* holding the cup (vs. an empty close).
- Stop when it bumps into something unexpected.
- Adjust force when squeezing a fragile object.

Sensors are how the arm answers those questions. They sit on the **same side
of the build-vs-buy line as the arm and gripper** — they are physical
hardware you procure, mount, wire, and budget for, *before* you start
choosing software.

You also do not pick sensors in isolation: they must mount on the arm or in
the workspace, their weight counts toward the payload, their data has to flow
to the controller, and their position changes how you'll have to calibrate
the system later. So this is genuinely a Layer-2-and-a-half decision.

## A note before you pick sensors: not every project needs every sensor

> "What sensors do we need?" — the honest answer is: **as few as possible.**
> Every sensor adds a wire to break, a calibration to maintain, and a piece
> of software to debug.

Read Layer 1's task spec again and answer these binary questions first:

| Question                                                              | If yes, you need…                                |
|-----------------------------------------------------------------------|--------------------------------------------------|
| Are object positions *known in advance* (fixed jig, taught pose)?     | …probably no perception sensor at all.           |
| Do object positions *vary* (random pose on a table, conveyor)?        | …a 2D or 3D camera.                              |
| Is depth important (stacked items, picking from a bin)?               | …a depth / RGBD camera, not just an RGB camera.  |
| Does the gripper need to *feel* the object (fragile / variable mass)? | …a force/torque or tactile sensor.               |
| Are humans nearby and you can't fully fence the workspace?            | …a safety sensor (laser scanner, light curtain). |
| Does the task involve weighing / measuring objects?                   | …a load cell or scale separately from the arm.   |

`place-items-on-shelf` answers *yes* to the second and third rows and *no* to
the rest — which is why the project ships with one RGBD camera and nothing
else. Don't reach for more.

## The sensor families you'll choose from

The catalogue is large; the families that matter for arm-mounted or
arm-adjacent use are:

1. **2D RGB cameras** — flat colour images. Cheap, well-supported, but only
   tell you "what" and "where in the image", not "how far".
2. **3D / RGBD / depth cameras** — colour + a distance value per pixel.
   The workhorse perception sensor for manipulation. Most "see the object,
   grasp it" demos use one of these.
3. **Force / torque (F/T) sensors** — measure the 3 forces and 3 torques at
   the wrist or fingertip. Used for fragile insertion, contact detection,
   variable-payload tasks.
4. **Tactile / pressure sensors** — measure local contact pressure at the
   fingertips or pad. Newer than F/T; standard for delicate manipulation.
5. **Proximity sensors** — say "something is near" without saying what or
   how far precisely. Cheap, fast, used for collision avoidance and pick
   verification.
6. **Safety sensors** — laser scanners, light curtains, e-stops, safety mats.
   Hardware that satisfies ISO 10218 / ISO/TS 15066 if humans share the
   workspace.
7. **Inertial (IMU) and joint encoders** — almost always built into the arm
   already. Worth knowing they exist; rarely a separate purchase for fixed
   arms.
8. **Environmental** — temperature, humidity, weight (load cells). Niche;
   only buy if Layer 1 explicitly asks.

## Where sensors mount (this matters)

The same camera can do very different jobs depending on where it sits:

- **Eye-in-hand** — sensor mounted on the wrist or gripper. Moves with the
  arm. Good for close-up inspection, fine grasp alignment, in-bin picking.
  Penalty: weight on the wrist eats payload, and the sensor is occluded
  during the grasp itself.
- **Eye-to-hand (external)** — sensor mounted on a tripod, frame, or the
  workspace, looking at the arm. Stable view of the whole scene; classic
  bin-picking setup. Penalty: the arm itself can occlude the workspace
  mid-motion.
- **Gripper-integrated** — F/T or tactile baked into the gripper. Zero
  wiring effort, fixed interface. Penalty: locked into that gripper's
  vendor.
- **Workspace-mounted (non-look-down)** — light curtains, safety scanners,
  load cells *under* the table. Don't move; don't need calibration; protect
  or measure but don't perceive grasp targets.

When you pick a sensor, you pick a mounting strategy at the same time. Both
have to fit Layer 1's workspace dimensions and obstacle list.

## Popular & common sensors by family (early 2026)

Like the arm/gripper map, this is not exhaustive — these are the names you
will see repeatedly in ROS tutorials, research papers, and integrator
quotes. Prices are rough indicative figures and exclude integration.

### 2D RGB cameras

For barcode reading, simple classification, fiducial / AprilTag detection.

- **Basler ace / dart / boost** — industrial GigE / USB3 colour cameras.
  Hugely common in inspection cells.
- **IDS uEye / NXT** — German industrial vision; the NXT family bundles an
  on-camera AI accelerator (closer to the "AI-included" end of the
  spectrum).
- **FLIR / Teledyne Blackfly S** — research-grade GigE / USB cameras.
- **Allied Vision Mako / Alvium** — similar tier to FLIR Blackfly.
- **Raspberry Pi HQ Camera, Logitech C920, Arducam modules** — hobby /
  prototype tier. Fine for `myCobot 280`-style demos; not for production.

### 3D / RGBD depth cameras

The most consequential sensor pick for manipulation projects. Each uses a
different physical principle (stereo, structured light, time-of-flight) with
different strengths.

- **Intel RealSense D435 / D435i / D405 / D455 / D456** — the de facto
  default for ROS manipulation projects since ~2018. Active IR stereo.
  Cheap (~$300), great driver support, every tutorial uses one. ⚠️ Intel
  has wound down new RealSense product development; the D400 series remains
  available through existing inventory and the SDK is still maintained, but
  new long-horizon projects should consider Orbbec as a future-proof
  alternative
  ([Robotics Center, 2026](https://www.roboticscenter.ai/blog/best-depth-cameras-robotics)).
- **Orbbec Gemini 2 / Gemini 2 L / Femto Bolt / Femto Mega** — the most
  credible "RealSense replacement". Femto Bolt/Mega are the official
  successors to the discontinued Microsoft Azure Kinect DK and use the same
  ToF sensor. Gemini 2 L produces smoother and more stable depth than the
  RealSense D455 in recent comparisons
  ([OpenCV, 2026](https://opencv.org/blog/a-quick-comparison-of-the-orbbec-and-realsense-3d-cameras/)).
- **StereoLabs ZED 2 / ZED 2i / ZED X / ZED Mini** — passive stereo cameras
  (no IR projector); works outdoors and at long range where IR projectors
  fail. NVIDIA-GPU-dependent SDK.
- **Photoneo PhoXi (S / M / L) and MotionCam-3D** — structured-light, very
  high-precision (<200 µm), the bin-picking industry standard. Heavier and
  pricier than RealSense (~$10–20k); typically eye-to-hand.
- **Zivid 2 / 2+ / Zivid One Plus** — premium structured-light, sub-100 µm
  accuracy. Often paired with bin-picking AI stacks. Heavy (~1.5–2 kg) — do
  the payload math before wrist-mounting.
- **Mech-Mind Pro / Nano** — vision sensors sold tightly bundled with
  Mech-Mind's bin-picking AI stack. AI-included by design.
- **Roboception rc_visard / rc_reason** — passive stereo + on-camera grasp
  detection software. Popular in EU manufacturing.

### Force / torque sensors

For insertion, fragile contact, polishing, and any task where the arm needs
to *feel* what it's doing.

- **ATI Industrial Automation Mini40 / Mini45 / Axia80 / Axia90 / Gamma /
  Delta** — the long-standing research and industrial standard. Multiple
  payload ranges; well-supported in ROS.
- **Robotiq FT 300-S** — the de facto F/T sensor for Universal Robots
  cobots. Plug-and-play with UR e-series.
- **OnRobot HEX-E v3 / HEX-H v3** — cobot-friendly F/T sensor, broad arm
  compatibility.
- **Bota Systems SensONE / Medusa** — newer entrant, popular in research
  for high signal-to-noise.
- **Built-in (no separate purchase)** — Universal Robots e-series, Franka
  FR3, KUKA LBR iiwa, and Kinova Gen3 all have joint torque sensing that
  produces wrist-equivalent F/T data without an external sensor. If your
  Layer-2 shortlist is one of those, skip the F/T line on the budget.

### Tactile sensors

Newer category, useful for fragile grasps and slip detection. Most are
still research-grade.

- **Contactile (Australian)** — multi-axis fingertip force, commercial.
- **GelSight (multiple research variants and a commercial offering)** —
  optical tactile, very high resolution, used heavily in research.
- **Tacterion** — flexible capacitive films; lower-resolution but easy to
  retrofit.
- **Pressure Profile Systems / Tekscan / Sensitronics** — industrial
  pressure pads and strips.
- **ReSkin (Meta)** — open-source magnetic-skin tactile design used in
  research.

If Layer 1 doesn't explicitly require feeling — for example, "must not
crush the strawberry" — skip this family. It costs design effort, not just
money.

### Proximity & presence sensors

Cheap, fast binary or short-range distance sensors. Mounted on the gripper
or in the workspace.

- **SICK photoelectric and capacitive sensors** — German industrial
  workhorse.
- **Keyence (FS / FU fiber-optic; CapaciTec)** — premium, very small form
  factor.
- **Banner Engineering / Pepperl+Fuchs / IFM Efector** — broad industrial
  catalogue.

Used for: detecting that a part is present in a feeder, that the gripper
actually closed on something, that the workspace is clear before motion.

### Safety sensors (mandatory when humans share the workspace)

If Layer 1 said "humans nearby = yes", you need at least one of these and
probably more than one. They are not optional and are usually specified by
your local equivalent of ISO 10218 / ISO/TS 15066.

- **Safety laser scanners** — SICK microScan3, Keyence SZ-V, Omron OS32C.
  Define safe and warning zones around the cell.
- **Safety light curtains** — Banner, SICK, Omron, Keyence.
- **Pressure-sensitive safety mats** — multiple vendors.
- **Emergency stop buttons** — every cell, always.

Note that cobots (Layer 02's collaborative tier) have built-in joint
torque limits that satisfy *some* of ISO/TS 15066. They don't replace
safety scanners for higher-speed or higher-force operation.

### Inertial sensors and joint encoders (almost always built in)

Joint encoders ship with every arm — that's how the arm knows its own pose.
IMUs are standard on mobile bases but are rarely a separate add-on for a
fixed arm. Worth knowing they exist so you don't budget for what's already
there.

## Practical considerations when picking a sensor

For every candidate sensor, check the following before purchasing — a
sensor that doesn't satisfy these is a sensor you'll be returning.

| Consideration       | What to check                                               | Why it bites later                                          |
|---------------------|-------------------------------------------------------------|-------------------------------------------------------------|
| **Mount weight**    | Sensor mass + cable mass vs. arm's *remaining* payload      | Adds to gripper + object weight; can silently violate payload limits |
| **Field of view**   | Horizontal × vertical FOV vs. workspace dimensions          | Eye-to-hand with too narrow a FOV won't see the whole table  |
| **Working range**   | Min / max depth in metres vs. typical arm-to-object distance | RealSense D405 is 7–50 cm; D435 is 30 cm – 3 m; mismatch = no useful data |
| **Resolution**      | Megapixels (2D) or depth-pixel size (3D)                     | Drives object-size resolvability; over-spec wastes bandwidth |
| **Frame rate (Hz)** | Frames per second at chosen resolution                       | Below 10 Hz feels "laggy"; ≥30 Hz needed for moving objects  |
| **Interface**       | USB3 / GigE / USB-C / Ethernet                               | Some controllers can't host USB3 cameras; GigE needs PoE or a switch |
| **Power**           | Bus-powered or external supply?                              | Bus-powered (USB3) is simpler; external is more reliable     |
| **Driver / SDK**    | ROS 2 driver maintained? Native API?                         | A sensor without a ROS 2 driver is a software project        |
| **Calibration tool**| Vendor calibration utility? Open hand-eye calibration?       | Every camera needs hand-eye calibration; budget the time     |
| **Mounting kit**    | Bracket sold for your arm's wrist flange?                    | "We'll print one" turns into a week of rework                |
| **Price + spares**  | Per-unit price; lead time on replacements                    | A single sensor is fine; a fleet needs a supply story        |

## How to use this layer (the output)

For each plausible sensor, extend the comparison table you built in Layer 02:

```
Sensor row (added below Arm + Gripper):

Sensor model:            ___        ___        ___
Family (RGB / RGBD / FT): ___        ___        ___
Mount mode:              ___        ___        ___
Working range:           ___        ___        ___
FOV / resolution:        ___        ___        ___
Frame rate:              ___        ___        ___
Interface:               ___        ___        ___
Weight (g):              ___        ___        ___
ROS 2 driver?:           y/n        y/n        y/n
Sensor price:            ___        ___        ___
```

The narrowed sensor list, *plus* the arm and gripper from Layer 02, becomes
the **finished hardware spec**. Together they are the input to Layer 04
(software / AI stack), where you ask "given this hardware, what do I build
vs. inherit?".

## Common mistakes at this layer

1. **Buying a sensor without checking the wrist's payload budget.** A
   Zivid 2+ alone weighs about 2 kg — more than the entire payload of a
   myCobot 280.
2. **Overspending on depth precision.** A Photoneo is brilliant; for the
   task "pick a coke can off a table", a $300 RealSense is good enough.
3. **Picking a sensor without a ROS 2 driver.** Writing one is a real
   project. Always check `index.ros.org` and the vendor's GitHub before
   buying.
4. **Forgetting hand-eye calibration.** Every camera-on-arm setup needs it.
   Tools like `easy_handeye` (or vendor utilities) help, but it still takes
   a day on first setup.
5. **Mixing IR sensors that fight each other.** Two RealSense cameras
   pointed at the same object can dazzle each other with their IR
   projectors. Switch one to "no projector" mode or stagger their captures.
6. **Skipping safety sensors.** If a human can step into the arm's
   workspace, a cobot's torque limits alone may not satisfy your local
   safety standard. Add the scanner.

## "Are there libraries or frameworks for this layer?"

Sensor selection itself is procurement — no library helps. Once you've
picked, expect to use:

- **Vendor SDK / ROS 2 driver** — `librealsense2`, `Orbbec SDK` (Femto / Gemini),
  `ZED SDK`, `Photoneo phoxi-control`, `ATI Net F/T`.
- **Hand-eye calibration tools** — `easy_handeye` (ROS), MoveIt's
  calibration plugin, vendor-shipped utilities.
- **Camera-intrinsic calibration** — `camera_calibration` (ROS),
  `Kalibr` (research-grade).
- **Point-cloud processing libraries** — PCL, Open3D — once you have data
  flowing, you'll want these in Layer 05.

These are software choices that belong in Layer 04 / Layer 05 properly — but
the *driver availability* is a Layer-3 procurement filter.

## What's next

With sensors chosen, the hardware side is finished. Layer 04 takes the full
hardware spec (arm + gripper + sensors) and asks the **software question**:
what perception, planning, control, and task-logic stack do you build vs.
inherit, given everything you've now committed to physically?

The four-software-responsibilities framing and the build-vs-buy spectrum
introduced briefly in Layer 02 will be unpacked there in full.

For an in-the-moment view of where the hardware/software line is moving
(humanoids that arrive with perception included, foundation-model "robot
brains" being pre-trained on huge teleoperation datasets), the snapshot in
[`latest-robots.md`](latest-robots.md) is still the right reference.

## Sources

- [Best Depth Cameras for Robotics 2026 — Robotics Center](https://www.roboticscenter.ai/blog/best-depth-cameras-robotics)
- [A Quick Comparison of the Orbbec and RealSense 3D Cameras — OpenCV](https://opencv.org/blog/a-quick-comparison-of-the-orbbec-and-realsense-3d-cameras/)
- [Empirical Comparison of Four Stereoscopic Depth Sensing Cameras for Robotics Applications — arXiv 2501.07421](https://arxiv.org/abs/2501.07421)
