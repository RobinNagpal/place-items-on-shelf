# Implementation notes — 02 Read and annotate the arm's URDF

## Why a doc and not a script

The checklist item says "no code". The point of the exercise is to
*build a mental model of the arm*, not to generate the document. A
script that prints the same table would let the reader skip the part
that matters.

We still write everything down because every later exercise needs to
look these numbers up quickly, and the autosampler reach check has to
land *before* anyone wires up MoveIt.

## Which URDF source we used

`automaticaddison/mycobot_ros2`, branch `main`. The repo's
`cobot280_moveit_task` already references this fork, so we stay
consistent. The Elephant Robotics official ROS 2 port uses different
link names; do not mix.

If upstream tightens a limit, the table in `annotation.md` will lie.
The mitigation is small: re-read the URDF whenever you clone a new
version, and update the table. The whole table is ~12 numbers.

## Why we copied joint axes rather than guessed

Two URDFs that produce the same physical motion can list completely
different axis vectors, because the `<axis>` is in the parent link's
frame and the parent's `<origin>` rotates that frame. Reading the
axis from the URDF directly is the only reliable approach.

## Why the reach check uses simple Euclidean distance

The arm's reach envelope is *roughly* a sphere of 280 mm radius
around the base. It is not exactly that — the envelope is dented by
joint limits and self-collision near the base — but flat
`sqrt(Δx² + Δy²)` against 280 mm is a safe *upper* check at the bench
level (z ≈ arm-base z): any point that fails the flat check is
definitely unreachable. Points that pass the flat check may still be
unreachable; for those, run MoveIt's IK in exercise 19 to confirm.

For a first-pass "does this layout even make sense?" filter, the
flat check is exactly the right tool.

## Trade-off — scaling down the rack and tray

The SDF uses 90 × 180 mm for the rack (catalogue is ~110 × 220 mm)
and 140 × 140 mm for the tray (catalogue is under 300 × 400 mm). We
took the requirements geometry and shrunk it just enough that the
far corners come inside reach. The cost: the SDF is no longer 1:1
with the catalogue products. The gain: the v1 cell physically
fits the chosen arm.

If we ever swap to a longer arm (myCobot 320, UR3e), restore the
catalogue footprints.

## Failure modes (in *using* the annotation)

- **MoveIt rejects a goal pose silently** — out of reach. Re-run the
  Δx, Δy arithmetic for that pose against 280 mm.
- **Arm reaches the pose in RViz but cannot in Gazebo** — a joint
  limit was tighter than the annotation table claims (upstream
  drift). Re-check `<limit>` tags in your local URDF.
- **TF frames not where expected** — `<axis>` is correct but `<origin>`
  rotations differ between forks. The annotation only covers axes,
  not origins; read the URDF for the rest.
