# AI and Foundation Models

The boundary between "perception software" and "AI" is blurry. This
layer is about the **models bigger than a single detector** — the ones
that take in vision + language + state and output either a high-level
plan or direct motor commands.

Five years ago this section didn't exist. Today it's where the most
visible robotics progress is happening — and where most of the hype
lives. The goal of this layer is to give you a sober map.

## When you actually need this

You probably do **not** need a foundation model for:

- A fixed jig and known objects.
- A repeatable factory cell with stable lighting.
- Picking one of N labelled classes you can train YOLO on.

You probably **do** want a foundation model for:

- "Generalise to objects we haven't labelled."
- "Take natural-language instructions from a human."
- "Handle long, multi-step tasks (open the box, take the part out,
  insert it, close the box)."

If you're new to robotics, **default to classical perception + MoveIt**
first. Reach for foundation models when classical perception runs out.

## How a robot policy is *trained*

A "policy" is the function `observation → action` the robot runs. You
get one in one of three ways:

1. **Scripted** — a human writes it. Classical Layer-4 code. No
   training. Fast, brittle.
2. **Imitation learning (IL)** — a human shows it. You record demos,
   the policy copies them.
3. **Reinforcement learning (RL)** — the robot tries it. The policy
   improves by trial and error against a reward.

Most useful systems mix all three: scripted for safety / motion
primitives, IL for the bulk of the skill, RL for fine-tuning specific
contact-rich bits.

## Read these in order — one file per technique

Each sub-file lists the **common use cases** and the
**frameworks / libraries / methods** you'd actually reach for.

1. **[01-open-vocab-perception.md](01-open-vocab-perception.md)** —
   CLIP, SAM, Grounding DINO, OWL-ViT. The "vision" half of any LLM-
   or VLA-driven robot.
2. **[02-neural-grasp-generation.md](02-neural-grasp-generation.md)** —
   GraspNet, ContactGraspNet, AnyGrasp. Given a novel object, where
   does the gripper go?
3. **[03-imitation-learning.md](03-imitation-learning.md)** —
   Behaviour cloning, ACT, Diffusion Policy, VQ-BeT. Plus the
   teleoperation rigs (ALOHA, GELLO, SO-100) you'll use to record
   demos.
4. **[04-reinforcement-learning.md](04-reinforcement-learning.md)** —
   PPO, SAC. Isaac Lab and MuJoCo MJX for parallel sim. Sim-to-real
   bridge with domain randomisation.
5. **[05-vision-language-action.md](05-vision-language-action.md)** —
   RT-1, RT-2, OpenVLA, Pi-0, GR00T, Octo. End-to-end policies that
   eat vision + text and emit motor commands.
6. **[06-llms-in-the-loop.md](06-llms-in-the-loop.md)** —
   GPT-4o / Claude / Gemini as task planner. Code-as-Policies,
   SayCan, Inner Monologue patterns.
7. **[07-datasets-and-pretraining.md](07-datasets-and-pretraining.md)** —
   LeRobot, Open X-Embodiment, DROID, BridgeData V2. Where pretrained
   checkpoints come from and how you fine-tune on your task.
8. **[08-where-models-run.md](08-where-models-run.md)** —
   Jetson Orin vs desktop GPU vs cloud. Quantisation. Edge / cloud
   split for VLAs.

## How to pick (the short version)

1. **Tight loop, fixed object set?** → Skip this layer. Scripted is
   fine. Go back to
   [`../05-perception-software.md`](../05-perception-software.md).
2. **Need to generalise to unseen objects?** → Start with
   [open-vocab perception](01-open-vocab-perception.md). Skip VLAs
   until you've exhausted classical methods.
3. **Long-horizon natural-language tasks?** →
   [LLM-as-planner](06-llms-in-the-loop.md) + a library of robust
   skills.
4. **Want to learn a new skill from human demos?** →
   [Imitation learning](03-imitation-learning.md): LeRobot + ACT or
   Diffusion Policy.
5. **Task is too hard to demonstrate (precise, fast, dynamic)?** →
   [Reinforcement learning](04-reinforcement-learning.md) in Isaac
   Lab or MuJoCo MJX.
6. **Research, willing to invest in data?** →
   [Vision-Language-Action](05-vision-language-action.md): OpenVLA
   or Pi-0 + your own teleoperation dataset.
7. **"AI-included" platform with budget?** → Pi-0.x via Physical
   Intelligence partnerships, or one of the bundled industrial
   solutions in
   [`../../02-hardware-selection/latest-robots.md`](../../02-hardware-selection/latest-robots.md).

## Output of this layer — your AI plan

```
Generalisation needed?:    yes (which axes: objects / lighting / scenes / instructions) / no
Open-vocab perception?:    Grounding DINO + SAM 2 / OWL-ViT / none
Learning paradigm:         scripted / imitation learning / RL / mix
Foundation model used?:    none / OpenVLA / Pi-0 / GR00T / proprietary
Policy architecture:       ACT / Diffusion Policy / VQ-BeT / VLA / custom
LLM in the loop?:          no / GPT-4o / Claude / local Llama / Gemini
Dataset source:            LeRobot / Open X-Embodiment / DROID / your own / mix
Teleop rig:                ALOHA / GELLO / SO-100 / SpaceMouse / VR / none
Training framework:        LeRobot / Isaac Lab / MuJoCo MJX / Stable-Baselines3 / none
Demos collected (count):   ___
Where it runs:             Jetson Orin / desktop GPU / cloud
Latency budget:            ___ ms perception, ___ s planning, ___ Hz control
Fine-tuning data:          none / N teleop demos / synthetic from sim
Fallback when AI fails:    classical perception / human intervention / safe stop
```

## Common mistakes (apply across all sub-techniques)

1. **Picking VLAs because they're cool.** Most "pick and place" jobs
   don't need one. Classical + a small fine-tuned detector is faster,
   cheaper, more reliable.
2. **Underestimating data needs.** A useful VLA fine-tune takes
   hundreds to thousands of demonstrations. Plan the data collection
   pipeline before the model.
3. **Training from scratch.** Always start from a pretrained
   checkpoint (Open X-Embodiment, LeRobot zoo, Pi-0). Random init
   wastes weeks.
4. **RL when IL would do.** If a human can teleop the task in a
   minute, just collect demos. IL converges in days; RL in weeks.
5. **No demo quality control.** Bad demos teach the policy to be bad.
   Throw away botched recordings; don't average over them.
6. **Sim-only training, no domain randomisation.** Policy works in
   sim, falls over on real lighting / friction. Randomise hard.
7. **Cloud LLM in the inner loop.** Network jitter ruins control.
   Use the LLM only for outer-loop planning at ≥1 s cadence.
8. **No fallback.** AI fails *silently*. Always have a "safe stop"
   behaviour when the model returns garbage or the network drops.
9. **Hype-driven hardware purchase.** "We need an H100 because Pi-0."
   Maybe. Run it at INT8 on a Jetson Orin AGX first.

## What's next

You have a model of *what* the robot will run. Before you run it on
real hardware, you test it in simulation.

→ Next: [07-simulation.md](../07-simulation.md)
