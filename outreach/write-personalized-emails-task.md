# Task — Write Personalized Outreach Emails

A worked task spec for drafting the first-touch outreach email to one
named contact at a robotics company in this folder. Use it as the input
brief for a session that turns rows in `outreach/pending/*.csv` into
ready-to-send email drafts.

Companion to [`find-outreach-companies-task.md`](find-outreach-companies-task.md),
which produces the CSV rows this task consumes. Sending the drafts is
handled separately by the `outreach-data` agent in the parent
Discord-bot project — this task only writes the copy.

## Goal

For each eligible contact, draft one short, personalized first-touch
email that:

- Names the contact and references the specific robot or product they
  build (using the `note` and `relevance` columns from the source CSV).
- Connects that product to one of DoDAO's two offerings (Simulation
  Setup or Synthetic Data — see <https://dodao.io/robotics>) with a
  reason a roboticist would recognise as true.
- Ends with one low-friction call to action (a 15-min call, or a reply
  with a sample dataset).

A drafted email is "personalized" if a reader who knows the company
would say "this was clearly written for us, not blasted to a list."
Re-using the same sentence about the product across two companies fails
this bar.

## Inputs — which rows are eligible

Read from `outreach/pending/*.csv`. A row is eligible when **all** of:

- `email` is non-blank (a primary-source-verified address, per the
  find-companies brief).
- `contact_name` is a real person, not an office or team alias.
- `note` and `relevance` are both filled in.
- No draft already exists for that contact under `outreach/drafted-emails/`
  (check by exact `email` match in the frontmatter).

Skip — do not draft — when:

- The row is in `outreach/done/`. Those companies have already been
  contacted; followups are a separate task.
- `email` is blank. Drafting for a guessed address damages sender
  reputation when it bounces.
- The contact is a generic alias (`info@`, `contact@`, `team@`,
  `hello@`). The find-companies brief rejects these, but spot-check.

## The pitch — what DoDAO sells

Same two offerings as the find-companies brief; pick the one that fits
the row's `relevance` sentence:

- **Simulation Setup** — a clean simulation world (robot model,
  workspace, sensors, parts, lighting, physics) in Gazebo, Isaac Sim,
  or MuJoCo. Lead with this when the company needs faster iteration,
  pre-hardware validation, or a controlled environment for policy
  rollouts.
- **Synthetic Data** — labelled images, masks, depth, pose, and
  demonstration trajectories in standard formats (RLDS, COCO, HDF5,
  MCAP, YOLO). Lead with this when the company is data-starved (rare
  procedures, long-tail edge cases, expensive teleop sessions, hard-to-
  label corner cases).

Pick one. Mentioning both dilutes the email and reads like a brochure.

## Email structure

Keep the whole email under 130 words. Aim for four short paragraphs.

1. **Greeting** — `Hi <first name>,`. Use the first name from
   `contact_name` only; never `Dear Dr.` unless the title in `position`
   explicitly includes `Dr.` or `Prof.`.
2. **Opener (1 sentence)** — name the company and the specific product
   from `note`. Example: `Saw the writeup on Versius and how CMR is
   pushing modular soft-tissue robotics.`
3. **Fit paragraph (2-3 sentences)** — restate the `relevance` reason
   in your own words, then connect it to the chosen offering. This is
   the personalized core — it must be different for every email.
4. **Offer + CTA (1-2 sentences)** — a single, specific ask. Examples:
   `Worth a 15-min call next week to see if a sample Isaac Sim scene
   for <product> would be useful?` or `Happy to send a labelled
   synthetic dataset for <task> — interested?`.
5. **Sign-off** — `Warm regards,` / `Ryan Smith` / `Outreach @ DoDAO` /
   LinkedIn URL. Same sign-off used by the existing outreach-data
   agent.

## Personalization rules

- The fit paragraph must name the product (from `note`) and the use
  case (from `relevance`). Generic phrasing like "your robotics work"
  is a failure.
- Do not invent capabilities. If the source row does not back a claim,
  do not make it. When in doubt, drop the sentence.
- Do not use buzzwords as personalization (`AI-native`, `cutting-edge`,
  `revolutionary`). They read as automated.
- Vary the opener and the CTA across the batch. Repeated phrasing is
  detectable when contacts at related companies compare notes.

## Style rules

- Plain English, short sentences. No marketing voice.
- No em-dashes, no `<p>` tags. Use `<br>` for line breaks if writing
  HTML, matching the existing outreach-data agent's convention.
- No attachments referenced in the first email. Links only.
- One link maximum in the body, plus the LinkedIn URL in the sign-off.
- US English spelling.
- No subject-line clickbait. The subject should describe the email
  honestly. Examples: `Synthetic data for <product>`, `Sim worlds for
  <company> R&D`, `Quick question on <product> data pipeline`.

## Output

Write each drafted email to its own file under
`outreach/drafted-emails/<contact-slug>.md`, where `<contact-slug>` is
the contact's first and last name lowercased and hyphenated (e.g.
`massimiliano-colella.md`). Create the `drafted-emails/` folder if it
does not exist.

Each file uses this exact format:

```markdown
---
to: <email>
contact_name: <contact_name>
position: <position>
company: <name>
source_csv: outreach/pending/<file>.csv
offering: simulation-setup | synthetic-data
---

Subject: <subject line>

<body, with <br> for line breaks if HTML, or plain text paragraphs>
```

The frontmatter is the audit trail — it tells the sending agent which
address to use and which CSV row this draft came from.

In the PR description, include:

1. **Count** — e.g. `8 drafts written across 3 source CSVs`.
2. **Per-draft table** — `contact_name`, `company`, `source_csv`,
   `offering`, `subject`.
3. **Spot-check log** — pick 3 random drafts and confirm: (a) the
   product name in the body matches the source `note`, (b) the
   `relevance` reason is honestly represented, (c) the CTA is specific
   and low-friction.

## Done when

- Every eligible row in the named source CSVs has exactly one draft
  file under `outreach/drafted-emails/`.
- Every draft has frontmatter with all six fields populated.
- Every draft body names the specific product and connects it to one
  (and only one) offering.
- No two drafts share an opener sentence or a CTA sentence verbatim.
- No draft makes a claim that is not supported by the source row.
- The PR description spot-check table is filled in for 3 drafts.

## Out of scope

- **Sending email** — handled by the `outreach-data` agent in the
  parent Discord-bot project.
- **Followup emails** — separate task. The outreach-data agent has
  dedicated `send-followup1` / `send-followup2` jobs for that.
- **Finding new companies or contacts** — see
  [`find-outreach-companies-task.md`](find-outreach-companies-task.md).
- **Enriching missing `email` cells** — separate
  `outreach-personal-emails-*` PR series. If a row has no email, leave
  it for that task; do not draft.
