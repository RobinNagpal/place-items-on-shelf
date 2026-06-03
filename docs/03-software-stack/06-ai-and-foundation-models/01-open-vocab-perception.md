# 06-a — Open-Vocabulary Perception

Detection and segmentation models that work on **classes they were
never explicitly trained for**. You prompt the model with text
("the red mug") or an image, and it returns a bounding box or mask.

This is the "vision" half of any LLM- or VLA-driven robot. It also
slots into a classical pipeline when you don't want to maintain a
fine-tuned YOLO per task.

## Common use cases

- **"Find the X"** prompts from a human or an LLM, without retraining.
- **Fast dataset labelling** — point at an image, get a mask, save it
  as a training label.
- **Zero-shot bin picking** — when the bin contains objects nobody
  pre-registered.
- **Open-set anomaly detection** — flag anything that *doesn't* match
  expected categories.

## Frameworks / libraries / methods

### CLIP / SigLIP (text-image embedding)

Maps images and text into the same vector space. "Is this a mug?" is
one dot-product away.

- **OpenAI CLIP** — the original. Many derivatives.
- **SigLIP, SigLIP-2 (Google)** — newer, more robust embeddings.
- **Used inside:** Grounding DINO's text head, OpenVLA's visual
  encoder, most zero-shot pipelines.

### Grounding DINO (text → bounding box)

Open-vocabulary detector. Type "find the red mug", get a bounding box.

- **GroundingDINO v1, v1.5** — the originals.
- **Grounding DINO 1.6** — current SOTA at the time of writing.
- **Use it via:** the official `GroundingDINO` PyTorch repo, or
  Hugging Face Transformers (`AutoModelForZeroShotObjectDetection`).

### Segment Anything (promptable segmentation)

Point or describe; SAM returns a pixel-perfect mask.

- **SAM 1** — released by Meta in 2023.
- **SAM 2** — adds video segmentation and tracking.
- **SAM-HQ, FastSAM, MobileSAM** — accuracy or speed variants.
- **Common pairing:** Grounding DINO → bounding box → SAM → mask.
  Often called "Grounded SAM."

### OWL-ViT, OWL v2 (open-vocab detection from Google)

Alternative to Grounding DINO. Slightly different prompting style;
sometimes faster.

- **Use it via:** Hugging Face Transformers.

### Florence-2, Kosmos-2 (general vision-language)

Multi-task vision-language models that do detection, captioning, OCR,
and phrase grounding in one model.

- **Best for:** when you want one model for several vision tasks.

## How to pick

1. **Just need "is this a mug?"** → CLIP / SigLIP.
2. **Need a bounding box for an arbitrary text prompt?** → Grounding
   DINO.
3. **Need pixel-perfect masks?** → Grounded SAM (Grounding DINO + SAM).
4. **Tracking a thing across video frames?** → SAM 2.
5. **Already using Hugging Face Transformers and want one model for
   multiple tasks?** → Florence-2 or Kosmos-2.

## Where it runs

- **SAM 2-base, Grounding DINO** — comfortable on a single RTX 3060 or
  a Jetson Orin AGX. ~5–15 Hz.
- **SAM 2-large at full precision** — desktop GPU.
- **CLIP / SigLIP** — small enough to run on an edge CPU; trivial on a
  Jetson.

## Common mistakes

1. **Open-vocab when fine-tuned YOLO would be 5× faster.** If your
   object set is fixed, fine-tune. Open-vocab is for when the set
   isn't.
2. **No threshold tuning.** Default confidence cutoffs are
   conservative. Tune on your scenes.
3. **Forgetting depth.** Open-vocab gives you a 2D box or mask. You
   still need a depth source or known plane to turn it into a 3D pose.

## What's next

Once you've located the object, you need to grasp it.

→ Next: [02-neural-grasp-generation.md](02-neural-grasp-generation.md)

← Back to: [Layer 3, AI overview](README.md)
