# 25 — Tiny VLA inspection (no execution)

Implements checklist item **25** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What this exercise does, in plain English

A **Vision-Language-Action (VLA)** model is a neural network that
takes a camera image and a natural-language instruction
("*pick the red cube*"), and outputs a robot action. It's the
single-network version of what the rest of this curriculum builds
out of separate pieces:

- **YOLO** turns the image into detections (exercises 03, 04).
- **MoveIt** turns a pose target into joint commands (exercise 19).
- A **VLA** does both, plus the language understanding, in **one
  forward pass.**

DeepMind's RT-2 (2023), Stanford / Google's OpenVLA (2024), and
Physical Intelligence's π0 (2024) are the famous public ones. They
are huge — OpenVLA is 7 **billion** parameters, trained on a million
real-robot trajectories from the Open X-Embodiment dataset.

This exercise does **not** try to run one of those. The checklist
asks for something more modest, and more useful as a learning step:

> *Feed a sim image + an instruction to a VLA, log the predicted
> 7-DoF action — **do not execute it.** Done when you can explain
> what each output channel means and how it maps to your arm's
> action space.*

So we build a **tiny stand-in VLA** that has the same three-block
shape as the real ones (vision encoder + text encoder + action
head), feed it a synthetic scene, print every output channel with
its name, units, and what it would do if executed. The model is
~10 000 parameters (vs. 7 000 000 000 for OpenVLA) and is
**randomly initialised** — we use it to demonstrate the **I/O
shape** of a VLA, not to make useful predictions.

```
    scene.png  +  "pick the red cube"
        │              │
        ▼              ▼
  ┌──────────┐   ┌──────────┐
  │  vision  │   │   text   │     real VLA: ViT-Large + Llama-7B
  │ encoder  │   │ encoder  │     tiny VLA: 3 conv layers + 1 embedding
  └────┬─────┘   └────┬─────┘
       │              │
       └──────┬───────┘
              ▼
       ┌────────────┐
       │ action head│           same in both: a few-layer MLP
       └─────┬──────┘
             ▼
     [dx, dy, dz, droll, dpitch, dyaw, gripper]   <-- 7-DoF action
             │
             ▼
       PRINT to terminal, WRITE to CSV
       (never sent to MoveIt — the whole point of "inspection")
```

## Quick answers (read this first)

**Why a stand-in instead of OpenVLA itself?**
OpenVLA is 7 B parameters and a ~14 GB download. Running it
locally needs a 24 GB GPU. The checklist task is *inspection*, not
*deployment* — the educational goal is to see the I/O shape and
understand each channel, which a tiny model demonstrates faithfully.
[`WHERE_REAL_VLAS_LIVE.md`](WHERE_REAL_VLAS_LIVE.md) explains where
to find the real ones when you do want to run them.

**Is the model trained?**
**No.** It is randomly initialised with a fixed seed. The numbers
it produces are not predictions you should believe — they only
illustrate the shape of a VLA's output. A real VLA was trained on
a million `(image, instruction, ground-truth action)` triples.

**What is the 7-DoF action space?**
The same one OpenVLA and most modern VLAs use:
`(dx, dy, dz, droll, dpitch, dyaw, gripper)`. Three end-effector
translation deltas in metres, three rotation deltas in radians,
and one normalised gripper-open value in [0, 1]. See
"Output channels" below for the full table.

**Why is this called 'inspection'?**
Because we never send the action to the arm. We print it. We log
it to a CSV. We compare its shape against what MoveIt would
expect. **No motors move.** That's the safe way to first
encounter a VLA — see what it would have done before trusting it
to actually do anything.

**How would I actually use a VLA on the autosampler?**
For v1, **you wouldn't.** Pre-trained VLAs don't yet know about
HPLC vials or laboratory racks. They would need fine-tuning on
your specific cell. The right path is: master the chain
(YOLO → depth → hand-eye → MoveIt) first, deploy v1 with
exercise 21, *then* if you want a VLA upgrade for one piece (e.g.
"the LLM decides which vial to pick next based on a tech's spoken
request"), use a VLA — but probably as the *router* (exercise 26)
rather than the motor controller.

## Output channels — the part the checklist asks you to explain

| # | Name | Units | Range we squash to | What it would do if executed |
|---|---|---|---|---|
| 0 | `dx` | metres | ±0.05 | translate the end-effector along base-frame X (+forward) |
| 1 | `dy` | metres | ±0.05 | translate along base-frame Y (+left) |
| 2 | `dz` | metres | ±0.05 | translate along base-frame Z (+up) |
| 3 | `droll` | radians | ±0.3 | rotate the EE about its X axis |
| 4 | `dpitch` | radians | ±0.3 | rotate about Y |
| 5 | `dyaw` | radians | ±0.3 | rotate about Z |
| 6 | `gripper` | unitless | [0, 1] | 0 = fully closed, 1 = fully open |

This is the action space OpenVLA produces ("the 7 DoF action
space" in the paper). It is in **end-effector delta** space, not
joint space — so the way you'd execute it on the myCobot is:

1. Read current end-effector pose from `tf` (base → end-effector).
2. Apply the deltas: `next_pose = current_pose * Δ(dx..dyaw)`.
3. Hand `next_pose` to MoveIt's `setPoseTarget` (exercise 19).
4. Set gripper width by mapping `gripper ∈ [0, 1]` to your
   gripper's open-distance range.
5. **Repeat at the model's control rate** (5–10 Hz for OpenVLA).

A real deployment would also clip per-channel to safe ranges and
add a workspace bounding-box check — same safety rules as the BC
deployment in [`../23-behavior-cloning-reach/HARDWARE.md`](../23-behavior-cloning-reach/HARDWARE.md).

## What is the workflow

`inspect_vla.py` is the only script you run:

```
scene.three_cube_scene()                    # synthesise a workspace
        │
        ▼
   render() -> 96x96x3 RGB                  # the camera image
        │
        ▼
   tokenize("pick the red cube")            # 12-token id sequence
        │
        ▼
   TinyVLA.forward(image, tokens)           # one network call
        │
        ▼
   action ∈ R^7  =  [dx, dy, dz, droll, dpitch, dyaw, gripper]
        │
        ▼
   print each channel + units + meaning     # the inspection
   write to output/predictions.csv
   save scene to output/scene.png
   (no execution — nothing sent to MoveIt)
```

## What the libraries are doing

- **`torch`** — defines the three blocks (vision encoder, text
  encoder, action head) and the forward pass. CPU-only is fine;
  the whole model has ~10 k parameters.
- **`numpy`** — the synthetic scene renderer (draws coloured
  rectangles on a grey background).
- **`vocab.py`** — a 35-word hand-listed vocabulary. Stand-in for
  the BPE / SentencePiece tokeniser a real VLA uses.

## Inputs and outputs

| | Format | Example |
|---|---|---|
| **Input — image** | `(96, 96, 3)` uint8 RGB | a tabletop with red / blue / green cubes |
| **Input — instruction** | English string | `"pick the red cube"` |
| **Output — action** | `(7,)` float32 | `[+0.0016, -0.0055, -0.0040, +0.0483, +0.0130, +0.0085, +0.4770]` |
| **Files written** | `output/scene.png`, `output/predictions.csv` | one row per instruction |

## Example run

```bash
# 1. install deps
pip install -r requirements.txt

# 2. run the inspection
python inspect_vla.py

# expected (numbers will differ on different torch versions):
# [inspect] building TinyVLA ...
# [inspect] model has 10,871 parameters (real OpenVLA: ~7,000,000,000)
# [inspect] scene saved to output/scene.png
#
# [inspect] instruction: 'pick the red cube'
# [inspect] action shape: (7,)  (7-DoF, same as OpenVLA)
# [inspect] channel-by-channel:
#            dx       = +0.0016   <- translate end-effector along base-frame X
#            dy       = -0.0055   <- translate end-effector along base-frame Y
#            dz       = -0.0040   <- translate end-effector along base-frame Z
#            droll    = +0.0483   <- rotate end-effector about X
#            dpitch   = +0.0130   <- rotate end-effector about Y
#            dyaw     = +0.0085   <- rotate end-effector about Z
#            gripper  = +0.4770   <- 0.0 = fully closed, 1.0 = fully open
# ...
# [inspect] NOTE: model is randomly initialised; numbers are illustrative.
# [inspect] No commands were sent to MoveIt. No motors moved. By design.
```

## How this ties into other exercises

- **Exercise 4 (YOLO live)** — the *non-VLA* way to do the perception
  half. YOLO gives detections; a VLA gives the entire action.
- **Exercise 8 (depth to 3D centroid)** — what a VLA *implicitly*
  learns (in its weights) instead of computing analytically.
- **Exercise 19 (Cartesian pose goal)** — the executor a VLA's
  output would feed in a real deployment.
- **Exercise 23 (behavior cloning)** — same family (supervised
  learning from demos). VLAs are essentially BC at huge scale with
  language conditioning bolted on.
- **Exercise 26 (LLM-as-router)** — the *useful-today* alternative to
  a VLA for getting natural language into the cell: have an LLM
  decide what to pick, hand the result to YOLO + MoveIt.

## What "Done when" means here

The checklist asks you to **explain what each output channel means
and how it maps to your arm's action space**. The script prints
exactly that — see the table in "Output channels" above for the
authoritative version. The CSV at `output/predictions.csv` records
one row per (instruction, scene) pair so you can compare predictions
across instructions side by side.

A `PASS` here is not a numerical bar — it's a comprehension bar.
After running the demo and reading this file you should be able to
answer:

- **What does channel 4 control?** → pitch of the end-effector.
- **In what units?** → radians.
- **What range is reasonable?** → ±0.3 rad per step.
- **How would you execute that on the myCobot?** → multiply current
  EE pose by the delta, hand result to `setPoseTarget`.
- **Why does the gripper channel use sigmoid?** → its target range
  is [0, 1] (closed → open), and sigmoid is the standard squashing
  function for that range.

## What this exercise is **not**

| Need | Where it is solved |
|------|--------------------|
| Run a real 7 B VLA | [`WHERE_REAL_VLAS_LIVE.md`](WHERE_REAL_VLAS_LIVE.md) — links to OpenVLA, RT-2, π0 |
| Execute the action on the arm | exercise 19 (Cartesian pose goal) — explicitly **not** done here |
| Natural-language pick selection without an arm-controlling VLA | exercise 26 (LLM-as-router) |
| Train a VLA from scratch | out of scope — requires Open X-Embodiment and ~$10k of GPU time |

## What's next

- Read [`WHERE_REAL_VLAS_LIVE.md`](WHERE_REAL_VLAS_LIVE.md) for the
  jump from "I understand the I/O" to "I want to run OpenVLA".
- Exercise 26 (LLM-as-router) for the most practical *today*
  natural-language interface for a lab cell.
