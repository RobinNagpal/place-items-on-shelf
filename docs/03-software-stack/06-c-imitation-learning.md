# 06-c — Imitation Learning

You drive the robot through a task many times. A neural network learns
the mapping from what the camera saw to what you did. The policy
becomes your demonstrator — only faster and cheaper.

## Common use cases

- **Repetitive manipulation** that's tedious to script (assembly,
  folding, sorting).
- **Contact-rich tasks** where the right strategy is "feel your way" —
  inserting, twisting, pouring.
- **Multi-step manipulations** the human can demo in 30–60 s.
- **Tasks where the spec is "watch me do it once."**
- **Last-mile fine-tuning** of a pretrained VLA on your specific
  robot.

You **don't** want IL when:

- The task is faster than the human can demonstrate.
- The task requires sub-millimetre precision the human can't repeat.
- The human doesn't know the right strategy (use RL instead — see
  [06-d](06-d-reinforcement-learning.md)).

## Frameworks / libraries / methods

### Behaviour Cloning (BC) — the baseline

Predict the next action from the current observation. The simplest
form of IL. Modern variants add sequence prediction and probabilistic
outputs.

### ACT (Action Chunking with Transformers)

Predicts a *chunk* of future actions, not one at a time. The default
IL recipe in 2025–2026.

- **Best for:** bimanual tasks, ALOHA-style setups, fine manipulation.
- **Use it via:** the original `act` repo, or the LeRobot
  implementation (`lerobot/policies/act`).

### Diffusion Policy

Uses a diffusion model to predict actions. Stronger on contact-rich
tasks than ACT.

- **Best for:** insertion, pouring, anything where the action
  distribution is multi-modal.
- **Use it via:** the `diffusion_policy` reference repo, or
  `lerobot/policies/diffusion`.

### VQ-BeT, BAKU, Behaviour Transformers

Variants that quantise the action space or use a behaviour-transformer
backbone.

- **Best for:** when ACT and Diffusion Policy aren't enough; research
  ablations.

### LeRobot (Hugging Face) — the on-ramp

The library that ties everything together: dataset format, policy
implementations, training scripts, and drivers for cheap arms. See
[06-g](06-g-datasets-and-pretraining.md) for the dataset side.

## Data you need

- **50–200 demos** for one simple task on one robot is the rough
  floor.
- **A few thousand demos** for robust multi-task.
- **Tens of millions of trajectories** for foundation-scale VLAs (see
  [06-e](06-e-vision-language-action.md)).

## How to collect demos — teleop hardware

The data pipeline is half hardware. The common rigs:

| Rig | What it is | Typical cost | Best for |
|-----|-----------|-------------|----------|
| **ALOHA / Mobile ALOHA** | Stanford bimanual leader-follower kit | $30–40k all-in | The "serious" academic setup. Bimanual contact-rich tasks. |
| **GELLO** | Open-source 3D-printed leader arm | ~$300 + follower arm | Pair with UR5 / xArm. Cheap upgrade from joystick. |
| **SO-100 / SO-ARM100** | Hugging Face + The Robot Studio kit | ~$110 per arm | LeRobot reference setup. The cheapest serious leader-follower. |
| **Koch v1.1, Moss v1** | Similar low-cost educational arms | ~$250 each | Drop-in LeRobot drivers. |
| **SpaceMouse / 3DConnexion** | 6-DOF joystick | ~$200 | Cartesian-style tasks. Not great for fine manipulation. |
| **Meta Quest 3 / Apple Vision Pro** | VR controllers | Headset price | Increasingly the serious setup for one-handed manipulation demos. |
| **Kinaesthetic teaching** | Physically grab the arm | Free | Quick demos on gravity-compensated arms (Franka FR3, KUKA LBR iiwa). |
| **Replay from rosbag** | Re-record an already-working scripted controller | Free | Bootstrapping. |

The Layer-4 workflow for actually doing this is in
[`../04-integration-and-bring-up/04-a-pick-teleop-hardware.md`](../04-integration-and-bring-up/04-a-pick-teleop-hardware.md)
through `04-f`.

## How to pick (the policy)

1. **Single-arm pick-and-place?** → ACT or Diffusion Policy.
2. **Bimanual contact-rich task?** → ACT (the recipe ALOHA uses).
3. **Insertion / pouring / multi-modal actions?** → Diffusion Policy.
4. **Want a pretrained starting point?** → fine-tune one of the
   LeRobot zoo checkpoints.

## A pragmatic data plan

1. Pick a pretrained policy that already saw many robots (OpenVLA,
   Pi-0, ACT on Open X-Embodiment).
2. Collect **50–200 of your own demos** with LeRobot or ALOHA-style
   teleop.
3. Fine-tune. Evaluate on a held-out scene.
4. If accuracy is short, add 50 more demos targeting the failure
   cases. Repeat.

## Where it runs

- **Training** — desktop GPU minimum (RTX 3090 / 4090). A
  Diffusion Policy fine-tune on 100 demos runs overnight; a full
  ACT train runs in a day.
- **Inference** — even a Jetson Orin Nano can run ACT or Diffusion
  Policy at 10–30 Hz once trained.

## Common mistakes

1. **Tiny dataset, expecting magic.** 5 demos is not enough. Start
   at 50.
2. **No demo quality control.** Bad demos teach the policy to be bad.
3. **Single-camera viewpoint when bimanual demands two.** Mirror your
   eval setup to your training setup.
4. **Not recording proprioception.** Joint positions and gripper state
   are part of the observation; many recipes need them.
5. **Forgetting to randomise camera position between demos.** Policy
   overfits to one viewpoint and falls over the moment the camera
   moves.

## What's next

When the human can't demo the task, the robot has to learn it itself.

→ Next: [06-d-reinforcement-learning.md](06-d-reinforcement-learning.md)

← Back to: [Layer 3, AI overview](06-ai-and-foundation-models.md)
