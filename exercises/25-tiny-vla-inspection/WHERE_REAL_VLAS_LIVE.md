# Where the real VLAs live

This file points to the actual VLA checkpoints if you want to swap
the tiny stand-in for a real model. None of the models below run on
a laptop CPU at a useful speed — plan for at least a 16 GB GPU.

## The three to know

| Model | Org | Year | Params | Backbone | Weights public? |
|---|---|---|---|---|---|
| **RT-2** | Google DeepMind | 2023 | 12B / 55B (two sizes) | PaLI-X / PaLM-E | No — research only |
| **OpenVLA** | Stanford + Google + others | 2024 | 7B | SigLIP + Llama-2-7B | **Yes** — Apache 2.0, on Hugging Face |
| **π0 (pi_0)** | Physical Intelligence | 2024 | ~3.3B | SigLIP-So400m + Gemma-2.6B | **Yes** — released Q4 2024 |

If you want to run something today, **OpenVLA** is the answer. RT-2
weights have not been released; π0 is similarly accessible but
slightly newer.

## OpenVLA — what running it looks like

```bash
pip install transformers torch accelerate
```

```python
from transformers import AutoModelForVision2Seq, AutoProcessor
import torch
from PIL import Image

processor = AutoProcessor.from_pretrained(
    "openvla/openvla-7b", trust_remote_code=True
)
model = AutoModelForVision2Seq.from_pretrained(
    "openvla/openvla-7b",
    attn_implementation="flash_attention_2",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
).to("cuda:0")

image = Image.open("scene.png")          # the scene from our inspect_vla.py
instruction = "pick the red cube"

prompt = f"In: What action should the robot take to {instruction}?\nOut:"
inputs = processor(prompt, image).to("cuda:0", dtype=torch.bfloat16)

action = model.predict_action(
    **inputs, unnorm_key="bridge_orig", do_sample=False
)
print(action)        # np.ndarray of shape (7,)
# action[0:3] -> dx, dy, dz in metres
# action[3:6] -> droll, dpitch, dyaw in radians
# action[6]   -> gripper (0 closed, 1 open)
```

That `model.predict_action(...)` call replaces `model(image, tokens)`
in our `inspect_vla.py`. The action shape (7-DoF) and channel order
are the same as TinyVLA's.

Footprint of running this once:

- ~14 GB of weight downloads (cached after the first run).
- ~16 GB GPU memory in `bfloat16` with FlashAttention 2.
- ~1 second per inference on an A100.

## π0 (pi_0) — what running it looks like

Physical Intelligence published `openpi`, a JAX-based codebase:
[github.com/Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi).
It is heavier to set up than OpenVLA (JAX + TPU-friendly code) but
the *interface* is the same: image + instruction → action.

## Comparison to our TinyVLA

| | TinyVLA | OpenVLA | RT-2 (55B) |
|---|---|---|---|
| Parameters | ~10 k | 7 B | 55 B |
| Vision encoder | 3 conv layers | SigLIP ViT-L | PaLI-X ViT |
| Text encoder | embedding + linear | Llama-2-7B | PaLM-E |
| Action head | 2-layer MLP | 2-layer MLP | 2-layer MLP |
| Output shape | (7,) | (7,) | (7,) |
| Training data | none | Open X-Embodiment (~1M trajectories) | RT-1 + web data |
| Reasonable hardware | any CPU | 24 GB GPU | TPU pod |

The **architecture** scales 1:1 with size. The **action space** is
identical. The **interface** in our `inspect_vla.py` works for any
of them.

## What you should do with this knowledge

For the autosampler v1 cell: **don't use a VLA yet.** The Open
X-Embodiment dataset OpenVLA trained on doesn't have HPLC vials.
Pre-trained VLAs ship with biases toward kitchen / household /
warehouse tasks. Fine-tuning OpenVLA to your cell is realistic but
requires ~100 teleop demos and a few hours on a GPU — more work than
the current curriculum covers.

For the *learning* path, the right uses of a real VLA are:

1. **Replace `model(...)` in this exercise** with OpenVLA, on the
   same synthetic 3-cube scene. Confirm the channel notes still
   hold. This is the lowest-cost "I actually ran a VLA" milestone.
2. **Compare to exercise 26 (LLM-as-router).** The router pattern
   (LLM picks an object id; YOLO + MoveIt handle the rest) is far
   cheaper and more reliable for a lab cell *today* than a full VLA.
3. **Watch the field.** π0.5 / RT-3 / etc. are coming. The
   architecture in `tiny_vla.py` will keep applying.

## Further reading

- OpenVLA paper: arXiv:2406.09246 (2024). Tells you exactly how the
  7-DoF action space is normalised and the discretisation trick
  (256 bins per channel, treated as tokens).
- RT-2 paper: arXiv:2307.15818 (2023). The originator of the "treat
  actions as language tokens" idea.
- π0 (pi_0) tech report: physicalintelligence.company (2024).
- Open X-Embodiment dataset: arXiv:2310.08864 (2023). The dataset
  OpenVLA was trained on.
