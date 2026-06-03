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

## How a robot policy is *trained*

A "policy" is the function `observation → action` the robot runs. The
foundation models above are all policies. You get a policy in one of
three ways:

1. **Scripted** — a human writes it. Classical Layer-4 code. No
   training. Fast, brittle.
2. **Imitation learning (IL)** — a human shows it. You record demos,
   the policy copies them.
3. **Reinforcement learning (RL)** — the robot tries it. The policy
   improves by trial and error against a reward.

Most useful systems mix all three: scripted for safety / motion
primitives, IL for the bulk of the skill, RL for fine-tuning specific
contact-rich bits.

### Imitation learning — "copy the human"

You drive the robot through a task many times. A neural network learns
the mapping from what the camera saw to what you did.

The simplest form is **behaviour cloning (BC)**: just predict the
next action from the current observation. Modern variants add
sequence prediction and probabilistic outputs:

- **Action Chunking with Transformers (ACT)** — predicts a *chunk* of
  future actions, not one at a time. The default IL recipe in 2025.
- **Diffusion Policy** — uses a diffusion model to predict actions.
  Stronger on contact-rich tasks than ACT.
- **Behaviour Transformers, VQ-BeT, BAKU** — alternatives.

**Data you need:** **50–200 demos** for one simple task on one robot
is the rough floor. A few thousand for robust multi-task. Tens of
millions of trajectories for foundation-scale VLAs.

**How you collect demos:**

- **Teleoperation with a leader arm** — a second identical (or
  cheaper) arm you move by hand; the robot mirrors it. Most accurate
  for contact-rich tasks.
  - **ALOHA / Mobile ALOHA** — Stanford's bimanual teleop rig. The
    most-cited setup.
  - **GELLO** — open-source low-cost leader arm.
  - **SO-100 / SO-ARM100** — sub-$200 open-source arm pair, used by
    HuggingFace LeRobot.
- **SpaceMouse / 3DConnexion** — 6-DOF joystick. Cheap, works for
  Cartesian-style tasks. Not great for fine manipulation.
- **VR controllers (Meta Quest, Vision Pro)** — increasingly common
  for collecting demos in 3D space.
- **Kinaesthetic teaching** — physically grab the arm (works on
  Franka FR3, KUKA LBR iiwa, gravity-compensated cobots).
- **Replay from rosbag** — re-use logs from an already-working
  scripted controller as "demos."

**Best for:** repetitive manipulation tasks where a human can
demonstrate. Not for tasks the human couldn't do (faster than human
speed, micron-precision, etc.).

### Reinforcement learning — "learn by trying"

The robot tries an action, gets a **reward** (good / bad), updates the
policy. Repeat millions of times. Works without human demos, but needs
either a simulator that runs at thousands of steps per second or
hundreds of real-world hours.

- **Algorithms in common use:**
  - **PPO (Proximal Policy Optimization)** — the default on-policy
    algorithm. Used in most Isaac Lab / MuJoCo training.
  - **SAC (Soft Actor-Critic)** — off-policy, sample-efficient. Used
    for real-robot RL.
  - **DDPG, TD3** — older continuous-control baselines.
- **Training frameworks:**
  - **Isaac Lab (NVIDIA)** — RL workflow on top of Isaac Sim. The
    serious training stack for robotics.
  - **MuJoCo / MJX (JAX)** — fast parallel rollouts; thousands of
    envs on one GPU.
  - **Stable-Baselines3, RLlib, CleanRL** — algorithm implementations
    you plug into your own env.
  - **Gymnasium** — the standard env interface (the successor to
    OpenAI Gym).
- **Sim-to-real bridge:**
  - **Domain randomisation** — vary lighting, friction, textures, mass
    during training so the real world looks like just one more sample.
  - **System identification** — measure real-world physics and tune
    the sim to match.

**When to use RL over IL:** when the task is **hard to demonstrate**
(very precise, very fast, or the human doesn't know the right
strategy). Examples: dynamic in-hand re-grasping, balancing,
locomotion.

**When to skip RL:** if a human can teleop the task in under a minute,
just collect demos. IL converges in days; RL converges in weeks.

### Datasets and training frameworks

You rarely train a robot policy from a blank weight matrix. You start
from a **pretrained foundation model** or a **dataset** somebody else
already collected, and fine-tune on your task.

- **LeRobot (HuggingFace)** — open-source library + dataset hub for
  robot learning. Three things in one:
  1. A standard **dataset format** (HF Datasets + video) for
     teleoperation demos.
  2. Pretrained **policies** you can fine-tune: ACT, Diffusion
     Policy, VQ-BeT, Pi-0 / Pi-0.5.
  3. **Drivers and configs** for cheap arms (SO-100, Koch, Moss,
     Aloha), so you can record demos and train end-to-end on
     hardware you can actually afford.

  **Best for:** anyone starting in robot learning today without a
  research budget. The on-ramp.

- **Open X-Embodiment (RT-X)** — 1M+ trajectories across 22 robot
  embodiments, contributed by 20+ labs. The largest open robot dataset
  as of writing. Used to pretrain RT-2-X, OpenVLA, Octo.
- **DROID** — 76k+ demos collected with a standardised Franka rig.
- **BridgeData V2** — 60k+ demos from low-cost WidowX arms.
- **RoboNet, RoboMimic, ManiSkill, RoboHive** — earlier / smaller
  benchmark datasets, still useful for ablations.
- **DexMimicGen, MimicGen** — synthetic demo generation: take 10
  human demos, expand to 1000 via sim augmentation.

**A pragmatic data plan:**

1. Pick a pretrained policy that already saw lots of robots (OpenVLA,
   Pi-0, ACT trained on Open X).
2. Collect **50–200 of your own demos** on your robot with LeRobot or
   ALOHA-style teleop.
3. Fine-tune. Evaluate on a held-out scene.
4. If accuracy is short, add 50 more demos targeting the failure
   cases. Repeat.

### Teleoperation and data-collection hardware

The data pipeline is half hardware. A short list of names you'll see:

- **ALOHA, Mobile ALOHA** — bimanual leader-follower from Stanford,
  $30–40k all-in.
- **GELLO** — open-source 3D-printed leader. Pair with a UR5 / xArm.
- **SO-100 / SO-ARM100 (HuggingFace + The Robot Studio)** —
  ~$110 per arm leader-follower kit. Designed for LeRobot.
- **Koch v1.1, Moss v1** — similar cheap educational arms with
  LeRobot drivers.
- **Meta Quest 3 / Apple Vision Pro** — VR teleop, increasingly the
  serious setup for one-handed manipulation demos.

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

1. **Tight loop, fixed object set?** → Skip this layer. Scripted is
   fine.
2. **Need to generalise to unseen objects?** → Start with Grounding
   DINO + SAM 2 for perception. Skip VLAs until you've exhausted
   classical methods.
3. **Long-horizon natural-language tasks?** → LLM-as-planner + a
   library of robust skills.
4. **Want to learn a new skill from human demos?** → LeRobot + ACT or
   Diffusion Policy. 50–200 demos, fine-tune a pretrained checkpoint.
5. **Task is too hard to demonstrate (precise, fast, dynamic)?** →
   RL in Isaac Lab or MuJoCo MJX with domain randomisation.
6. **Research, willing to invest in data?** → OpenVLA + your own
   teleoperation dataset, or fine-tune Pi-0.
7. **"AI-included" platform with budget?** → Pi-0.x via Physical
   Intelligence partnerships, or one of the bundled industrial
   solutions in [`../02-hardware-selection/latest-robots.md`](../02-hardware-selection/latest-robots.md).

## Output of this file — your AI plan

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

## Common mistakes

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

You now have a model of *what* the robot will run. Before you run it
on real hardware, you test it in simulation.

→ Next: [07-simulation.md](07-simulation.md)
