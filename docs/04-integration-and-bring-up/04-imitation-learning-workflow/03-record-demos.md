# 04-c — Record Demos

This is the step that produces the **training data**. You sit at the
rig and run the task many times. Every successful run becomes a
training example.

The biggest single mistake people make in imitation learning is
**recording too few or too varied demos**. This file gives you a
discipline that fixes that.

## What you need before this step

- A calibrated leader-follower rig from
  [step 2](02-install-and-calibrate-leader-follower.md).
- A working LeRobot or ALOHA recording setup.
- The objects you want to manipulate, on the table.
- A clear, written **task definition** — one sentence, e.g. "Pick the
  red mug from anywhere on the green mat and place it upright in the
  black bin."

If you can't write the task in one sentence, you'll record demos that
disagree on what the task even is. Fix the definition first.

## How many demos do you need?

Rough numbers, from real projects in 2024–2026:

| Task complexity | Demo count | Notes |
|-----------------|------------|-------|
| **Single object, fixed jig** | 30–50 | If you can script it, skip IL. |
| **Single object, varied pose** | 100–200 | The common case. |
| **Multiple objects, varied scene** | 300–800 | Different objects each demo. |
| **Multi-step, language-conditioned** | 1,000+ | And usually a foundation-model fine-tune. |

These are **after curation** ([step 4](04-curate-and-clean-dataset.md));
expect to record 20–30% more than your target and throw away the
bad takes.

## How long does each demo take?

For a typical pick-and-place: 5–15 seconds of motion, plus 10–15
seconds of reset and recording overhead. So **120 demos ≈ 1 hour of
actual time** if everything goes well. Reserve 2× that on first
attempts.

## Design the variation

Don't record 200 identical demos. Vary the **inputs** the policy
will face in production:

- **Object position.** Spread evenly over the table.
- **Object orientation.** Rotate it through several angles.
- **Object identity.** Even if the task is "the red mug," include
  different *exact* mugs if they vary.
- **Background clutter** (a little). Empty table vs. a few distractor
  objects.
- **Lighting** (a little). If the production cell has a window,
  include both sunny and overcast.

Don't vary **everything**. The first dataset is for the *core skill*,
not robustness. Add variation deliberately, in waves.

A simple plan for 200 demos:

| Phase | Count | What varies |
|-------|-------|-------------|
| Warm-up | 10 | Mostly the same — get into rhythm |
| Core skill | 100 | Object position grid |
| Orientation | 40 | Object rotated |
| Identity / variant | 30 | Different objects of the same class |
| Edge cases | 20 | Edge of reach, near clutter |

## The episode loop

For each episode:

1. **Reset the scene** — object back to its planned variant.
2. **Start recording.** Foot pedal or button.
3. **Drive the leader** through the task at a natural pace.
4. **Stop recording.** Same foot pedal / button.
5. **Inspect the take** — was it successful? Smooth? Any glitch?
6. **Mark it `success` or `failure`.** Most stacks support this in
   the recording tool (LeRobot's `--record-success` flag).
7. **Reset.** Go again.

A **failure-tagged** episode is sometimes useful for training (the
policy learns what *not* to do), but usually you discard them. Make
the tag now; you'll thank yourself later.

## Operator discipline

You're the data source. Your habits become the policy's habits.

- **Move at a consistent pace.** Don't sprint some episodes and crawl
  others.
- **Use a consistent grasp style.** Always palm-down? Always
  sideways? Pick one.
- **Restart if you flinch.** A demo where you almost dropped the
  object teaches the wrong thing.
- **Watch the cameras** — make sure the object is visible at every
  moment. The policy can't learn what it can't see.

If you have two operators, spend the first 10 demos comparing styles
and agreeing on a convention.

## The dataset format

Whatever recording tool you use, the artefact looks roughly like:

```
my_pick_task_dataset/
  episode_000/
    observations/
      joint_states.parquet
      images_cam_overhead.mp4
      images_cam_wrist.mp4
    actions/
      joint_targets.parquet
    metadata.json   # success/fail, duration, operator id
  episode_001/
    …
  dataset_info.yaml
```

LeRobot specifically uses the **HuggingFace Datasets** format + MP4
video, indexed and chunked for fast random access.

Save the dataset path **in version control adjacent metadata** (not
the dataset itself — too big). Track the dataset by **content hash**
or a `git-lfs` pointer, not the raw files.

## A typical LeRobot recording command

```
python -m lerobot.scripts.control_robot record \
  --robot.type=so100 \
  --control.type=teleoperate \
  --control.fps=30 \
  --control.repo_id=username/my_pick_task \
  --control.num_episodes=200 \
  --control.episode_time_s=20 \
  --control.reset_time_s=10
```

This drives the leader-follower, records video + joint state at 30 Hz,
and tags each episode with success / failure prompts.

## When to stop recording

Watch your **failure-mode distribution** during recording:

- Object position at edge of reach: 80% success → record more edge
  cases.
- Object on the right side: 30% success → record more right-side
  demos.
- Even success across all variations → you're done with this round.

You'll record another round after the first training pass anyway
(see [step 6](06-evaluate-and-iterate.md)). Don't aim for perfection
in round one.

## Output of this step

```
Task one-sentence definition:    ___
Dataset name / repo ID:          ___
Episodes recorded:               ___
Success-tagged:                  ___
Failure-tagged:                  ___
Variations covered:              positions: ___ , orientations: ___ , objects: ___
Cameras per episode:             ___
FPS:                             ___ Hz
Storage path / size:             ___ GB
Operator(s):                     ___
Date(s) recorded:                ___
```

## Common mistakes

1. **Recording the same demo 200 times.** Looks fine in training,
   fails the moment the object moves an inch.
2. **No success / failure tag.** Bad episodes pollute training. Tag
   live.
3. **Different camera mounting between sessions.** Day-one cam at the
   left; day-two cam at the right. Half your data is wrong.
4. **Inconsistent pace.** Some demos at 1 m/s, some at 0.1 m/s.
   The policy struggles to learn either.
5. **Recording with the object out of frame.** Policy literally can't
   learn what it can't see.
6. **Storage filling up.** 100 demos × 3 cameras at 30 Hz adds up
   fast. Make sure the recording disk has 50+ GB free.

## What's next

You have a dataset. Half of it is gold; the other 20–30% is junk.
Time to clean it.

→ Next: [04-curate-and-clean-dataset.md](04-curate-and-clean-dataset.md)
