# 04 — First Run

Your workspace builds. Time to actually run something and confirm the install is
healthy end-to-end.

There are two natural "first runs" you can pick from. They are independent —
start with whichever interests you more.

| Option | What runs | Why pick it first |
|--------|-----------|-------------------|
| **A. Our custom MoveIt task** (`cobot280_moveit_task`) | Three terminals: Gazebo, `move_group`, our `move_to_named_pose` node. Arm moves through `home → ready → joint goal → home`. | Smallest moving parts. Validates that the workspace + our package are wired up correctly without needing perception or MTC. |
| **B. The full pick-and-place demo** | Four terminals from [`recipes/the-four-terminals.md`](../recipes/the-four-terminals.md). Perception + MTC pick up the red cylinder. | More impressive, exercises every component. Only fully works after the three small upstream patches listed in [`concepts/04-pick-place-task.md`](../concepts/04-pick-place-task.md). |

If anything goes wrong in Option B, fall back to Option A — that isolates whether
the problem is "my install is broken" or "the MTC demo's known quirks bit me".

## Option A — three-terminal custom-task run

Every terminal needs both sources active first:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

Then in three separate terminals, launched in this order, waiting for each one's
"ready" message before starting the next:

```bash
# Terminal 1 — Gazebo, RViz, ros2_control
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py

# Terminal 2 — MoveIt action server
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal 3 — our task
ros2 launch cobot280_moveit_task move_to_named_pose.launch.py
```

What you should see:

- **Terminal 1**: Gazebo window opens. `Loaded arm_controller` prints in the log.
- **Terminal 2**: long startup log, ending with
  `[move_group]: You can start planning now!`.
- **Terminal 3**: a sequence of log lines:
  ```
  Planning to named target: home
  Plan ok, executing.
  Planning to named target: ready
  Plan ok, executing.
  Planning to explicit joint goal (6 joints)
  Plan ok, executing.
  Planning to named target: home
  Plan ok, executing.
  Sequence finished: all stages succeeded
  ```
- In Gazebo: the arm visibly moves four times.

If Terminal 3 hangs at `Planning to named target: home` for ≥10 s, the most
common culprits are listed in
[`cobot280_moveit_task/README.md → Troubleshooting`](../../cobot280_moveit_task/README.md#troubleshooting).

## Option B — four-terminal MTC pick-and-place

The full demo uses the same Terminals 1 and 2 above, plus the perception node and
the MTC task. The canonical reference is
[`recipes/the-four-terminals.md`](../recipes/the-four-terminals.md) — read it
once and use it as your operational checklist; this section is not a substitute.

Before you launch, apply the three small patches discussed in
[`concepts/04-pick-place-task.md`](../concepts/04-pick-place-task.md):

1. Add a brown table model to `pick_and_place_demo.world` so perception's
   "find horizontal plane" step succeeds.
2. Set `execute: true` in `mtc_node_params.yaml`.
3. Fix the controller-name typo: `grip_action_controller` →
   `gripper_action_controller` in the same file.

Without (2) and (3) you'll get successful planning logs but no arm movement —
not a build problem, just config.

## Headless / no-display run

If you're on a server (no display) you can still validate the build by launching
Gazebo headless (`gz sim -s …`) or skipping it entirely. For Option A, swap
Terminal 1 for `use_gazebo:=false` — the arm trajectories will be planned and
"executed" against the RViz ghost arm only. See
[`cobot280_moveit_task/README.md → Verify without Gazebo`](../../cobot280_moveit_task/README.md#verify-without-gazebo)
for the exact incantation.

## When the first run works

Congratulations — your environment is ready. From here on, every time you open a
fresh terminal you only need to:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

…and you can launch any of the demos directly.

## Where to go next

- **Want to understand what each piece does?** Read the
  [concepts](../concepts/) section in order, starting with
  [`01-gazebo.md`](../concepts/01-gazebo.md).
- **Want to dig into the math behind perception or planning?** Read the
  [deep-dives](../deep-dives/).
- **Want a single-page operational cheatsheet for the four-terminal demo?**
  [`recipes/the-four-terminals.md`](../recipes/the-four-terminals.md).
- **Want to add a new package or doc to this repo?** Read the
  [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md) at the repo root.
