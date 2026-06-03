# 06-h — Where the Models Run

The practical question: "this model is 13 billion parameters; how do
I run it on a robot?"

This file is about the **compute placement** of the AI you picked in
[step 1](01-open-vocab-perception.md)..[step 7](07-datasets-and-pretraining.md).
Hardware constraints often force the model choice, not the other way
around.

## Common use cases

- **Edge-only deployment** — robot is offline or in a regulated
  environment.
- **Edge + workstation in the cell** — small models on the robot,
  large model on a workstation on the same LAN.
- **Edge + cloud** — small models on the robot, frontier models in
  the cloud for outer-loop planning.
- **Fleet** — many robots share one heavy model serving from a single
  GPU box.

## Frameworks / libraries / methods

### Compute tiers — what fits where

| Compute | Typical models that fit |
|---------|------------------------|
| **Jetson Orin Nano (8 GB)** | YOLO, MobileSAM, small detection nets, Llama 3 8B INT4. |
| **Jetson Orin NX / AGX (16–64 GB)** | SAM 2 base, Grounding DINO, Octo, OpenVLA INT8, Pi-0 small. |
| **Desktop GPU (RTX 4080 / 4090, A6000)** | Most VLAs at full precision, SAM 2 large, Llama 3 70B INT4. |
| **Workstation (single H100 / A100)** | Frontier VLAs at FP16. |
| **Multi-GPU rack / cloud** | Pi-0 at scale, RT-2-size models, full-precision frontier LLMs. |

### Quantisation / inference runtimes

You don't have to run at full precision.

- **TensorRT / TensorRT-LLM (NVIDIA)** — optimised inference on
  NVIDIA hardware. Often 2–5× faster than vanilla PyTorch.
- **llama.cpp, vLLM, ExLlamaV2, MLC-LLM** — LLM inference servers
  with INT8 / INT4 / Q4_K_M quantisation. vLLM is the production
  default in 2026.
- **ONNX Runtime** — cross-framework inference; pairs with TensorRT
  on NVIDIA, CoreML on Apple, DirectML on Windows.
- **Hugging Face `bitsandbytes`** — 4-bit / 8-bit quantisation for
  PyTorch models.
- **torch.compile** — vanilla speedup for PyTorch models on most
  recent versions.

### Edge accelerators (non-NVIDIA)

- **Hailo-8, Hailo-15** — efficient INT8 vision accelerators.
- **Google Coral (Edge TPU)** — older, smaller models.
- **Intel Movidius / OpenVINO** — vision on Intel hardware.
- **Apple Silicon (M-series)** — CoreML for vision; good for
  prototyping.

### Network shapes

- **All-on-robot** — Jetson handles perception, planning, motion.
  No external dependency. Best reliability, smallest models.
- **Edge + workstation in the cell** — Jetson on the robot,
  workstation on a local switch for heavy inference. ~5–10 ms
  Ethernet latency. Common in real cells.
- **Edge + cloud** — Jetson on the robot; frontier model in the
  cloud. Adds 50–500 ms; usable only for outer-loop planning.

## How to pick

1. **Hard real-time, fixed cycle time?** → All-on-robot. Smaller,
   quantised models only.
2. **Need a 7B+ VLA but the robot has only a Jetson?** → Workstation
   in the cell, robot streams video over Ethernet.
3. **Want a frontier LLM as the planner?** → Cloud API for the LLM
   only (outer loop), edge for the inner loop.
4. **Multi-robot fleet?** → Cloud-hosted heavy model serving all
   robots; each robot has just a Jetson for fast skills.

## A common split that works

- **Robot's IPC** — vendor driver, MoveIt, motion control. CPU /
  small GPU.
- **Edge box on the robot (Jetson Orin AGX)** — perception (YOLO,
  SAM, Grounding DINO), small VLAs, sensor fusion.
- **Workstation in the cell or rack (RTX 4090 / A6000)** — heavy
  policy (OpenVLA / Pi-0), training, dataset replay.
- **Cloud or on-prem server (H100)** — only when a frontier model is
  the requirement, and only in the outer planning loop.

## Common mistakes

1. **Hype-driven hardware purchase.** "We need an H100 because Pi-0."
   Maybe. Run it at INT8 on a Jetson Orin AGX first.
2. **Forgetting power and cooling.** A second GPU in the cell needs
   1 kW + airflow. Plan it into Layer 2.
3. **No latency budget.** Measure end-to-end: capture → inference →
   action. Until you have a number, optimisation is guessing.
4. **Cloud-only deployment with bad uplink.** First WAN blip kills
   the robot. Always have an on-robot fallback.
5. **Quantisation without re-evaluation.** INT8 changes accuracy.
   Re-run your eval set after quantising.

## What's next

You've decided what AI runs, what hardware it runs on, and what data
trained it. Now you test the whole stack in simulation before you
plug in the real arm.

→ Next: [07-simulation.md](../07-simulation.md)

← Back to: [Layer 3, AI overview](README.md)
