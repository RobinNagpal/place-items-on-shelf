# 06-d — Reinforcement Learning

The robot tries an action, gets a **reward**, updates the policy.
Repeat millions of times. Works without human demos — but needs either
a simulator that runs at thousands of steps per second or hundreds of
real-world hours.

## Common use cases

- **Locomotion** — quadrupeds, bipeds, humanoid walking.
- **Dynamic in-hand manipulation** — re-orienting a cube, dexterous
  ball-rolling.
- **Tasks the human can't demonstrate** — sub-millimetre precision,
  faster-than-human speeds, balancing.
- **Last-mile fine-tuning** of an IL policy on its sticking points.
- **Reward-shaped exploration** when the success metric is easy to
  measure but the strategy is unknown.

You **don't** want RL when:

- A human can teleop the task in under a minute. Just collect demos.
  See [06-c](06-c-imitation-learning.md).
- You don't have a sim that matches reality well enough — bad sim,
  bad policy.

## Frameworks / libraries / methods

### Algorithms

| Algorithm | When to use |
|-----------|-------------|
| **PPO (Proximal Policy Optimization)** | The on-policy default. Most Isaac Lab / MuJoCo training. |
| **SAC (Soft Actor-Critic)** | Off-policy, sample-efficient. Common for real-robot RL. |
| **DDPG, TD3** | Older continuous-control baselines. |
| **MPO, IMPALA, V-MPO** | Distributed-training variants. |
| **DreamerV3** | Model-based; learns a world model alongside the policy. |

### Training environments / simulators

- **Isaac Lab (NVIDIA)** — RL workflow on top of Isaac Sim. The
  serious training stack for robotics. Thousands of parallel envs
  per GPU.
- **MuJoCo / MJX (JAX)** — fast parallel rollouts; thousands of envs
  on one GPU. The lightweight alternative to Isaac.
- **Gazebo / Webots** — slower per-step; better for "physics-faithful"
  rather than "fast RL."
- **PyBullet** — older but still used for cheap RL experiments.
- **Brax (Google)** — JAX-native rigid-body sim. Useful for very
  fast, very simple RL experiments.

### Algorithm libraries (plug into your env)

- **Stable-Baselines3 (SB3)** — clean PyTorch reference
  implementations of PPO, SAC, DDPG, TD3.
- **RLlib (Ray)** — distributed RL at scale.
- **CleanRL** — single-file implementations; easy to read and modify.
- **Tianshou** — modular PyTorch RL library.
- **TorchRL** — PyTorch's own RL stack.

### Standard env interface

- **Gymnasium** — the successor to OpenAI Gym. Every modern RL library
  speaks this interface.

## Sim-to-real bridge

A policy trained in sim works perfectly in sim and falls over on real
hardware. The fix:

- **Domain randomisation** — vary lighting, friction, textures, mass,
  link sizes during training so the real world looks like just one
  more sample.
- **System identification** — measure real-world physics (motor
  response, friction) and tune the sim to match.
- **Real-to-sim fine-tune** — collect a small real dataset and
  fine-tune the sim-trained policy on it.

Layer 4 walks through this end-to-end: see
[`../04-integration-and-bring-up/02-a-shared-urdf-and-frames.md`](../04-integration-and-bring-up/02-a-shared-urdf-and-frames.md)
through `02-e`.

## How to pick

1. **Locomotion, balancing, walking?** → PPO in Isaac Lab with heavy
   domain randomisation.
2. **In-hand dexterity research?** → PPO or SAC in Isaac Lab;
   consider Brax / MJX for speed.
3. **Last-mile improvement on an IL policy?** → SAC on real hardware,
   warm-started from the IL policy.
4. **Cheap exploration / education?** → Stable-Baselines3 + Gymnasium
   on PyBullet.

## Where it trains / runs

- **Training** — desktop GPU minimum (RTX 3090 / 4090); ideally a
  multi-GPU box for serious work. Cloud A100 / H100 for the heaviest
  jobs.
- **Inference (on the robot)** — even a Jetson Orin Nano can run a
  trained policy at 50–500 Hz; the cost is all in training.

## Common mistakes

1. **RL when IL would do.** If a human can teleop it, just collect
   demos. IL converges in days; RL in weeks.
2. **No domain randomisation.** Sim-trained policy looks great in
   sim, collapses on real lighting and friction.
3. **Reward hacking.** The policy exploits a flaw in your reward and
   does something useless. Test the reward function before training.
4. **Training in one fixed sim scene.** Policy overfits to the scene.
   Randomise scenes from the start.
5. **No safety wrapper on the real robot.** RL exploration on real
   hardware breaks things. Always run with torque limits and a soft
   workspace.

## What's next

A class of models eats vision + text instructions + state and outputs
actions directly — the result of training IL + RL at foundation scale.

→ Next: [06-e-vision-language-action.md](06-e-vision-language-action.md)

← Back to: [Layer 3, AI overview](06-ai-and-foundation-models.md)
