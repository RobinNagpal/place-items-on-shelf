# 05 — Existing Solutions And Companies

> **Who this is for:** Anyone asking "isn't this already a solved
> problem?" Short answer: **at the high end yes, in the middle
> almost nothing**, and that gap is where this project sits.

This doc only lists products and projects I've read and confirmed
are relevant. Generic "lab automation" pages with no concrete tie
to vial tray loading have been left out.

## 1. The high-end "do everything" workstations

Hamilton STAR, Tecan Fluent, Beckman Biomek. **$50k–$300k**,
full sample-prep + injection workflows for big pharma. They are
not our reference points — the price gap is too wide and most of
what they automate (pipetting, dilution, plate transport) is out
of scope for v1.

## 2. HPLC-integrated autosamplers with built-in sample prep

These are the products closest to what a lab would buy *instead
of* our project. Reading them shows what we are competing with
in terms of vendor-supplied features. Capsule on each:

### PAL System — PAL RTC (CTC Analytics)

[palsystem.com/.../pal-rtc](https://www.palsystem.com/en/products/pal-systems/pal-rtc/)

The PAL RTC is the gold-standard HPLC sample-prep autosampler.
It automatically switches between **injection tools and
sample-prep tools** (SPME, micro-SPE, derivatisation, dilution,
protein digestion) and runs unattended **24/7** with all major
GC, LC, and MS instruments.

> **How it relates to us:** the PAL RTC is what a well-funded
> lab would buy to *avoid* needing our robot. It targets the
> full sample-prep + injection pipeline; we target only the
> last "load the tray" step at a tiny fraction of the price.
> The PAL's tool-changer pattern is also a useful idea for a
> hypothetical v2+ of our project (gripper change for different
> vial sizes).

### HTA HT4000L Autosampler (Icon Scientific)

[iconsci.com/.../ht4000l](https://www.iconsci.com/shop/the-hplc-autosampler-ht4000l/)

A modular HPLC autosampler with **176 × 2 mL** capacity,
interchangeable racks for **2 / 4 / 6 / 10 / 20 / 40 mL vials**
plus test tubes and microplates, and a drag-and-drop method
editor (HTAPREP) for custom workflows. Markets itself as
"lab-automation-ready."

> **How it relates to us:** confirms that **modular, swappable
> racks** are a real customer feature, not a niche. If our robot
> can load the HT4000L's standard 2 mL rack on the bench and a
> human transfers it in, we are matching the workflow this
> product is built for. The HT4000L's documentation does not
> explicitly describe a robot-load interface, but the fact that
> capacity is described in interchangeable trays means there is
> a physical tray that can be loaded outside the instrument.

### CTC HTS PAL Autosampler (refurbished, via American Laboratory Trading)

[americanlaboratorytrading.com/.../leap-technologies-ctc-hts-pal-autosampler-6244](https://americanlaboratorytrading.com/lab-equipment-products/leap-technologies-ctc-hts-pal-autosampler-6244/)

An older PAL-family autosampler with **600+ × 2 mL** vial
capacity (or 24 microplates) in just 50 cm of bench. Acts as a
**robotic liquid handler**: opens a stack drawer, aspirates from
the microplate, injects directly into the LC valve. Peltier-cooled
sample storage (4–40 °C).

> **How it relates to us:** this listing is on a **refurbished
> equipment** site (currently out of stock) — i.e. a budget-
> conscious lab buying a used CTC PAL is a real and direct
> competitor to our project. Worth knowing the price point and
> the feature gap: the CTC PAL handles 600 vials and integrated
> injection; our robot will start far below that scale but at a
> fraction of the cost.

### Andrew+ Pipetting Robot (Waters / Andrew Alliance)

[andrewalliance.com/pipetting-robot](https://www.andrewalliance.com/pipetting-robot/)

A benchtop cobot from Waters / Andrew Alliance. **0.2 µL – 10 mL
pipetting** with off-the-shelf electronic pipettes, **Domino**
modular labware holders, optional vacuum / heating / shaking
add-ons. Fits in a biosafety cabinet — about **53.5 × 43 × 45.5 cm,
16 kg**. Programmed through OneLab software.

> **How it relates to us:** the closest "small cobot in a lab"
> commercial product I found. The Andrew+ is sold as a sample-prep
> tool — its documentation does **not** explicitly mention HPLC
> autosampler vials or autosampler tray loading, and there is
> "no explicit coverage of automated vial decapping or tray
> loading" in the published feature set. That gap is exactly the
> niche our project occupies: small cobot, but pointed at tray
> loading rather than pipetting.

## 3. Cobot demos and adjacent commercial work

Worth knowing about but not direct competitors:

- **ABB GoFa + Agilent (SLAS 2026 demo)** —
  [automate.org](https://www.automate.org/robotics/news/turning-ai-into-action-abb-accelerates-the-future-of-lab-automation-at-slas-2026).
  ABB demoed a GoFa cobot moving SBS/SLAS plates between a plate
  hotel, an Agilent Bravo deck, and an HPLC — pipetting, decanting,
  vial cap/uncap. Larger scope than ours, same pattern.
- **Hitachi HPLC preprocessing robot** —
  [shop.cgenomix.com — Hitachi for HPLC preprocessing](https://shop.cgenomix.com/archives/6779/transforming-hplc-preprocessing-boosting-efficiency-and-accuracy-with-the-hitachi-robot/).
  Hitachi sells a robot specifically for HPLC preprocessing.
  Useful evidence that the niche is recognised in industry.

## 4. The closest research paper

**"Leveraging Multi-modal Sensing for Robotic Insertion Tasks in
R&D Laboratories"** (arXiv 2023). A cobot with a wrist camera and
camera-based tactile sensors **picks a vial from a rack and
inserts it into a target rack**. This is essentially our v1 task,
on a more expensive platform.

[arxiv.org/pdf/2307.00671](https://arxiv.org/pdf/2307.00671)

> **How it relates to us:** the methodology is directly
> transferable. Read this when designing perception and grasp
> verification.

**OSCAR — Modular Open-Source Robotic Platform** (ACS Synthetic
Biology, 2025). 6-DOF cobot with vision-enabled gripper and a
pipetting tool, doing standard lab manipulations. Close in
spirit to our project.

[pubs.acs.org — OSCAR paper](https://pubs.acs.org/doi/10.1021/acssynbio.5c00733)

> **How it relates to us:** good reference for "what does an
> open, low-cost lab cobot actually look like end-to-end."

## What this all means for our project

Reading the four "HPLC-integrated" products together with the
ABB + Hitachi demos:

1. **The "$0 to ~$10k, tray-loading only" niche is genuinely
   empty.** PAL / HTA / CTC start at much higher prices and
   include features (prep, injection, cooling) we don't aim for.
   Andrew+ is in the right size class but pointed at pipetting,
   not tray loading.
2. **The "benchtop tray, robot loads, human transfers" pattern
   is the right one** — it matches the workflow these
   commercial products already use (interchangeable racks,
   external trays).
3. **Our differentiator is scope + cost.** A ~$700 cobot focused
   only on tray loading, with open code and a clean LIMS hook.

The honest position: we are not building the next PAL. We are
filling the price gap underneath it.

## What's next

→ Next: [`../requirements/`](../requirements/) — the
requirements themselves, broken out by topic.
