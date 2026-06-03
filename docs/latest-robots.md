# Latest Robots — A Snapshot

> **Who this is for:** You're done filtering on physical fit
> ([Layer 02](02-choosing-arm-and-gripper.md)) and you want to know what's
> *new* — especially in the rapidly-changing "AI-included" category where the
> platform comes with perception and a learned manipulation policy out of the
> box.

> **Freshness warning:** This page is a snapshot, dated below. The humanoid /
> foundation-model-driven robot space is moving fast enough that any list
> like this is partly out of date by the time it's written. Treat it as a
> starting point, not a buying decision. Always cross-check current pricing,
> shipping status, and SDK availability with the manufacturer.
>
> **Snapshot date:** mid-2026. Re-check before committing to a platform.

## Why a separate doc for "latest"

The market map in [Layer 02](02-choosing-arm-and-gripper.md) covers the
*established* arms and grippers — names that have been shipping in volume for
years (UR, FANUC, ABB, Robotiq, OnRobot, …). This page is for the **newer
entrants**: humanoids being delivered for the first time, foundation-model
"robot brains" trained on huge teleoperation datasets, and AI-included
manipulation platforms where the value is mostly in the software stack.

These belong in a separate doc because:

- They change month-to-month — the established arms barely move year-to-year.
- Their value proposition is *the AI*, not the mechanical specs.
- Most of them are **not yet commodity hardware** — pricing, availability, and
  SDKs are still in flux.

If you're early in a project and time-to-market matters less than mature
tooling, the Layer 02 map is the right place to look. If your task genuinely
needs "the robot already knows how to grasp varied objects from a description"
and you can absorb some bleeding-edge risk, this page is for you.

## Humanoids actually shipping or in production pilots

The humanoid market hit an inflection point in 2025–2026: more than one
manufacturer is now shipping units to paying customers (factories or homes),
not just demoing on stage
([Technerdo, 2026](https://www.technerdo.com/blog/humanoid-robots-market-2026);
[EVS, 2026](https://www.evsint.com/top-8-humanoid-robot-companies-2026/)).

- **Figure AI — Figure 03.** Bimanual humanoid. Completed an 11-month pilot
  on the BMW Spartanburg line, contributing to assembly of 30,000+ vehicles.
  Figure's "BotQ" facility is tooled for ~12,000 Figure 03 units / year.
  Sold to enterprise / industrial customers, not consumer.
- **Tesla — Optimus (Gen 3).** Deployed inside Tesla factories. Ramping
  internal production; no third-party commercial availability confirmed yet.
  Tesla has talked about a sub-$20k consumer Optimus by 2028 — treat as a
  target, not a commitment.
- **1X Technologies — NEO.** Consumer-targeted home humanoid. Early
  deliveries beginning in late 2026 at ~$20k. First credible "humanoid in
  your house" product.
- **Apptronik — Apollo.** $935M+ total funding, $5B valuation after a $520M
  Series A round led by strategic investors including Google. Pilots running
  with Mercedes-Benz (manufacturing) and GXO Logistics (warehousing).
- **Unitree Robotics — G1 and H1.** G1 is commercially available for direct
  purchase. Unitree shipped ~5,500 units in 2025 across its line and is
  targeting 10–20k units in 2026 — by far the highest-volume humanoid maker
  on this list.
- **Agility Robotics — Digit.** Bipedal logistics humanoid, deployed at
  Amazon and other warehouse customers. Sells as a service in some
  deployments rather than a one-off purchase.
- **Sanctuary AI — Phoenix.** Canada-based, focused on general-purpose
  manipulation with proprietary "Carbon" AI control system.
- **Boston Dynamics — Atlas (electric).** Fully-electric Atlas (the
  hydraulic version retired in 2024). Hyundai-owned; targeting automotive
  manufacturing customers.

If your task is *industrial manipulation in a structured environment*,
expect Figure, Apptronik, and Digit to be live commercial conversations in
2026. If your task is *home or consumer*, only 1X NEO has actually started
shipping at this snapshot; everyone else is roadmap-only.

## "AI-included" manipulation platforms (non-humanoid)

These are tabletop / mounted arms whose value is the included perception +
grasp policy, not the arm itself. Many of them mount on commodity cobots
(UR, Franka, etc.).

- **Physical Intelligence — π0 / π0-FAST policies.** A foundation-model
  control policy trained on a large multi-embodiment teleoperation dataset.
  Doesn't ship hardware; ships the brain that runs on top of arms like the
  Franka FR3 or a bi-manual ALOHA-style rig.
- **Covariant — "Brain".** Vision + manipulation policy as a service,
  integrated with cobots / industrial arms for warehouse pick-and-place.
- **Dexterity AI.** Pick-and-place and palletising stack for logistics
  customers; usually shipped on top of major-brand arms.
- **Skild AI.** "General-purpose robot intelligence" foundation model, very
  hardware-agnostic.
- **Mech-Mind, Photoneo, RightHand Robotics.** AI bin-picking and parcel
  induction stacks. Less "general intelligence", more "battle-tested
  computer vision + grasp planning" — but reliable, and often the right
  pick for narrow industrial tasks.

If you walked into Layer 02 thinking "we need to pick coloured products and
I don't want to write a perception stack", any of the names above will get
you further faster than building from `OpenCV` + `MoveIt` yourself. The
trade-off is platform lock-in and a much higher per-unit license cost.

## Cobots with growing AI / vision integration

A few of the established cobot families are visibly closing the gap to the
"AI-included" platforms above:

- **Techman Robot TM AI Cobot series.** Eye-in-hand camera + TMflow vision
  SDK has been the headline feature for years; recent generations add
  on-device deep-learning models for classification and grasping.
- **Standard Bots RO1.** US-market 6-DOF cobot with an "AI operator"
  programming interface — closer to natural-language task setup than
  traditional teach pendants.
- **Universal Robots + UR+ ecosystem.** UR doesn't bundle AI itself, but the
  certified UR+ ecosystem (over 1,000 partner components) includes virtually
  every AI vision and grasping add-on from the names above.

## Robot "brains" worth knowing (foundation models)

You may see these names in papers, demos, and press releases. They are
*models*, not hardware — but they materially change what hardware is viable.

- **Physical Intelligence π0** — generalist robot policy, multi-embodiment.
- **Google DeepMind RT-2 / RT-X** — earlier vision-language-action models.
- **OpenVLA / OpenVLA-OFT** — open-source vision-language-action models.
- **NVIDIA GR00T** — humanoid foundation-model effort, paired with NVIDIA
  Isaac simulation.
- **Skild AI brain** — foundation policy for arbitrary embodiments.

Most are pre-commercial or limited-release. Track them on Hugging Face and
the major robotics conferences (RSS, CoRL, ICRA, IROS) rather than vendor
sites.

## What this list implies for *our* project

`place-items-on-shelf` deliberately targets a structured, well-defined task
on a low-cost hobby arm (myCobot 280 Pi). For that profile:

- Humanoids and "robot brains" are **not** in scope — they're aimed at
  unstructured or general-purpose tasks where their cost is justified.
- The right reference point is the AI-included cobot tier (Techman, Standard
  Bots) if we ever want to grow into vision-driven object selection without
  the AI rewrite.
- Foundation-model policies (π0, OpenVLA) are interesting to track even now
  — running an open VLA on a cheap arm is increasingly viable as a research
  exercise.

When Layer 03 (software / AI) lands, the table from Layer 02 plus this
snapshot become the inputs to "build vs. buy" for the perception and
manipulation stack.

## How to keep this file fresh

Every 3–6 months:

1. Re-run a quick search for "humanoid robots shipping" and "robot
   foundation models" to refresh the snapshot date and the bullet points
   above.
2. Drop anything that's been cancelled or absorbed; add anything new with a
   real pilot or shipment.
3. Bump the **Snapshot date** at the top of the file.
4. Do **not** rewrite Layer 01 / Layer 02 in response to this churn — the
   structured-decision framework holds even as the names underneath it
   change.

## Sources

- [Humanoid Robots in 2026: Market Leaders, Deployments — Technerdo](https://www.technerdo.com/blog/humanoid-robots-market-2026)
- [Top 8 Humanoid Robot Companies to Watch in 2026 — EVS](https://www.evsint.com/top-8-humanoid-robot-companies-2026/)
- [Humanoid Robots 2026: Tesla Optimus vs Figure AI vs Unitree — LumiChats](https://lumichats.com/blog/humanoid-robots-2026-tesla-optimus-figure-ai-unitree-complete-guide)
- [Humanoid Robot Comparison Tracker (2026) — New Market Pitch](https://newmarketpitch.com/blogs/news/humanoid-robotics-robot-comparison)
- [Top 10 Collaborative Robot Brands by Market Share 2026 — EVS](https://www.evsint.com/top-collaborative-robot-brands/)
