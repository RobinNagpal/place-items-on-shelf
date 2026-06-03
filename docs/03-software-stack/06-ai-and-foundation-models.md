# AI and Foundation Models

The boundary between "perception software" and "AI" is blurry. This
file is about the **models bigger than a single detector** — the ones
that take in vision + language + state and output either a high-level
plan or direct motor commands.

Five years ago this section didn't exist. Today it's where the most
visible robotics progress is happening. It's also where most of the
hype lives, so the goal of this file is to give you a sober map.

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

## The main categories

### Object-level zero-shot models

Models that work on classes they were never explicitly trained for.

- **CLIP / SigLIP** — text-image embedding. "Is this a mug?" without
  training a mug classifier.
- **Grounding DINO** — text → bounding box. "Find the red mug."
- **Segment Anything (SAM, SAM 2)** — promptable segmentation. Combine
  with Grounding DINO for open-vocabulary masks.
- **OWL-ViT, OWL v2** — open-vocabulary detection from Google.

**Best for:** perception pipelines that need to handle objects you
didn't pre-label. The "vision" half of an LLM-driven pick robot.

### Foundation models for grasping and manipulation

Models that predict **how** to interact with an object, not just where
it is.

- **GraspNet-1Billion, ContactGraspNet** — grasp pose prediction from
  point clouds.
- **AnyGrasp, ManiSkill, RoboNet** — research benchmarks, models
  trained on diverse manipulation data.

**Best for:** "given a novel object, find a stable grasp." Pair with
the open-vocab detectors above.

### Vision-Language-Action (VLA) models

The headline category. Take in vision + text instructions + robot
state, and output action sequences directly.

- **RT-1 (Google), RT-2 (DeepMind)** — the original "robot transformer"
  papers. Not generally released as products.
- **OpenVLA** — open-source VLA, easier to fine-tune.
- **Pi-0, Pi-0.5 (Physical Intelligence)** — commercial VLA. The
  most-discussed VLA as of late 2025–2026.
- **GR00T (NVIDIA)** — NVIDIA's humanoid-focused foundation model.
- **Octo, Manipulate-Anything, RDT** — research and open-source VLAs.

**Best for:** research, multi-task robots, "AI-included" platforms.
Not yet a fit for tight cycle-time production cells.

### Large Language Models in the loop

LLMs as **planners or task decomposers**, not as motor controllers.

- **GPT-4o, Claude, Gemini, Llama 3** etc. — translate "tidy the
  table" into a sequence of perception + motion primitives.
- **Code-as-Policies** — LLM writes Python that calls perception and
  motion APIs.
- **SayCan, Inner Monologue, ProgPrompt** — research patterns for
  grounding LLM plans in robot capabilities.

**Best for:** orchestrating a small library of robust skills the
robot already has. The LLM picks *which* skill in *what* order.

### World models and policy learning

A separate research direction: train a policy in simulation, transfer
to real.

- **Diffusion Policy** — diffusion-model action prediction. Strong
  results on contact-rich tasks.
- **Action Chunking with Transformers (ACT)** — used in ALOHA / Mobile
  ALOHA bimanual demos.
- **Dreamer, MuZero-style world models** — learn the environment
  before acting.

**Best for:** research labs with imitation-learning datasets. Hard to
deploy in production without serious infrastructure.

## Where these models actually run

A common practical question: "this model is 13 billion parameters; how
do I run it on a robot?"

- **On a Jetson Orin (~16-64 GB)** — small-to-medium VLAs (Pi-0,
  OpenVLA at low precision), most detection / segmentation models.
- **On a desktop GPU (RTX 4090, A6000)** — most VLAs and LLMs at full
  precision.
- **On a remote server (cloud A100 / H100)** — frontier models, with
  the robot calling them over the network.
- **Quantised (INT8, INT4) and runtime-optimised (TensorRT-LLM,
  llama.cpp, vLLM)** — to fit bigger models on smaller hardware.

The split usually looks like: **fast perception on the edge box (Jetson),
slow planning on the cloud or a local desktop, motion primitives back
on the robot's IPC.**

## How to pick

1. **Tight loop, fixed object set?** → Skip this layer. Use Layer 5.
2. **Need to generalise to unseen objects?** → Start with Grounding
   DINO + SAM 2 for perception. Skip VLAs until you've exhausted
   classical methods.
3. **Long-horizon natural-language tasks?** → LLM-as-planner + a
   library of robust skills.
4. **Research, willing to invest in data?** → OpenVLA + your own
   teleoperation dataset.
5. **"AI-included" platform with budget?** → Pi-0.x via Physical
   Intelligence partnerships, or one of the bundled industrial
   solutions in [`../latest-robots.md`](../latest-robots.md).

## Output of this file — your AI plan

```
Generalisation needed?:    yes (which axes: objects / lighting / scenes / instructions) / no
Open-vocab perception?:    Grounding DINO + SAM 2 / OWL-ViT / none
Foundation model used?:    none / OpenVLA / Pi-0 / GR00T / proprietary
LLM in the loop?:          no / GPT-4o / Claude / local Llama / Gemini
Where it runs:             Jetson Orin / desktop GPU / cloud
Latency budget:            ___ ms perception, ___ s planning, ___ Hz control
Fine-tuning data:          none / N teleop demos / synthetic from sim
Fallback when AI fails:    classical perception / human intervention / safe stop
```

## Common mistakes

1. **Picking VLAs because they're cool.** Most "pick and place" jobs
   don't need one. Classical + a small fine-tuned detector is faster,
   cheaper, more reliable.
2. **Underestimating data needs.** A useful VLA fine-tune takes
   hundreds to thousands of demonstrations. Plan the data collection
   pipeline before the model.
3. **Cloud LLM in the inner loop.** Network jitter ruins control.
   Use the LLM only for outer-loop planning at ≥1 s cadence.
4. **No fallback.** AI fails *silently*. Always have a "safe stop"
   behaviour when the model returns garbage or the network drops.
5. **Hype-driven hardware purchase.** "We need an H100 because Pi-0."
   Maybe. Run it at INT8 on a Jetson Orin AGX first.

## What's next

You now have a model of *what* the robot will run. Before you run it
on real hardware, you test it in simulation.

→ Next: [07-simulation.md](07-simulation.md)
