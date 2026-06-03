# CLAUDE.md

## What this repo is for

Two things, and only two:

1. **Plain-English documentation** about how to build a real robotic-arm cell —
   from picking the task, to picking hardware, to picking software, to
   integration and bring-up. The general (vendor-neutral) docs live in
   [`docs/`](docs/).
2. **Hands-on simulation playground** for one specific arm — the
   **myCobot 280 Pi**. The robot-specific docs, MoveIt 2 task package, and
   simulation source live under [`robots/mycobot-280-pi/`](robots/mycobot-280-pi/).

No real hardware is required to follow along. Everything works in simulation.

## Where to read first

- [`README.md`](README.md) — 30-second project overview.
- [`docs/README.md`](docs/README.md) — the layered learning walkthrough
  (requirements → hardware → software → integration). Also contains the
  **writing guidelines** to follow when adding or editing docs.
- [`robots/mycobot-280-pi/docs/README.md`](robots/mycobot-280-pi/docs/README.md) —
  myCobot-specific concepts, deep-dives, recipes, and reference.

## When editing docs

Follow the writing guidelines in [`docs/README.md`](docs/README.md). Short
version: simple English, proper Markdown, pinpoint details, no fluff.
