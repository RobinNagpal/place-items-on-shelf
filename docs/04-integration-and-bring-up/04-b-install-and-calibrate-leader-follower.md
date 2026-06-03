# 04-b — Install and Calibrate the Leader-Follower Rig

You bought the teleop hardware. Now you wire it up, install the
software, and make sure that when you move the leader, the follower
copies it **accurately** and **safely**.

If the joint mapping is off by a few degrees, the follower jerks at
startup. If the camera frames aren't time-synced with the joint
states, your training data is poisoned and the policy can't learn.
This file is about avoiding both.

## What you need before this step

- Teleop hardware from [04-a](04-a-pick-teleop-hardware.md) on the
  desk.
- The production arm (the follower) brought up through
  [03](03-system-integration-on-real.md).
- USB / Ethernet cables for the leader and the cameras.
- LeRobot (for SO-100, Koch, Moss) or the ALOHA stack (for ALOHA) or
  your custom mapping code.

## Step-by-step

### Step 1 — install the software

For **LeRobot** (the easiest case):

```
pip install lerobot
# clone the configs / examples
git clone https://github.com/huggingface/lerobot.git
```

For **ALOHA**:

```
git clone https://github.com/tonyzhaozh/aloha.git
cd aloha && pip install -e .
# follow the install guide for the ROS 1 / ROS 2 driver
```

For **VR rig**: install your VR runtime (Meta SDK, ARKit / RealityKit
for Vision Pro) and the ROS 2 publisher node that converts headset +
controller pose to TF and a `geometry_msgs/PoseStamped`.

### Step 2 — wire and confirm comms

- **USB / serial** for SO-100 / Koch / Moss: connect both leader and
  follower; confirm the OS sees `/dev/ttyUSB0`, `/dev/ttyUSB1`.
- **Ethernet** for ALOHA-style rigs: same subnet, ping passes.
- **Cameras**: plug into USB 3.x ports (not 2.x — bandwidth matters).

Run the LeRobot / vendor identification script:

```
python -m lerobot.scripts.find_motors_bus_port      # SO-100 / Koch
```

Note which port maps to which arm. Lock them as udev rules so the
mapping survives a reboot:

```
/etc/udev/rules.d/99-lerobot.rules
SUBSYSTEM=="tty", ATTRS{serial}=="...", SYMLINK+="leader_arm"
SUBSYSTEM=="tty", ATTRS{serial}=="...", SYMLINK+="follower_arm"
```

### Step 3 — homing and joint mapping

The most common bug at this stage: leader joint 1 is at 30° at start,
follower joint 1 is at -10°. Press "go" and the follower jerks 40°
to match.

The fix:

1. Power both arms in **passive** mode (motors off, brakes off if
   safe).
2. Move them by hand to a **shared reference pose** — usually "arms
   fully extended forward" or "T-pose".
3. Run the **homing** routine for the rig:
   ```
   python -m lerobot.scripts.calibrate --robot-type so100   # example
   ```
4. The script records joint offsets so that when leader = 0,
   follower = 0.
5. Save the offsets to `~/.cache/huggingface/lerobot/calibration/`
   (LeRobot) or your project's `calibration.yaml`.

### Step 4 — first "follow me" test (slow)

Before doing anything fancy:

1. Set follower max velocity to **25%** (LeRobot calls this
   `max_relative_target`).
2. Move the leader very slowly through a small range.
3. Confirm the follower mirrors in real time.
4. Stop. Inspect: was there a 40° jerk anywhere? If yes, your
   calibration is wrong — go back to Step 3.

Run this test for **5 minutes** before you trust the rig.

### Step 5 — camera-and-state time sync

Your training data is `(observation_t, action_t)` pairs. If the
camera frame and the joint state aren't from the same instant in
time, the policy learns the wrong correlation.

Two reasonable approaches:

- **Software timestamps** — every message includes a ROS time. The
  recorder picks the closest pair. Fine for ≤ 30 Hz.
- **Hardware sync** — most industrial cameras can be triggered;
  syncing to a master clock keeps drift under a millisecond. Overkill
  for hobby setups.

Check the synchronisation with a simple **time-of-flight test**: snap
your fingers in front of the camera *and* tap the follower's wrist
at the same moment. The camera frame and joint-state spike should
share a timestamp within a few ms.

### Step 6 — set up the recording layout

The cameras you'll use during teleop must be **the same** you'll use
at inference time. Different mount = different inputs = the policy
fails on deploy.

A typical multi-camera ALOHA layout:

- `cam_overhead` — top-down view of the workspace.
- `cam_wrist_left` and `cam_wrist_right` — bolted to the follower's
  wrists.
- `cam_side` — operator's perspective.

Save the camera names and mount poses in your project config so the
inference launch file uses the same ones.

### Step 7 — sanity-record a 30-second teleop session

Drive a small motion, record it as **one episode**, replay it
visually. Check:

- Joint trajectory smooth.
- No timestamps reset to zero mid-episode.
- Camera frames present at the expected rate.
- LeRobot's dataset viewer (`lerobot.scripts.visualize_dataset`) plays
  it back without errors.

If this episode looks good, you're ready for full recording.

## Output of this step

```
Rig vendor / stack:           LeRobot SO-100 / ALOHA / GELLO / VR / custom
Leader serial / IP:           ___
Follower serial / IP:         ___
udev rules pinned?:           yes (file: ___ ) / no
Joint homing done (date):     ___
Offset YAML path:             ___
First "follow me" test passed: yes / no
Follower max velocity cap:    ___ %
Cameras (count, names):       ___
Camera mount pose:            same as inference / different (record the diff: ___ )
Time sync method:             software / hardware
Time-of-flight check passed:  yes / no
Sanity 30-s recording opens cleanly: yes / no
```

## Common mistakes

1. **Skipping the homing step.** First "go" jerks the follower 40°,
   damages the arm or scares the operator.
2. **Different USB ports between sessions.** Today `ttyUSB0` is the
   leader; tomorrow it's the follower. Use udev rules.
3. **One camera during teleop, three at inference.** Policy fails on
   deploy because it never saw the inputs it sees in production.
4. **No time sync verification.** A 200 ms offset between camera
   and joint state is enough to make the policy random.
5. **Going to full speed before the "follow me" test passes
   reliably.** A jerk at speed can damage cables, motors, the
   operator.
6. **Recording into an unversioned directory.** Two sessions later,
   you can't tell which dataset is which. Use a clear naming
   convention with date + task.

## What's next

The rig is calibrated. The follower mirrors the leader. Time to
actually collect the demonstrations.

→ Next: [04-c-record-demos.md](04-c-record-demos.md)
