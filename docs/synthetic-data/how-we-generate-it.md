# How We Generate the Data — The Four Methods

The poster lists four methods at the bottom of the "Synthetic Data"
page:

> **How We Generate It.** Domain Randomization · Procedural Scenes ·
> Photo Real Rendering · Sensor Noise Modelling.

These are the techniques we use *inside* the simulator. They show up
across every [feature](features/) — sometimes one of them, more often
a mix of two or three. This file explains each one in plain English
so you can talk about it on a call.

For deeper, vendor-by-vendor coverage (Isaac Replicator vs Unity
Perception vs Drake vs CARLA, etc.) see
[`industry-methods.md`](industry-methods.md).

## 1. Domain randomisation

**What it is.** On every rendered frame we vary the parts of the
scene that should *not* matter for the task — lighting, textures on
the table and walls, the position of the camera by a few cm,
distractor objects scattered around. The object the model cares
about (a vial, a box, a part) stays the **same** in shape and class.

**Why it works.** A model trained on one scene learns *that one
scene*. A model trained on 50 000 random variations of the same scene
learns the *object*. So when the real camera sees real lighting that
the model has never seen exactly, the model still recognises the
object — because to it, it is just another random lighting.

**What we vary in a typical run.**

| Knob | Range |
|------|-------|
| Light source position | 360° around the cell, varied elevation |
| Light intensity | 100 lux to 2000 lux |
| Light colour temperature | 3000 K to 6500 K |
| Background / wall texture | sample from a library of ~200 textures |
| Camera pose | ± 3 cm position, ± 5° rotation |
| Distractor objects | 0–5 random objects placed on the table |
| Object pose | random within the working area |

**Best platform.** NVIDIA Isaac Sim **Replicator** — a Python API
built exactly for this. Gazebo can do it with a custom Python script
on top of the world file.

**When we use it.** Always. Every feature uses domain randomisation
to some degree.

## 2. Procedural scenes

**What it is.** Code generates the *whole scene* from scratch every
time, not just the lighting on a fixed scene. A random rack layout, a
random number of products on the shelf, random clutter, even random
object identities pulled from a library.

**Why it works.** Domain randomisation varies the *look* of a fixed
scene. Procedural scenes vary the *structure*. So the model also has
to be robust to "shelf is half empty" or "the rack is shifted 10 cm
left" — things a single-scene dataset would never show.

**Concretely.** A procedural-scene script looks like:

```
for episode in range(10_000):
    rack = random_rack_layout()      # 6×8 or 4×12 or scattered
    products = random_product_set()  # subset of the catalogue
    place_products(rack, products)   # with random orientations
    add_clutter(table, count=random.randint(0, 5))
    render_frame()
```

**Best platform.** Isaac Sim Replicator, Google **Kubric** (open
source, Blender backend), Roboverse / RoboCasa for household scenes.

**When we use it.**

- **Feature 4 (rare and edge cases)** — to sweep every combination
  of edge case.
- **Feature 1 (detection)** — when the cell layout itself can
  change.
- **Feature 3 (demonstrations)** — when the task starts from a
  different scene every time.

## 3. Photo-real rendering

**What it is.** Render the frame with **ray tracing** and physically
based materials, so the result looks close to a real photograph.
Light bounces, reflections on glossy surfaces, shadows with soft
edges, glare from a window — all of it modelled physically, not
faked.

**Why it matters.** A model trained on cartoon-looking renders will
look at a real RealSense frame and see something completely
different. A model trained on photo-real frames sees, well, almost
the same image the real camera produces.

**The price.** Photo-real rendering is **slow** and **expensive**. A
ray-traced frame can take ~1 s per frame on a desktop GPU vs ~10 ms
for a rasterised Gazebo frame. We use it only when the customer's
production camera is high quality enough that the realism matters.

**Best platform.**

- **NVIDIA Isaac Sim** with the RTX path tracer — the production
  default.
- **Unreal Engine 5** — used by some AV / industrial customers.
- **Blender Cycles** — if we only need offline rendering, not a
  live simulator.

**When we use it.**

- **Feature 1 (detection)** when the real camera is a RealSense /
  Basler / FLIR.
- **Feature 4 (edge cases)** because glare and shadow are visual.
- **Feature 6 (OCR)** because OCR fails on glare and shadow.

**When we skip it.** Geometric tasks where the camera is just
"checking that the slot is empty" — Gazebo renders are fine.

## 4. Sensor noise modelling

**What it is.** Add **realistic noise** on top of the perfect sensor
reading. Real sensors are messy:

- A real RealSense depth camera has **speckle** on glossy surfaces
  and **dropouts** at depth discontinuities.
- A real Velodyne lidar has **range-dependent variance** and **mixed
  pixels** at object boundaries.
- A real ATI force/torque sensor **drifts** with temperature.
- A real RGB camera has **JPEG artefacts** and **motion blur**.

If the model trains on the *perfect* simulator output, it learns to
expect perfect input. The first time it sees a real, noisy reading it
fails.

**How we do it.** For each sensor we apply a noise model — usually
a math function calibrated against one real-world recording from the
customer. Isaac Sim ships RealSense, Kinect, ZED, and Velodyne noise
models out of the box. For F/T we build a small per-customer model
because every load cell is different.

**Best platform.** Isaac Sim has the largest catalogue of built-in
sensor noise models. MuJoCo has the best contact / friction noise.
Gazebo we extend with custom Python noise layers.

**When we use it.**

- **Feature 2 (depth / pose / grasp)** — depth without speckle is a
  trap.
- **Feature 5 (non-camera sensors)** — this is the *main* method for
  that feature.
- **Feature 1 / 4 / 6** — light camera-noise layer only, to harden
  against blur and compression.

## How the methods combine per feature

| Feature | DR | Procedural | Photo-real | Noise |
|---------|----|------------|------------|-------|
| 1 — Detection images and masks | always | sometimes | for production cameras | light |
| 2 — Depth, pose, and grasp | always | always | when RGB matters | **always** |
| 3 — Demonstration trajectories | always | always | sometimes | sometimes |
| 4 — Rare and edge cases | always | **always** | **always** | light |
| 5 — Non-camera sensors | always | always | rarely | **always** |
| 6 — OCR and barcode renders | always | sometimes | **always** | light |

A "**always**" cell is one we explicitly include in every project of
that feature. A "sometimes" is one we add when the customer's task
demands it.
