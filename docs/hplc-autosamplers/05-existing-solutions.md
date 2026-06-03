# 05 — Existing Solutions And Companies

> **Who this is for:** Anyone asking "isn't this already a solved
> problem?" The short answer: **yes, at the high end ($50k–$200k)
> and at the research-paper end (low cost but unsupported)** — and
> almost nothing in the middle. That gap is what this project aims
> at.

This doc lists the companies, products, and research projects that
already work in this space. Only links that are clearly relevant
are kept.

## The landscape, in one paragraph

The market for lab automation is well-served at three layers:

1. **Big walk-away workstations** (Hamilton, Tecan, Beckman) —
   tens of thousands to hundreds of thousands of dollars, do
   sample prep + injection, used by big pharma.
2. **HPLC-integrated autosamplers with built-in sample prep**
   (PAL System / CTC Analytics, Agilent Multisampler,
   Waters / Andrew Alliance Andrew+, HTA HT4000L) — usually
   $20k–$100k, bolted onto the HPLC.
3. **Academic open-source projects** (OSCAR, PyLabRobot, Sidekick,
   ABB + Agilent demos) — low cost but research-grade, not
   shipping products.

There is a real **gap between $0 (DIY) and $20k (entry-level
commercial)** for a small lab that just wants to automate tray
loading. That is where this project fits.

## 1. Big walk-away workstations

These are the "we'll do everything" systems. Sample prep, capping,
labelling, plate transport, integration with HPLC and mass spec.
Big footprint, big budget, big software stack.

- **Hamilton Microlab STAR** — the gold-standard liquid handler.
  Used everywhere in pharma QC. Price: ~$100k–$300k depending on
  configuration. Hamilton's
  [Analytical Chemistry page](https://www.hamiltoncompany.com/applications/analytical-chemistry)
  covers their HPLC / LC-MS workflows.
- **Tecan Freedom EVO / Fluent** — the main Hamilton competitor.
  Multiple independent arms; very flexible. Tecan's main
  [liquid-handling product line](https://www.tecan.com/) (see also
  the comparison summary on
  [Sigma-Aldrich PS1049 PDF](https://www.sigmaaldrich.com/deepweb/assets/sigmaaldrich/product/documents/213/124/ps1049en00.pdf)).
- **Beckman Coulter Biomek** — third in the big-three, also $100k+.

> **Why this isn't us:** these systems are built for whole
> sample-prep workflows. They include things our project explicitly
> skips. They also need a separate validation effort for every new
> workflow — for one specific task like tray loading, they are
> overkill.

## 2. HPLC-integrated autosamplers with built-in sample prep

These are the **most directly comparable** commercial products. They
sit on the HPLC and do prep + load + inject as one integrated
machine.

- **PAL System (CTC Analytics)** — by far the most successful
  product in this niche. The PAL has been the de-facto standard
  since 1985.
  - Product home: [palsystem.com](https://www.palsystem.com/en/)
  - **PAL RSI** (Robotic Sample Injection) — entry-level injection
    + basic prep:
    [palsystem.com/.../pal-systems](https://www.palsystem.com/en/products/pal-systems/)
  - **PAL RTC** (Robotic Tool Change) — auto tool changer for full
    walk-away prep:
    [palsystem.com/.../pal-rtc](https://www.palsystem.com/en/products/pal-systems/pal-rtc/)
  - **LEAP Technologies** is the North America distributor:
    [legacy.leaptec.com/ctc-analytics.php](http://legacy.leaptec.com/ctc-analytics.php)
  - Used / refurbished market is active (e.g.
    [American Laboratory Trading](https://americanlaboratorytrading.com/lab-equipment-products/leap-technologies-ctc-hts-pal-autosampler-6244/),
    [LabX listings](https://www.labx.com/product-a/ctc-pal-autosampler)),
    which is good news for budget-constrained labs.

- **HTA HT4000L Autosampler** — explicitly "lab-automation-ready",
  176 × 2 mL vials per run. Closer in spirit to our project
  scope.
  - [iconsci.com/.../ht4000l](https://www.iconsci.com/shop/the-hplc-autosampler-ht4000l/)

- **Agilent 1290 Infinity II Vialsampler with external tray** —
  Agilent specifically supports an **external tray + WalkUp**
  option so that robots can load on the bench and a transport
  step delivers the tray.
  - Product page:
    [agilent.com — 1290 Infinity III LC system](https://www.agilent.com/cs/library/usermanuals/public/G7104ASystem.pdf)
  - Multisampler user manual (mentions external tray):
    [agilent.com — Multisampler User Manual](https://www.agilent.com/cs/library/usermanuals/public/G7167-G5668-G7137-Multisampler-UseMa-en-SD-29000238.pdf)

- **Waters Automation Portal** — Waters' integration layer for
  their ACQUITY / Arc UPLC systems.
  - [waters.com — laboratory-automation-and-equipment](https://www.waters.com/nextgen/us/en/products/laboratory-automation-and-equipment.html)

> **Why this isn't us:** all of these are tied to one HPLC vendor
> (or one autosampler design) and cost in the tens of thousands.
> Our project is meant to be **vendor-agnostic** and run an order
> of magnitude cheaper.

## 3. Cobot integrations (newer, closer to our approach)

This is the segment growing fastest. A cobot sits next to a normal
lab instrument and handles physical transport — the closest match
to our project.

- **ABB GoFa + Agilent Bravo / HPLC integration** — ABB demoed
  exactly this at SLAS 2026: a GoFa robot moving SBS/SLAS plates
  and consumables between a plate hotel, an Agilent Bravo deck,
  and an HPLC. Pipetting, decanting, capping, uncapping.
  - [automate.org — ABB at SLAS 2026 news](https://www.automate.org/robotics/news/turning-ai-into-action-abb-accelerates-the-future-of-lab-automation-at-slas-2026)
  - [Drug Target Review coverage](https://www.drugtargetreview.com/news/193042/abb-robotics-brings-ai-driven-automation-to-life-at-slas-2026/)

- **Waters / Andrew Alliance — Andrew+ pipetting robot** —
  benchtop cobot using off-the-shelf Sartorius electronic
  pipettes. Volume range 0.2 µL to 10 mL.
  - [andrewalliance.com](https://www.andrewalliance.com/)
  - [andrewalliance.com/pipetting-robot](https://www.andrewalliance.com/pipetting-robot/)

- **Opentrons (OT-2 / Flex)** — the most affordable established
  cobot-style liquid handler. AI / generative protocol design.
  - [opentrons.com](https://opentrons.com/)
  - [opentrons.com — protocol library news](https://opentrons.com/archives/news/opentrons-unveils-new-protocol-library-and-generative-ai-tools-to-accelerate-lab-automation-and-scale-scientific-research)

- **Hitachi HPLC preprocessing robot** — Hitachi sells a robot
  specifically for HPLC preprocessing.
  - [shop.cgenomix.com — Hitachi robot for HPLC preprocessing](https://shop.cgenomix.com/archives/6779/transforming-hplc-preprocessing-boosting-efficiency-and-accuracy-with-the-hitachi-robot/)

- **Labman Automation** — UK firm building custom benchtop systems
  including vial weighing and labelling.
  - [labmanautomation.com — sample prep](https://labmanautomation.com/processes/sample-prep/)
  - [labmanautomation.com — vial weighing + labelling system](https://labmanautomation.com/portfolio/custom-system/vial-weighing-labelling-system/)

> **Why this is closest to us:** the cobot pattern (small arm next
> to an existing instrument, doing pickup-and-place + barcode read)
> is exactly what we are building. Our differentiator is **cost
> and openness** — we use a $700 educational cobot and open-source
> tooling, not a $20k+ commercial integration.

## 4. Academic and open-source projects

Most relevant to a learning project. These have published the
hardware, software, and methods, so we can learn from them
directly.

- **OSCAR — Modular Open-Source Robotic Platform for Biological
  Laboratories** (ACS Synthetic Biology, 2025). A 6-DOF cobot with
  a vision-enabled gripper and a pipetting tool. Very close in
  spirit to our project.
  - [pubs.acs.org — OSCAR paper](https://pubs.acs.org/doi/10.1021/acssynbio.5c00733)

- **PyLabRobot** — open-source Python interface for liquid-handling
  robots, including Hamilton STAR and Tecan Freedom EVO. Lets you
  write protocols once and run them on multiple robots. Useful
  reference for our software API design.
  - [pmc.ncbi.nlm.nih.gov — PyLabRobot paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10369895/)
  - [media.mit.edu — PyLabRobot project page](https://www.media.mit.edu/publications/pylabrobot-an-open-source-hardware-agnostic-interface-for-liquid-handling-robots-and-accessories/)
  - [biorxiv.org — full PDF](https://www.biorxiv.org/content/10.1101/2023.07.10.547733.full.pdf)

- **"Leveraging Multi-modal Sensing for Robotic Insertion Tasks in
  R&D Laboratories"** (arXiv, 2023). A robot arm with a wrist
  camera and two camera-based tactile sensors picks a vial from a
  rack and inserts it into a target rack. **This is almost our
  task, on a much higher-end platform.** Excellent reference for
  sensing strategy.
  - [arxiv.org/pdf/2307.00671](https://arxiv.org/pdf/2307.00671)

- **"Facilitating laboratory automation using a robot with a simple
  and inexpensive camera detection system"** (Scientific Reports,
  2025). Low-cost camera + small arm doing exactly the kind of
  affordable workflow we are after.
  - [nature.com — paper](https://www.nature.com/articles/s41598-025-05670-1)

- **Sidekick** — fully 3D-printed liquid-dispensing robot, ~$710
  build cost. The "what does $700 of lab automation actually look
  like?" reference.
  - [ncbi.nlm.nih.gov — Sidekick paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9168727/)

- **Open-source CV + ML framework for affordable lab robotics**
  (arXiv, 2026). Discusses vision-based control of a low-cost arm
  for colony picking and liquid handling.
  - [arxiv.org/pdf/2603.20465](https://arxiv.org/pdf/2603.20465)

## 5. Niche / adjacent — vial filling and capping robots

These are not tray-loading robots, but they handle the same vials
on the prep side. Useful as a sanity check on grip / handling
strategies.

- **Dispense Works Ring Dex** — vial filling and capping.
  - [clpmag.com — Ring Dex](https://clpmag.com/lab-essentials/lab-automation/ring-dex-robot-automates-vial-and-bottle-filling-capping/)
- **MachineLogix VIX** — vial filling, capping, labelling.
  - [machinelogix.com — automated vial system](https://machinelogix.com/laboratory-automation/automated-vial-filling-capping-labeling/)
- **Pester pharma robotic tray loading** — robotic tray loading
  on the *packaging* side of pharma (filled vials into shipping
  trays). Different scale but the same physical primitives.
  - [pester.com — robotic tray loading](https://www.pester.com/en/pharma-solutions/your-topic/pharma-liquid/robotic-tray-loading/)

## 6. Reference articles worth reading

- **HPLC Autosamplers: Perspectives, Principles, and Practices** —
  excellent broad survey of how autosamplers actually work in real
  labs.
  - [chromatographyonline.com](https://www.chromatographyonline.com/view/hplc-autosamplers-perspectives-principles-and-practices)
- **The Rise of Automation in the Chromatography Lab** — market
  framing piece on where automation is heading in chromatography.
  - [elementlabsolutions.com](https://www.elementlabsolutions.com/uk/chromatography-blog/post/automation-in-the-chromatography-lab)
- **Building the Fully Automated Dissolution Lab** — adjacent
  market (dissolution testing) but useful for thinking about full
  walk-away lab automation.
  - [contractpharma.com](https://www.contractpharma.com/building-the-fully-automated-dissolution-lab/)

## 7. What this all means for our project

Reading the list above, three things stand out:

1. **The "small, cheap, tray-only" niche is genuinely
   underserved.** The PAL System dominates the high end. ABB and
   Andrew+ are climbing into the mid range. Below ~$10k there is
   basically only open-source academic work.
2. **The benchtop-tray pattern (load on the bench, human moves
   it) is exactly what Agilent's WalkUp option does.** We are not
   inventing a workflow — we are matching a workflow real
   commercial products already support.
3. **The closest research paper to our task is the arXiv 2307.00671
   "Multi-modal Sensing for Robotic Insertion" paper.** That work
   uses wrist cameras + tactile sensors for vial pick-and-insert,
   on a more expensive arm. We should read it carefully when we
   design our perception stack.

The honest position: **our project is closest to OSCAR plus the
arXiv insertion paper, scaled down to a myCobot-class arm and
focused only on tray loading.** Not a market disruptor; a useful
educational + small-lab tool that fills a real gap.
