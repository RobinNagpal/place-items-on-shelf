# 06-e — Vision-Language-Action Models (VLAs)

VLAs take in **vision** + a **natural-language instruction** + the
**robot's current state**, and output **action sequences** directly.
The headline category of "robot foundation models."

A VLA is, in effect, a large neural-network policy that has seen many
robots, many tasks, and many language descriptions during pretraining.
You fine-tune (or sometimes zero-shot) on your task.

## Common use cases

- **Multi-task robots** that need to handle a long tail of jobs
  without retraining per task.
- **"Tell the robot what to do"** interfaces — kitchen, household,
  flexible warehousing.
- **Pretraining base** for your own imitation-learning fine-tunes
  (see [06-c](06-c-imitation-learning.md)).
- **"AI-included" commercial platforms** — the customer pays for the
  policy, not the arm (see
  [`../02-hardware-selection/latest-robots.md`](../02-hardware-selection/latest-robots.md)).
- **Long-horizon tasks** where pure perception + planning fall short.

You **don't** want a VLA when:

- The task is fixed and tight cycle time matters more than
  flexibility.
- You don't have the data or compute to fine-tune one usefully.

## Frameworks / libraries / methods

### Closed / commercial VLAs

- **Pi-0, Pi-0.5 (Physical Intelligence)** — the most-discussed VLA
  as of late 2025–2026. Sold via partnerships, not open weights.
- **RT-1, RT-2, RT-2-X (Google DeepMind)** — the original "robot
  transformer" line. Mostly closed; small distilled checkpoints
  available.
- **GR00T (NVIDIA)** — humanoid-focused foundation model, paired
  with Isaac Sim.

### Open-source VLAs

- **OpenVLA** — open-source VLA, easier to fine-tune. Built on a
  Prismatic / Llama backbone, trained on Open X-Embodiment.
- **OpenVLA-OFT** — instruction-tuned variant.
- **Octo (Berkeley)** — open VLA, smaller and faster than OpenVLA.
- **RDT (Robotics Diffusion Transformer)** — diffusion-based VLA.
- **Manipulate-Anything, RoboFlamingo, RoboCat** — research VLAs.

### Skill-policy hybrids

Not strictly end-to-end VLAs, but used in the same slot:

- **Skild AI brain** — foundation policy claimed to be very
  hardware-agnostic.
- **Covariant Brain, Dexterity** — commercial VLA-ish stacks for
  warehouses.

## How to pick

1. **Production deployment with budget?** → Pi-0.x via a Physical
   Intelligence partnership, or a bundled industrial VLA.
2. **Research, open weights, fine-tunable?** → OpenVLA or Octo.
3. **Diffusion-based experimentation?** → RDT.
4. **Humanoid?** → GR00T (if you can get access).
5. **You don't actually need a VLA?** → Use an IL policy from
   [06-c](06-c-imitation-learning.md). Most "AI robot" demos in 2026
   are still just well-tuned ACT or Diffusion Policy.

## Where it runs

- **OpenVLA (7B parameters)** — runs on a single RTX 4090 or A6000 at
  ~3–6 Hz. Fits on a Jetson Orin AGX at INT8.
- **Octo (small variants)** — comfortable on a Jetson Orin AGX.
- **Pi-0** — Physical Intelligence ships their own runtime; usually a
  workstation-class GPU.
- **GR00T** — requires NVIDIA's stack; an Isaac-Sim-paired runtime.

For latency-sensitive control, run the VLA at slow cadence (1–5 Hz)
to emit *high-level intents*, and let a lower-level controller
(MoveIt, vendor driver) execute at full rate. See
[06-h](06-h-where-models-run.md).

## Common mistakes

1. **Picking a VLA when a small fine-tuned ACT would do.** VLAs are
   slow, expensive, and overkill for a single task on a single robot.
2. **Zero-shot expectations.** Out-of-the-box VLAs usually need
   fine-tuning on your specific robot and gripper. Plan a fine-tune
   stage.
3. **VLA in the inner loop.** A 5 Hz VLA is a planner, not a
   controller. Pair it with a fast lower-level policy or with MoveIt.
4. **No fallback.** The VLA returns garbage on out-of-distribution
   prompts. Always have a "safe stop" branch.
5. **Pretrained on Open X, fine-tuned on 5 demos.** Not enough data.
   You still need 50–200 demos on *your* robot.

## What's next

When the high-level policy is just "decide what to do next," a plain
LLM sometimes does the job better than a VLA — without the training
budget.

→ Next: [06-f-llms-in-the-loop.md](06-f-llms-in-the-loop.md)

← Back to: [Layer 3, AI overview](06-ai-and-foundation-models.md)
