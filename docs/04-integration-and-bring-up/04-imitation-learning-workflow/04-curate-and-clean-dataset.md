# 04-d — Curate and Clean the Dataset

Most demos you record are good. Some are not. The bad ones teach the
policy bad habits. Curating is the unglamorous filter that separates
"training data" from "a folder of MP4s."

A clean 80-demo dataset out-performs a dirty 200-demo one. Spend
the hour.

## What you need before this step

- A recorded dataset from [step 3](03-record-demos.md).
- A way to play back episodes (LeRobot has
  `lerobot.scripts.visualize_dataset`; ALOHA has a similar tool).
- A spreadsheet or note file for tagging.

## What "curation" means

Three things, in this order:

1. **Drop bad takes.** Episodes that failed, glitched, or looked
   weird.
2. **Balance variation.** Make sure no single setup (e.g. object in
   centre, palm-down grasp) dominates the dataset.
3. **Tag for evaluation.** Mark a hold-out set the policy never sees
   during training.

## 1. Drop bad takes

For each episode, ask:

- **Did the task complete?** If not, drop.
- **Was the motion smooth?** Big stutters where the operator
  hesitated — drop.
- **Did the operator restart mid-take?** Drop.
- **Did the object disappear from the camera at any point?** Drop —
  the policy can't learn from invisible inputs.
- **Did something unrelated happen?** (Someone walked through the
  shot, the dog jumped on the table). Drop.

Realistic drop rates: **10–30%** of recordings are removed after
curation. If yours is higher, fix the recording process before
running another session.

**How to actually do it:** LeRobot stores a per-episode metadata
file. Set `is_valid: false` on bad ones; later splits / loaders
filter by it. Don't delete the files — keep them archived for
inspection.

## 2. Balance variation

Plot your dataset histogram:

- Object x-position (binned).
- Object y-position (binned).
- Object rotation.
- Object identity, if you varied it.

If 80% of demos have the object in the centre, the policy will
struggle when the object is at the edge. Either record more
edge-of-table demos, or **down-sample the over-represented bins** at
training time.

A simple discipline: aim for **≤ 2× ratio** between the most-
populated and least-populated bin of each variable.

## 3. Tag the hold-out set

Set aside **10–20%** of curated episodes as a **held-out evaluation
set**. The policy never sees these during training. You use them to
compute "validation success rate" — the honest measure of how well
the policy will generalise.

Choose hold-out episodes to **cover the variation space**, not
randomly:

- Object near each of the four corners.
- Each orientation bin.
- Each object identity.

Save the split as `train.json` and `eval.json` lists, version-
controlled with the project (not the dataset).

## Re-label for failure cases (later passes)

After the first training round ([step 6](06-evaluate-and-iterate.md)),
you'll discover specific failure modes. Re-label some held-out
episodes as **targeted regression cases** for those failures, and
record new training demos that cover them.

This is the iteration loop. Curation isn't one-shot.

## Tools and commands

For LeRobot:

```
# Visualise an episode
python -m lerobot.scripts.visualize_dataset --repo-id user/my_dataset --episode-index 5

# Re-export a curated subset
python -m lerobot.scripts.filter_dataset --repo-id user/my_dataset --keep-success-only

# Push to HF Hub when ready
huggingface-cli upload user/my_dataset_curated ./dataset
```

For ALOHA / custom: a Python script that walks episode folders,
reads `metadata.json`, and writes the filtered list. No magic.

## Version every change

A curated dataset is a *named artefact*. Tag the version when you
freeze it for training:

```
my_pick_task_v1   (200 recorded)
my_pick_task_v1c  (158 after curation — c for curated)
my_pick_task_v1c_train  (140 — train split)
my_pick_task_v1c_eval   (18 — eval split)
```

Then when you discover the v1c policy fails on left-side objects, you
record:

```
my_pick_task_v2_supplement  (50 new left-side demos)
my_pick_task_v2c            (200 = v1c + supplement, recurated)
```

…and so on. Without this naming you'll lose track of which dataset
trained which policy after the third iteration.

## Output of this step

```
Recorded episode count:          ___
Episodes dropped (bad):          ___ (___ %)
Final curated count:             ___
Train / eval split:              ___ / ___
Bin balance (worst ratio):       max:min = ___ : 1
Hold-out covers variation?:      yes (each bin has ≥ 1 episode) / no
Dataset version tag:             ___
Storage location (path / HF id): ___
Date frozen:                     ___
```

## Common mistakes

1. **Skipping curation.** Bad demos in → bad policy out.
2. **Random hold-out split.** Random isn't the same as covering the
   variation space. Stratify.
3. **Deleting bad takes.** Archive them — sometimes a "bad" take is
   actually useful as a failure example.
4. **No version on the dataset.** Two months later, nobody knows
   which dataset trained the policy.
5. **Curating once and never again.** New failure modes need new
   curated subsets. Plan to re-curate every iteration.
6. **Pushing private data to a public HF dataset.** Datasets often
   include operator faces and surroundings. Audit before publishing.

## What's next

You have a clean, versioned dataset. Time to pick a policy
architecture and fine-tune.

→ Next: [05-pick-and-fine-tune-policy.md](05-pick-and-fine-tune-policy.md)
