# 04-e — Pick and Fine-tune the Policy

You have a clean dataset. Now you choose what kind of neural network
to train and run the training. The output is a **policy file** — a
`.pt`, `.safetensors`, or similar — that maps observations to
actions.

The big mistake at this step is **training from scratch**. You start
from a pretrained checkpoint that has already seen many robots and
many demos. Your dataset is small; the prior is doing the heavy
lifting.

## What you need before this step

- A curated, versioned dataset from
  [step 4](04-curate-and-clean-dataset.md).
- A training computer with a GPU. A single RTX 4090 (24 GB) handles
  most policies. Bigger models want an A6000 or H100. LeRobot will
  also run small policies on a Jetson Orin.
- Disk space: ~50 GB for one dataset + a few checkpoints.

## Choose the policy architecture

For a typical pick-and-place task in 2025–2026, four reasonable
choices:

| Policy | Strengths | Best for | Notes |
|--------|-----------|----------|-------|
| **ACT (Action Chunking Transformer)** | Predicts a chunk of future actions. Fast, well-tested. | Default for bimanual / leader-follower IL. | LeRobot ships this with strong defaults. |
| **Diffusion Policy** | Strong on contact-rich tasks. Multimodal action distributions. | Tasks where multiple "correct" actions exist. | Slower at inference than ACT (~10 Hz vs 30 Hz). |
| **VQ-BeT** | Newer; discretises actions then transforms them. | Tasks with sharp action transitions. | Less battle-tested than ACT / Diffusion. |
| **Foundation model fine-tune (OpenVLA, Pi-0)** | Generalisation from a huge prior. | Multi-task, language-conditioned, or "looks like prior demos." | Heavier compute; longer training. |

If you're unsure, **start with ACT**. It's the default LeRobot offers
and a strong baseline.

## Fine-tune, don't train from scratch

For ACT and Diffusion Policy, LeRobot ships pretrained checkpoints
trained on Open X-Embodiment or similar. Fine-tuning from these gets
to working in days; from scratch takes weeks of training and a
larger dataset to even match.

For VLAs (OpenVLA, Pi-0), pretrained is even more critical —
the whole point is the prior.

## A LeRobot fine-tune in one command

```
python -m lerobot.scripts.train \
  --dataset.repo_id=user/my_pick_task_v1c_train \
  --policy.type=act \
  --policy.pretrained=lerobot/act_aloha_sim_transfer_cube_human \
  --output_dir=outputs/train/act_my_task \
  --steps=80000 \
  --batch_size=8 \
  --policy.chunk_size=100 \
  --eval_freq=5000 \
  --save_freq=10000
```

What's happening:

- Load the ACT pretrained checkpoint.
- Fine-tune on your dataset.
- Run a quick eval every 5k steps to track progress.
- Save checkpoints every 10k steps.

For Diffusion Policy:

```
--policy.type=diffusion --policy.pretrained=lerobot/diffusion_pusht
```

## Choose hyperparameters with restraint

The defaults are usually fine. Touch only:

- **`steps`** — ~50k–100k is the typical range for fine-tuning. More
  isn't always better — watch the eval curve.
- **`batch_size`** — fits your GPU; 8 for a 24 GB card, 32 for an
  80 GB card.
- **`chunk_size`** (ACT) — how many future actions to predict per
  step. 50–100 is normal.
- **`learning_rate`** — leave at the default (LeRobot's is
  conservative).

Resist the urge to grid-search before you have a working baseline.

## Watch the training run

Things to monitor (TensorBoard / wandb / LeRobot's built-in
dashboard):

- **Training loss** — should drop smoothly. Plateaus are normal at
  the end; sudden spikes mean a bad batch.
- **Eval loss** — should drop and then plateau. If it climbs while
  training loss falls, you're overfitting.
- **Action-space MSE on the eval split** — a small concrete number;
  use it to compare runs.
- **Time per step** — if it's much slower than expected, something
  on the data loader is the bottleneck.

Save a **training log** with the dataset version, hyperparameters,
final loss, and runtime. Pair it with the checkpoint.

## Multi-GPU and bigger models

For VLAs or larger Diffusion Policy variants:

- **Single-node multi-GPU** — most LeRobot training scripts support
  `accelerate launch` or `torch.distributed` out of the box.
- **Mixed precision (bf16 / fp16)** — usually safe to enable; ~2×
  speedup.
- **LoRA fine-tuning** for VLAs — train a small adapter rather than
  the whole network. OpenVLA's `vla-scripts/finetune.py` supports
  this.

## Reality check the model size on the deployment box

The policy you train must run on the **inference computer**. Check
ahead of time:

- ACT (~80M params): runs at 30+ Hz on a Jetson Orin Nano.
- Diffusion Policy: ~10 Hz on a Jetson Orin Nano, 30+ Hz on a
  desktop RTX.
- OpenVLA / Pi-0 (~7B params): needs INT8/INT4 quantisation to fit
  on a Jetson Orin AGX (~64 GB); full precision wants an
  RTX 4090 / A6000.

If you train a model the deployment box can't run, you've wasted the
training run. Test inference on the target hardware **early**.

## Output of this step

```
Policy type:                ACT / Diffusion Policy / VQ-BeT / OpenVLA / Pi-0
Pretrained checkpoint:      ___
Dataset version:            ___
Training steps:              ___
Batch size:                  ___
Final training loss:         ___
Final eval loss:             ___
Action-space MSE on eval:    ___
Training time (h):           ___
Final checkpoint path:       ___
Inference target hardware:   ___ (verified runs at ___ Hz)
Quantisation used:           none / INT8 / INT4
```

## Common mistakes

1. **Training from scratch.** Always start from a pretrained
   checkpoint.
2. **Hyperparameter grid search before a baseline.** Get one run
   working first.
3. **Not validating on a held-out set.** Train-set loss looks great,
   real evaluation fails. Use the eval split from
   [step 4](04-curate-and-clean-dataset.md).
4. **Wrong inference rate.** Trained at 30 Hz, deploying at 10 Hz —
   the timing of action chunks is wrong. Match training and
   deployment rates.
5. **Saving only the final checkpoint.** If training overfits late,
   you can't recover. Save every 10k steps.
6. **No record of what trained the checkpoint.** Six months later
   nobody knows which dataset + commit produced this policy.

## What's next

The policy is trained. Time to find out if it actually works — first
in sim, then on real.

→ Next: [06-evaluate-and-iterate.md](06-evaluate-and-iterate.md)
