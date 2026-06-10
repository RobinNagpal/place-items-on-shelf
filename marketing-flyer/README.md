# Marketing Flyer — DoDAO Robotics Services

A four-page flyer set sent to small robotics companies. Each page is one
PDF / Canva page. The set as a whole offers two services:

- **Simulation setup** — building a clean simulation world for a robotics product.
- **Synthetic data** — rendering labelled training data inside that simulator.

This folder is the **source** for the Canva design: every page below has
both the **content** (what to type into Canva) and the **layout**
(where each block goes on the page). Designers should be able to open
one `0N-…md` file and reproduce the page in Canva without guessing.

## Audience

Small robotics companies (roughly 1–50 engineers) that:

- Are building a robot product or research prototype.
- Need a simulation world but do not have one yet.
- Need labelled synthetic data to train perception or policy models.
- Do not want to hire a dedicated simulation / data engineer in-house.

The flyer assumes the reader is a technical decision-maker (CTO, head
of engineering, robotics lead). It explains the service in plain
English without assuming the reader has time for buzzwords.

## Pages

| # | Page | Goal |
|---|------|------|
| 1 | [`01-who-we-are.md`](01-who-we-are.md) | Introduce DoDAO and the two services. |
| 2 | [`02-simulation-setup.md`](02-simulation-setup.md) | Explain the simulation setup service. |
| 3 | [`03-synthetic-data.md`](03-synthetic-data.md) | Explain the synthetic data service. |
| 4 | [`04-contact-us.md`](04-contact-us.md) | Tell the reader how to reach us. |

## Design

The visual style follows the existing KoalaGains / DoDAO brand — see
[`design-system.md`](design-system.md) for the page size, colors,
fonts, and the section-and-card pattern lifted from the KoalaGains
GenAI flyer.

Each page file ends with a **Layout** section that says, block by
block, where the content goes on the page.

## Writing rules

These rules apply to every page. They exist so that the four pages
read like one document, not four.

- **Plain English.** Short sentences. Common words. If a sentence
  needs a comma to survive, split it.
- **No marketing language.** Cut "leverage", "unlock", "synergy",
  "best-in-class", "world-class", "cutting-edge", "powerful",
  "seamless", "delight", "empower", "robust", "scalable".
- **Professional, not casual.** No "hey there", no exclamation
  marks, no emojis in the body copy.
- **Cover the whole story without padding.** One sentence is
  enough where one sentence is enough. Add a second only if it
  carries new information.
- **One idea per bullet.** Each bullet has a short bold heading
  (2–4 words) and a 1–2 sentence body. Never a wall of bullets
  with no headings.
- **Be concrete.** Say "Gazebo and Isaac Sim", not "industry-standard
  simulators". Say "two business days", not "fast turnaround".
- **No invented commitments.** Numbers and timelines marked
  `[CONFIRM]` in the source files must be reviewed by the business
  owner before the flyer ships.

## Sources used while writing

- Page 2 (Simulation Setup) content distilled from the existing
  service page at <https://dodao.io/home-section/dodao-io/services/simulation-setup>.
- Page 3 (Synthetic Data) content distilled from
  [`../docs/hplc-autosamplers/synthetic-data/industry-methods.md`](../docs/hplc-autosamplers/synthetic-data/industry-methods.md).
- Visual reference: the existing KoalaGains "GenAI Simulations For
  Every Business School" flyer (page 4 of 5) shared with the brief.

## Workflow for putting this in Canva

1. Open Canva, create a new design, US Letter portrait (8.5 × 11 in).
   The same size on all four pages.
2. Apply the page background color from
   [`design-system.md`](design-system.md).
3. For each of the four pages, open the matching `0N-…md` file, copy
   the **Content** blocks into the Canva text frames described in the
   **Layout** section.
4. Add the DoDAO logo to the top-right corner and the footer line at
   the bottom of every page — both are identical across all four pages.
5. Export as a single 4-page PDF. The file is the marketing flyer.
