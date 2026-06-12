# Outreach Email Templates — DoDAO Robotics Services

Cold-outreach emails for robotics company decision-makers (CEO, co-CEO,
co-founder, VP / senior leadership).

## Writing rules followed in every variant

- Simple English. Short sentences. Words a non-native speaker can read.
- No marketing language. No superlatives ("best", "leading"), no buzzwords
  ("leverage", "unlock", "cutting-edge"), no vague promises.
- Professional and direct. State who we are, what we do, and what the next
  step is.
- Two placeholders only: `[name]` (the recipient's first name) and
  `[company name]` (their company). Everything else is the same across
  every send.
- One link: `https://dodao.io/robotics`. One follow-up commitment:
  written proposal with scope, timeline, and cost within two business
  days.

## What we are pitching (one-line summary used across all variants)

We help robotics teams with two things that come before training and
testing: a clean **simulation world** for the robot (Gazebo or Isaac
Sim), and **labelled synthetic data** for the models (LeRobot, Robomimic,
RLDS, COCO, HDF5, MCAP, YOLO).

---

## Final email (this is the one to send)

Both links below are written in Markdown link form so that, when pasted
into a Gmail / Outlook compose window, the URL is hidden behind the
anchor text. (In Gmail: paste, then press `Ctrl+K` if it doesn't
auto-detect; in Outlook: paste, select the text, and use **Insert link**.)
Sending the URL bare also works — embedding is just cleaner.

**Subject:** Simulation and synthetic data for [company name]

Hi [name],

I am writing from DoDAO. We help robotics teams with two things that
come before training and testing on hardware:

- A clean simulation world for your robot — robot model, workspace,
  sensors, parts, lighting, and physics, built in Gazebo or Isaac Sim.
- Labelled synthetic data for your models — images, masks, depth, pose,
  demonstration trajectories, and edge cases, shipped in the format your
  team already uses.

You can [read more about the services](https://dodao.io/robotics), and a
one-page [overview poster](https://dodao.io/robotics/poster.pdf) is
available too.

Thanks,
Ryan Smith
DoDAO

**Notes on the chosen wording**

- "Two things" replaces the earlier "two pieces of work" — same meaning,
  reads more natural in English.
- Grammar fix: the earlier draft had "If either is useful for [company
  name], You can read more at ..." — the half-sentence and the stray
  capital `Y` are gone.
- No call to action by design. The reader can click either link if
  interested; there is nothing they are asked to do.
- The poster URL assumes the file at `academy-ui/public/robotics/poster.pdf`
  is deployed to `https://dodao.io/robotics/poster.pdf`. If the academy-ui
  app is hosted on a different domain or sub-path, swap the URL — the
  email body does not change.

---

## Variant 1 — Direct introduction

**Subject:** Simulation and synthetic data for [company name]

Hi [name],

I am writing from DoDAO. We help robotics teams with two pieces of
work that come before training and testing on hardware:

1. A clean **simulation world** for your robot — robot model,
   workspace, sensors, parts, lighting, and physics, built in Gazebo or
   Isaac Sim.
2. **Labelled synthetic data** for your models — images, masks, depth,
   pose, demonstration trajectories, and edge cases, shipped in the
   format your team already uses (LeRobot, Robomimic, RLDS, COCO, HDF5,
   MCAP, or YOLO).

If either is useful for [company name], I can send a written proposal
with scope, timeline, and cost within two business days. You can read
more at https://dodao.io/robotics.

Thanks,
[Your name]
DoDAO

---

## Variant 2 — Problem-first framing

**Subject:** Help with simulation or training data at [company name]

Hi [name],

Two questions we often hear from robotics teams:

- Can we check reach, sensor placement, and cell layout before the
  hardware is built?
- Where do we get enough labelled data to train our vision or grasping
  models?

At DoDAO we answer both. We build the simulation world for your robot
(robot model, workspace, sensors, lighting, physics) in Gazebo or Isaac
Sim, and we produce labelled synthetic data (detection, depth, pose,
demonstrations, edge cases) in the format your team already uses.

If this fits any project on the roadmap at [company name], I would be
glad to send a written proposal with scope, timeline, and cost within
two business days. More at https://dodao.io/robotics.

Thanks,
[Your name]
DoDAO

---

## Variant 3 — Short and to the point

**Subject:** Simulation and synthetic data services

Hi [name],

DoDAO works with robotics teams on two pieces of infrastructure:

- A clean simulation world for your robot, built in Gazebo or Isaac
  Sim.
- Labelled synthetic data for your models, shipped in LeRobot,
  Robomimic, RLDS, COCO, HDF5, MCAP, or YOLO format.

If [company name] is starting a project where either would help, I
can send a written proposal with scope, timeline, and cost within two
business days. Details at https://dodao.io/robotics.

Thanks,
[Your name]
DoDAO

---

## Variant 4 — Concrete-detail framing

**Subject:** Simulation and synthetic data for robotics teams

Hi [name],

I am writing from DoDAO. We do two things for robotics teams.

First, we build a clean **simulation world** for the robot. That
covers the robot model, the workspace, sensors and cameras, parts,
lighting and materials, and physics tuning. Built in Gazebo or Isaac
Sim, and shipped as a project folder your team can run.

Second, we produce **labelled synthetic data** for the models.
Detection images and masks, depth and pose labels, demonstration
trajectories, rare and edge cases, and non-camera sensor readings.
Shipped in LeRobot, Robomimic, RLDS, COCO, HDF5, MCAP, or YOLO format.

If [company name] has a project where either would help, send a short
note about what you are building and I will reply with a written
proposal — scope, timeline, and cost — within two business days. More
at https://dodao.io/robotics.

Thanks,
[Your name]
DoDAO

---

## Sender-side notes (not part of the email)

- The signature line `[Your name]` should be the actual sender's name.
- If the recipient does not list a clear first name on LinkedIn or the
  company site, use `Hi there,` rather than guessing. Do not use
  `Dear Sir/Madam`.
- One email per recipient. Do not BCC a list — every send should look
  one-to-one.
- Subject lines do not use `[company name]` in Variants 3 and 4 on
  purpose, so the subject does not look mail-merged. Pick the variant
  that matches the level of personalisation you want.
