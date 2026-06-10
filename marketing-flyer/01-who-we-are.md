# Page 1 — Who We Are

**Goal of the page.** In 60 seconds of reading, the reader should
know who DoDAO is, what we build, and which two services this flyer
is about. The next three pages go deeper; this one is the door.

---

## Content

### Page title

> Who We Are

### One-sentence intro (sits directly under the title)

> DoDAO builds the simulation and data infrastructure that small
> robotics teams need before they can train, test, and ship a robot
> product.

### Section 1 — What we do

A short paragraph, then three bullet cards. The paragraph anchors
the section; the bullets break it into the two services this flyer
is about, plus the documentation work that ships with both.

**Section heading**

> What We Do

**Section paragraph**

> Two services, both delivered as code, models, and documentation
> that your team owns and can edit.

**Bullet 1 — Simulation setup**

> We build a clean simulation world for your robot — the robot model,
> the workspace, the parts it handles, the sensors, and the lighting.
> Your team gets a project folder that runs on day one.

**Bullet 2 — Synthetic data**

> We render labelled training data inside that same simulator —
> images, depth maps, poses, force traces, and demonstration
> trajectories — in the format your training code already reads.

**Bullet 3 — Documentation and handover**

> Every deliverable ships with a README that another engineer can
> follow without us in the room. We hand over source, not a
> black box.

### Section 2 — Who we work with

Three concise bullets. Each names a real audience type so the
reader can self-identify.

**Section heading**

> Who We Work With

**Bullet 1 — Robotics startups**

> Teams of 1–50 engineers building a robot product who need
> simulation infrastructure before hiring a full-time sim
> engineer makes sense.

**Bullet 2 — Research labs**

> University and industry research groups that need a
> reproducible simulator to run experiments and share results.

**Bullet 3 — Industrial automation pilots**

> Teams piloting cobots or fixed arms in a new cell who want
> to test the layout in simulation before buying hardware.

### Section 3 — Why teams choose us

Three bullets. Each one answers a real objection a CTO would have
in the first meeting.

**Section heading**

> Why Teams Choose Us

**Bullet 1 — Standard tools, no lock-in**

> We work in Gazebo, Isaac Sim, ROS 2, MoveIt 2, and the standard
> dataset formats (LeRobot, Robomimic, RLDS). Nothing you receive
> depends on a tool only we can run.

**Bullet 2 — Plain handover**

> The final deliverable is a git repository, a README, and a
> short walk-through call. No retainer, no support contract
> required to keep the work running.

**Bullet 3 — Honest scope**

> We tell you what we can and cannot deliver before the project
> starts, in writing. If a request is outside our scope, we say
> so and point at a team that can do it.

### Footer (same on every page)

> For more information, visit https://dodao.io     Page 1 of 4

---

## Layout

```
+-----------------------------------------+
|                              [DoDAO ▢] |
|                                         |
|  ▎Who We Are                            |  ← Page title block
|                                         |
|  DoDAO builds the simulation and data   |  ← Intro paragraph,
|  infrastructure that small robotics     |    full width, 11 pt
|  teams need before they can train, …    |
|                                         |
|  ▎What We Do                            |  ← Section 1 heading
|  Two services, both delivered as code…  |  ← Section paragraph
|                                         |
|  • Simulation setup                     |  ← Three bullets
|    We build a clean simulation world …  |    stacked vertically
|  • Synthetic data                       |
|    We render labelled training data …   |
|  • Documentation and handover           |
|    Every deliverable ships with a …     |
|                                         |
|  ▎Who We Work With                      |  ← Section 2 heading
|                                         |
|  • Robotics startups                    |
|    Teams of 1–50 engineers …            |
|  • Research labs                        |
|    University and industry …            |
|  • Industrial automation pilots         |
|    Teams piloting cobots …              |
|                                         |
|  ▎Why Teams Choose Us                   |  ← Section 3 heading
|                                         |
|  • Standard tools, no lock-in           |
|    We work in Gazebo, Isaac Sim, …      |
|  • Plain handover                       |
|    The final deliverable is …           |
|  • Honest scope                         |
|    We tell you what we can …            |
|                                         |
|  For more information, visit            |
|  https://dodao.io        Page 1 of 4    |
+-----------------------------------------+
```

**Block-by-block placement**

| # | Block | Position | Notes |
|---|-------|----------|-------|
| 1 | DoDAO logo | Top-right, ~120 px wide | Identical on every page. |
| 2 | Page title "Who We Are" | Top-left, 36 pt | Accent bar on the left. |
| 3 | One-sentence intro | Full width under the title | 11 pt body, max 2 lines. |
| 4 | Section "What We Do" | Below intro | Heading + paragraph + 3 bullets. |
| 5 | Section "Who We Work With" | Below Section 1 | Heading + 3 bullets. |
| 6 | Section "Why Teams Choose Us" | Below Section 2 | Heading + 3 bullets. |
| 7 | Footer | Bottom, full width | URL left, "Page 1 of 4" right. |

If the three sections do not fit vertically at the spacing in
[`design-system.md`](design-system.md), trim each bullet body to
one sentence before changing the type sizes.
