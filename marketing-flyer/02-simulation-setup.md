# Page 2 — Simulation Setup

**Goal of the page.** Explain what the simulation setup service is,
what the client receives, and which tools we use. The reader should
finish the page knowing whether their project fits this service.

**Source.** Content distilled from the existing service page at
<https://dodao.io/home-section/dodao-io/services/simulation-setup>.

---

## Content

### Page title

> Simulation Setup

### One-sentence intro

> When you start a robotics project, the first step is building a
> clean simulation world. We build that world for you so your team
> can focus on the parts that are unique to your product.

### Section 1 — What we build

A short paragraph plus five bullets covering the five object types
a real cell needs.

**Section heading**

> What We Build

**Section paragraph**

> Every simulation world has five pieces. We build all five for
> your specific use case, then ship the project folder.

**Bullet 1 — Robot model**

> The robot model with the correct joint chain, link frames, and
> joint limits. Loads cleanly in ROS 2 and MoveIt 2.

**Bullet 2 — Workspace**

> The bench, table, floor, fixtures, and any safety enclosures
> around the cell. Matches the real dimensions you give us.

**Bullet 3 — Parts**

> The objects the robot picks, places, scans, or works on —
> modelled at the right size, weight, and material so contacts
> and gripping behave the way they will on hardware.

**Bullet 4 — Sensors and cameras**

> Cameras, depth sensors, force/torque sensors, and barcode
> readers, positioned where they will sit on the real cell so
> the perception code can be developed in sim first.

**Bullet 5 — Lighting and materials**

> Light sources and surface materials set to match the real
> environment so a vision model trained in sim has a chance
> of working on the real camera.

### Section 2 — Tools we use

Two bullets — one per simulator — plus a one-line note about
running both side by side.

**Section heading**

> Tools We Use

**Bullet 1 — Gazebo**

> ROS-native, fast to iterate, free. The right choice when the
> project will live inside the ROS 2 stack and the perception
> work does not need photo-real images.

**Bullet 2 — Isaac Sim**

> Photo-realistic rendering, GPU-parallel rollouts, sensor noise
> models out of the box. The right choice when training data
> needs to look like the real camera, or when reinforcement
> learning needs thousands of parallel environments.

**Bullet 3 — Or both**

> When the project needs both — ROS 2 integration and photo-real
> images — we ship a single asset library and load the same
> models into both simulators.

### Section 3 — What you get

Four bullets describing the deliverable.

**Section heading**

> What You Get

**Bullet 1 — Project folder**

> A git repository with the simulator config, the world file, and
> a launch script. Clone, install dependencies, run.

**Bullet 2 — Models for every object**

> Every robot, fixture, and part as a URDF / USD file with the
> mesh, the colliders, and the inertial properties.

**Bullet 3 — README to run the world**

> A README that another engineer on your team can follow from
> a clean machine to a running simulator without us in the room.

**Bullet 4 — Help wiring in your code**

> A short integration period where we help your team load the
> world from your existing pipeline and answer questions about
> the structure.

### Section 4 — Why start here

A short statement, no bullets.

**Section heading**

> Why Start Here

**Body**

> Simulation is the cheapest place to find a wrong assumption.
> A week spent fixing a problem in sim almost always saves a
> month of rework once hardware is in the loop.

### Footer

> For more information, visit https://dodao.io     Page 2 of 4

---

## Layout

```
+-----------------------------------------+
|                              [DoDAO ▢] |
|                                         |
|  ▎Simulation Setup                      |
|                                         |
|  When you start a robotics project,     |
|  the first step is building a clean …   |
|                                         |
|  ▎What We Build                         |  ← Section 1
|  Every simulation world has five …      |
|  • Robot model                          |
|  • Workspace                            |
|  • Parts                                |
|  • Sensors and cameras                  |
|  • Lighting and materials               |
|                                         |
|  ▎Tools We Use                          |  ← Section 2
|  • Gazebo                               |
|  • Isaac Sim                            |
|  • Or both                              |
|                                         |
|  ▎What You Get                          |  ← Section 3
|  • Project folder                       |
|  • Models for every object              |
|  • README to run the world              |
|  • Help wiring in your code             |
|                                         |
|  ▎Why Start Here                        |  ← Section 4
|  Simulation is the cheapest place to    |
|  find a wrong assumption. …             |
|                                         |
|  For more information, visit            |
|  https://dodao.io        Page 2 of 4    |
+-----------------------------------------+
```

**Block-by-block placement**

| # | Block | Position | Notes |
|---|-------|----------|-------|
| 1 | DoDAO logo | Top-right | Same as Page 1. |
| 2 | Page title | Top-left, 36 pt | Accent bar on the left. |
| 3 | Intro | Under title, full width | 2 lines max. |
| 4 | "What We Build" | Below intro | 5 bullets — the biggest section, give it the most vertical room. |
| 5 | "Tools We Use" | Below Section 1 | 3 bullets, compact. |
| 6 | "What You Get" | Below Section 2 | 4 bullets, compact. |
| 7 | "Why Start Here" | Below Section 3 | One short paragraph, no bullets. |
| 8 | Footer | Bottom | URL left, page number right. |

**If it does not all fit:** drop the intro paragraph above
"What We Build" (the page title already implies the topic), or
collapse "Tools We Use" into two bullets by merging "Or both" into
the Isaac Sim bullet.

This page is the densest of the four. Resist the urge to shrink
type — readers will skim, so they need the same type size as the
other pages.
