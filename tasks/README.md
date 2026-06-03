# Tasks — Worked Problem Statements

The files in this folder are **concrete task specifications** for problems
this project might tackle. Each one is a filled-in version of the framework
in [`../docs/01-finalize-requirements/`](../docs/01-finalize-requirements/):
the 7 core questions from
[`01-understanding-the-problem.md`](../docs/01-finalize-requirements/01-understanding-the-problem.md)
plus the follow-up checklist in
[`02-additional-requirements-to-consider.md`](../docs/01-finalize-requirements/02-additional-requirements-to-consider.md).

These are the *outputs of Layer 1* — the documents you'd take into Layer 2
(hardware selection) and beyond.

## Entries

- [`hplc-autosampler.md`](hplc-autosampler.md) — Loading sample vials into
  an HPLC autosampler tray. The medium-term goal of the project (see
  [`../robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md`](../robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md)).

## How to add a new entry

1. Copy the structure of an existing file.
2. Fill in every line of the two checklists. "N/A" or "don't know yet" are
   valid answers — but mark which is which.
3. Link the new file from the **Entries** list above.
4. Keep it short — one to two pages. Detailed engineering notes belong in
   the robot-specific docs, not here.
