# Implementation notes — 02 Read and annotate the arm's URDF

## Why a doc and not a script

The checklist item explicitly says "no code". The point of the exercise
is to **build a mental model of the arm**, not to generate the document.
A script that prints the same table would let the reader skip the part
that matters.

We still write the table down because:

1. Other exercises need to look these numbers up quickly.
2. Re-reading 800 lines of xacro every time is wasteful.
3. Putting a human summary next to the URDF makes drift visible the
   next time upstream changes a limit.

## Which URDF source we used

We use the URDF that ships with
[`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2),
specifically `mycobot_description/urdf/mycobot_280.urdf.xacro` and the
matching SRDF in `mycobot_moveit_config/config/mycobot_280/`. That
matches what the rest of this repo already references — see the
`cobot280_moveit_task` README.

There are at least three URDFs floating around for the myCobot 280:

| Source | When to use |
|---|---|
| **automaticaddison/mycobot_ros2** | what this repo uses, has a working Gazebo + MoveIt 2 setup |
| **elephantrobotics/mycobot_ros2** | the vendor's own ROS 2 port, sometimes lags behind on Jazzy |
| **elephantrobotics/mycobot_ros** | the ROS 1 original — link names differ |

If you swap sources, **the link and joint names may change**. The
*structure* (six revolute joints, base→shoulder→elbow→wrist1→wrist2→
roll) will not.

## Why the joint axes were copied, not computed

Joint axes look obvious when you look at the arm — joint 1 is clearly
vertical, joint 6 clearly rolls the gripper. But the *exact* axis
vector in the URDF (e.g. `0 0 1` vs `1 0 0`) depends on how the parent
link is oriented in its `<origin>` block. Two URDFs that produce the
same physical motion can list completely different axis vectors.

So we copy the axes verbatim from the URDF rather than guess them from
the arm's appearance. If you fork the URDF, re-read the `<axis>` tags
and update the table.

## Why we use radians not degrees in the table

The URDF is in radians. MoveIt is in radians. `joint_states` is in
radians. Translating to degrees once on paper helps human intuition,
but the source of truth must be the radian value — that is the number
the planner and the controllers actually use. The table lists both for
that reason.

## Trade-off: copying limit values vs linking to upstream

The cleanest alternative would be to not duplicate the numbers at all
and instead say "see the URDF". We did not do that because:

1. The URDF is in a different repo — readers have to clone it before
   they can answer the simplest question ("what's the limit on
   joint 3?").
2. Limits change rarely. The maintenance cost of duplicating them is
   low.

The trade-off: if upstream tightens a limit and we forget to update
`annotation.md`, the doc lies. Mitigation: pin the upstream commit hash
in this notes file when we copy values, and re-verify on each new
release.

Pinned reference (when this exercise was written):
`automaticaddison/mycobot_ros2`, branch `main`. If the numbers in
`annotation.md` drift from upstream, treat the URDF as the truth and
update the doc.

## Assumptions about the gripper

The annotation includes the parallel-jaw gripper section only as a
*conditional* tree — "if a gripper is loaded on top". The base URDF
ships without one; the gripper is a separate xacro that gets included
in the MoveIt config. If you fork without a gripper, ignore the gripper
table.

The two-finger prismatic limits in the annotation (`0..0.03 m`) are
representative for the parallel jaw in the addison fork. The
Elephant Robotics adaptive gripper has different limits and a different
joint structure — re-annotate if you swap to that gripper.

## Failure cases (in *using* the annotation)

- **MoveIt rejects a joint goal silently** — your goal probably exceeds
  the limits in the annotation. Re-check against the radian column
  (not the degree column — rounding can mislead).
- **Arm "wobbles" near a singularity in RViz** — joints 4 and 5 line
  up. This is a kinematic property of the arm, not a URDF bug. The
  annotation does not list singularities; if a later exercise needs
  them, add a separate doc.
- **Frames in RViz are not where you expect** — the URDF's `<origin>`
  blocks define the link-to-link offsets, not just the joint axes. The
  annotation focuses on joint axes; for full origin offsets, read the
  URDF directly.

## Debugging tips

- `xacro mycobot_280.urdf.xacro > mycobot_280.urdf` first — pure URDF
  is easier to read than xacro with macros.
- `check_urdf mycobot_280.urdf` from `liburdfdom-tools` prints the
  parsed tree and fails loud if the URDF is malformed. Run this before
  trusting any annotation you produced yourself.
- `urdf_to_graphiz mycobot_280.urdf` writes a PDF of the kinematic
  tree. Stick it next to `annotation.md` on the same screen while you
  fill in the tables.

## Things this exercise intentionally does *not* do

- No measurement of mass / inertia values. The annotation lists the
  total mass for sanity, but the per-link inertia tensors are not
  copied — they are noisy, vendor-tuned, and rarely useful to a human
  reader.
- No discussion of `<transmission>` or `<gazebo>` tags. Those matter
  for `ros2_control` and the Gazebo simulation plugin respectively;
  they get their own treatment when the relevant later exercises need
  them.
- No comparison with a different arm. The point is to know *this* arm
  cold.
