# 04 — Imitation Learning Workflow

This workflow is **optional.** You only need it if classical
perception + planning (Layers 3 and the earlier Layer 4 folders) can't
deliver the task. When they can't, the dominant 2025–2026 pattern is
imitation learning: a human demos the task many times and a neural
policy copies them.

Six steps, in order:

1. **[01-pick-teleop-hardware.md](01-pick-teleop-hardware.md)** —
   Choose the teleop rig (leader-follower, SpaceMouse, VR,
   kinaesthetic) that fits your task and budget.
2. **[02-install-and-calibrate-leader-follower.md](02-install-and-calibrate-leader-follower.md)** —
   Set up the leader arm, joint-home both sides, time-sync the data
   stream.
3. **[03-record-demos.md](03-record-demos.md)** —
   Collect 50–200 (or more) clean demonstrations with a planned
   variation grid.
4. **[04-curate-and-clean-dataset.md](04-curate-and-clean-dataset.md)** —
   Drop bad takes, balance the variation bins, hold out an eval
   split.
5. **[05-pick-and-fine-tune-policy.md](05-pick-and-fine-tune-policy.md)** —
   Pick a policy (ACT, Diffusion Policy, VQ-BeT, or a pretrained VLA)
   and fine-tune on your dataset.
6. **[06-evaluate-and-iterate.md](06-evaluate-and-iterate.md)** —
   Evaluate in sim, then real. Find the failure cases. Collect 50
   more targeted demos. Repeat.

You leave this workflow with a learned policy that runs alongside
(or instead of) the scripted task on the real cell. The next step is
[`../05-bring-up-checklist.md`](../05-bring-up-checklist.md).

For the AI background — what ACT, Diffusion Policy, and VLAs *are*
— see Layer 3
[`../../03-software-stack/06-ai-and-foundation-models/`](../../03-software-stack/06-ai-and-foundation-models/).

← Back to: [Layer 4 README](../README.md)
