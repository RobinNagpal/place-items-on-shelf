# Task — Find Outreach Companies

A worked task spec for adding more rows to the outreach CSVs in this
folder. Use it as the input brief for a session that researches new
companies, scores them, and writes them into the right CSV.

## Goal

Add more robotics companies to the CSVs in this folder that fit DoDAO's
robotics offering (see <https://dodao.io/robotics>). For each company,
record what they build, why they fit, and the highest-ranking publicly
named contact.

DoDAO sells two things:

- **Simulation Setup** — a clean simulation world (robot model, workspace,
  sensors, parts, lighting, physics) in Gazebo / Isaac Sim / MuJoCo.
- **Synthetic Data** — labelled images, masks, depth, pose, demonstration
  trajectories, edge cases, in standard formats (RLDS, COCO, HDF5, MCAP,
  YOLO).

A company "fits" if it builds or operates a **physical robot product**
whose perception, motion, or manipulation stack would benefit from one
of the two.

## Where to put each new company

| If the company is... | Add to... |
| --- | --- |
| Small US robotics product company | `robotics-companies-us-small-relevant.csv` |
| Humanoid or robotics foundation-model team | `robotics-companies-humanoid-foundation-models.csv` |
| Warehouse / logistics arm or robot company | `robotics-companies-warehouse-logistics.csv` |
| Tagged for review but does not fit | `robotics-companies-us-small-irrelevant.csv` |

If a category does not exist yet (e.g. EU surgical robotics), create a
new CSV with the same schema as the matching relevant file and link it
from this section in the PR description.

## CSV schemas

Relevant lists (4 files above except the irrelevant one):

```
name,relevance,note,contact_name,position,email
```

Irrelevant list:

```
name,relevance,note
```

| Column | Content |
| --- | --- |
| `name` | Company name as it appears on its own website. |
| `relevance` | One sentence on how the company fits the simulation + synthetic-data offering. For the irrelevant CSV, the literal word `irrelevant`. |
| `note` | What the company actually builds, in one short noun phrase (e.g. `AI-powered warehouse sorting robots`). |
| `contact_name` | Highest-ranking publicly-named founder / CEO / CTO. |
| `position` | Their title at the company. |
| `email` | Personal or work email, only if verified from a primary source (see below). Blank otherwise. |

## Where to search

- YC, Techstars, Plug and Play robotics-cohort pages.
- Crunchbase, filtered by `industry: robotics`, `location: US`,
  `employees < 200`.
- The Robot Report, TechCrunch robotics, Robotic Industries Association
  press releases.
- LinkedIn company search by industry and headcount.
- Targeted Google searches like
  `"robot arm" startup site:techcrunch.com 2025`.

## Inclusion criteria — must pass all

- Builds, sells, or operates a **physical robot product** — not pure
  software or SaaS.
- Has a public website with a product page.
- Headquartered in the US, or a major robotics hub (Tokyo, Munich,
  Zurich, Shanghai, London). Note the location in `relevance` if
  non-US.
- Not already present in any of the four CSVs (check `name` exact match
  and a fuzzy match for renames).

## Exclusion criteria — any one means irrelevant

- Aerial drones (different sim ecosystem).
- Marine / underwater (different sim ecosystem).
- Defense weapons systems (won't engage / ethical).
- Pure component vendors — motors, gearboxes, sensors only — with no
  integrated robot product.
- Autonomous-vehicle software stacks (CARLA, not Gazebo).
- Service-only integrators that compete with DoDAO.
- Defunct, acquired, or with no working contact path.

Borderline cases go in the irrelevant CSV with a one-line `note`
explaining the call.

## Email verification rules

The `email` column only accepts addresses verifiable from a **primary
source**:

- The company's own website (team / about / contact page).
- A document published by the company (PDF, blog, conference booth
  listing).
- The contact's own public post (e.g. a CEO tweeting their address, a
  university faculty page).
- An SEC filing or other regulatory document.

Reject:

- Pattern guesses such as `firstname@company.com`.
- Data-broker hits — RocketReach, ZoomInfo, ContactOut, Apollo,
  Crunchbase exports.
- LinkedIn-only addresses behind the paywall.

Blank is better than wrong — a bounced address damages the sender
domain reputation.

## Output

In the PR description, include:

1. **Count and bucket breakdown** — e.g. `12 rows added: 7 relevant
   (small US), 3 humanoid, 2 irrelevant`.
2. **Per-row summary table** — `name`, `note`, `contact_name`,
   `position`, `email present? (Y / N + source)`.
3. **Spot-check log** — pick 5 random new rows and confirm the company
   exists, the contact name + title match the cited primary source, and
   the `relevance` sentence is true.
4. **New CSVs created**, if any, and why.

## Done when

- Every new row passes the inclusion criteria above.
- Every new row lands in the correct CSV (or a new CSV is created and
  added to the [Where to put each new company](#where-to-put-each-new-company)
  table).
- Every non-blank `email` cell cites a primary source in the PR
  description.
- The PR description spot-check table is filled in for 5 rows.
- No duplicates against existing CSV rows.

## Out of scope

- **Sending email** — handled by the `outreach-data` agent in the
  parent Discord-bot project.
- **Writing email copy** — separate task.
- **Personal-email enrichment of existing rows** — separate
  `outreach-personal-emails-*` PR series.
- **Re-tagging existing rows** as relevant or irrelevant — separate
  `find-emails-task` style PR.
