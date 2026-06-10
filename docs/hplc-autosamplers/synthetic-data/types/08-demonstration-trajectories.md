# Type 8 — Demonstration trajectories

## What it is

A long file that records **every step a "scripted expert" takes
while doing the workflow once**, from the simulator's point of
view.

Each timestep is one row with:

- **Observation** — joint positions, joint efforts, gripper
  state, end-effector pose, any relevant sensor reading
  (overhead RGB? depth? F/T?).
- **Action** — the next target the expert chose (a small joint
  delta, or a target pose for the gripper).

One file per **demonstration** (one full run of the task).
Hundreds of demonstrations per training run.

This is the standard data shape for **imitation learning** —
the model watches the expert and tries to imitate it.

## When it is useful

When the task is **easy to script but hard to specify in
closed form**, and you want the eventual real-world policy to
be more robust than the brittle script.

Concrete fits in this cell:

- The Step 5 "drip into the vial mouth" final centimetre — a
  scripted expert can hard-code "centre on the rack-slot
  coordinate," but a learned policy can tolerate a vial that
  shifted by 1 mm.
- The Step 8 "lower into slot" with slightly mis-aligned tray
  — same idea, larger workspace.
- The Step 2 swirl pattern — a clean circular wrist motion is
  easy to script but hard to describe in numbers.

## Who uses it

**Imitation-learning models.** Three popular ones:

| Model | What it is, in one line |
|---|---|
| **Behaviour Cloning MLP** | A small fully-connected network: `observation → action`. The simplest possible imitation learner; works when the task is short and the observation is low-dimensional. Already in [`exercises/23-behavior-cloning-reach/`](../../../../exercises/23-behavior-cloning-reach/). |
| **Diffusion Policy** | A diffusion-model that generates a short *action trajectory* given the current observation. Better than BC on dexterous tasks. |
| **ACT (Action Chunking Transformer)** | A small transformer that predicts a chunk of future actions at once. Robust on tasks with noisy demonstrations. |

In all three, the on-disk demonstration shape is the same.

## How to produce it in Gazebo

The "expert" is a **Python script that already knows the answer**.
You let it run the task in sim and log everything.

### 1. Write a scripted-expert function

Use the existing MoveIt setup. The expert is allowed to read
ground truth — that's the point:

```python
def expert_demo_step5(world, vial_id):
    """Pick the pipette, dip in source, dispense into vial_id."""
    pipette_pose = world.true_pose("pasteur_pipette")
    source_pose  = world.true_pose("source_beaker")
    vial_pose    = world.true_pose(vial_id)

    yield from move_above(pipette_pose,  approach_z=0.08)
    yield from move_to(pipette_pose); close_gripper()
    yield from move_above(source_pose,   approach_z=0.05)
    yield from move_to_z(source_pose.z - 0.01); squeeze_bulb()
    yield from move_above(vial_pose,     approach_z=0.04)
    yield from squeeze_bulb()
    yield from move_above(vial_pose,     approach_z=0.10)
```

`yield` so the calling loop can log every intermediate pose.

### 2. Log every timestep

Wrap the expert's loop with a per-timestep logger:

```python
trace = []
for action in expert_demo_step5(world, "vial_b1_r1"):
    obs = {
        "joint_pos":    read_joint_positions(),
        "joint_effort": read_joint_efforts(),
        "ee_pose":      read_ee_pose(),
        "gripper":      read_gripper_state(),
        # optional, if you also want vision-conditioned policies:
        "image":        read_overhead_image_hash(),
    }
    trace.append({
        "t":      now(),
        "obs":    obs,
        "action": action,
    })
    apply(action)
save_jsonl(f"demo_{demo_idx:04d}.jsonl", trace)
```

Notice that **the joint-state and joint-effort traces live
inside this file**. That is why type 7 (joint logs) was
dropped from the catalogue as a standalone — it's already here
as part of the observation.

### 3. Randomise across demonstrations

A model that watches the same trajectory 1 000 times overfits.
Vary across demos:

- Initial vial position (within the rack-slot tolerance).
- Initial gripper pose.
- Lighting (only matters if you also log images).
- Tiny random noise on the joint commands so the expert isn't
  identical run-to-run.

Standard rule of thumb: **~200 demos is the floor**, ~1 000 is
plenty for an MLP, ~5 000 starts to help Diffusion Policy.

## What you end up with

```
synthetic_<step>/
└── demos/
    ├── demo_0000.jsonl    # one row per timestep
    ├── demo_0001.jsonl
    ├── ...
    └── meta.json          # observation schema, action schema,
                          # randomisation parameters, expert version
```

For larger datasets (> 10 k demos) prefer HDF5 or Parquet over
JSONL — load time matters.

## What this data lets you do that other types don't

The other types are **per-frame snapshots**. Demonstrations are
**stories** — the whole sequence of actions that solved the
task once.

That is what an imitation-learning model needs to learn the
*policy* (the rule for what to do next), not just the
*perception* (where things are right now).

## Existing project reference

[`exercises/23-behavior-cloning-reach/`](../../../../exercises/23-behavior-cloning-reach/)
already trains a small MLP on a teleop demonstration set for a
toy reach task. The shape of its dataset is exactly the shape
above; only the expert function (and the observation schema)
change for each HPLC step.
