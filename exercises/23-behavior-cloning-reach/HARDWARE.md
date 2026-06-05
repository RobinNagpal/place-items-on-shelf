# Behavior cloning on a real arm — the hardware path

This exercise runs entirely in software. Doing the *same thing* on a
real myCobot 280 Pi (or any ROS-driven arm) takes the same three
steps — record, train, deploy — but each step gains a real-world
concern that the simulator hid from you. This file walks through
each step as it would actually be wired up on the real arm, and
flags the safety bits you cannot skip.

## What stays the same

- The **algorithm**: BC is still `(state, action)` pairs into a
  small MLP, supervised loss, no reward.
- The **model**: an MLP with `state_dim` in / `action_dim` out, same
  shape as the sim version (just bigger inputs / outputs).
- The **success bar**: TCP within 3 cm of the target on 8/10 fresh
  runs.

## What changes

| Step | Software exercise | Real hardware |
|---|---|---|
| Generate demos | analytical `expert.py` | human at a gamepad / keyboard |
| State input | `(q1, q2, target_x, target_y)` | `(q1..q6, target_x, target_y, target_z)` from `/joint_states` + a `/target_pose` topic |
| Action output | `(dq1, dq2)` joint velocity | `(dq1..dq6)` joint velocity command, or a Cartesian `Twist` if you prefer |
| Step physics | Euler integrator | real motors, real friction, real safety limits |
| Record format | numpy `.npz` | `rosbag2` (records every topic on a timeline) |
| Deploy | one Python script | a ROS 2 node publishing `/arm_controller/commands` |
| Safety | none needed | required (see "Safety" below) |

## Step 1 — record the demo

### Hardware setup

- The arm, set to a **teleop-friendly mode** — for myCobot Pi that's
  usually `mc.set_free_mode(1)` (compliant) plus a velocity
  controller in `ros2_control`.
- A teleop input device. For the myCobot, the cheapest options are:
  - **Keyboard** — `teleop_twist_keyboard` from ROS, remapped onto
    joint-velocity commands.
  - **Gamepad** — `joy_node` -> `joy_teleop` -> joint commands.
  - **Lead-through** — physically grab the arm and move it while it
    is in compliant mode; record `/joint_states` only. The
    "actions" in this case are the *measured* joint velocities, not
    commanded ones. This is the easiest way to record on the
    myCobot specifically.
- A way to define **the target** for the demo. The simplest version
  is a piece of tape on the table marked with an ArUco tag (exercise
  10) — that gives you a `(x, y, z)` in base frame to publish on
  `/target_pose`.

### Recording

```bash
# Start the arm + your teleop node. In a separate shell:
ros2 bag record /joint_states /target_pose -o demo_001
```

Drive the arm to the target for ~30 seconds. Stop the bag. Repeat
for ~20 fresh target locations (move the ArUco tag between bags).

### Convert the bag to a training dataset

A small Python script reads each bag, time-syncs `/joint_states`
with `/target_pose` at 20 Hz, finite-differences the joint angles
to recover the velocity (action), and stacks every demo into one
`(states, actions)` numpy array exactly like `record_demo.py`. The
training code is then byte-identical to the sim version.

The key gotcha is **alignment**: `/joint_states` and `/target_pose`
publish on different clocks at different rates. Use
`message_filters.ApproximateTimeSynchronizer` or just resample both
streams at a fixed rate before pairing them.

## Step 2 — train the BC model

This step is **identical** to the sim version (`train_bc.py`). You
can train on a laptop. The model is still ~10 k parameters.

The realistic numbers shift a bit:

- 6-DoF state and action -> 12-dim total instead of 6-dim.
- 60 s per demo at 20 Hz = 1200 samples, same as sim.
- 20 demos -> 24 000 samples, same as sim.
- Final training loss is higher (real sensor noise + human
  inconsistency vs the analytic expert).

## Step 3 — deploy the policy

Replace your teleop node with a "policy node" that:

1. Subscribes to `/joint_states` and `/target_pose`.
2. On each `/joint_states` callback, builds the same state vector
   the model was trained on.
3. Calls `model.predict(state)` -> action.
4. Publishes the action to `/arm_controller/commands` (or whatever
   the velocity-controlled command topic is on your arm).

A minimal ROS 2 node skeleton:

```python
import rclpy
import joblib
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float64MultiArray

class BcPolicyNode(Node):
    def __init__(self):
        super().__init__("bc_policy")
        self.model = joblib.load("bc_policy.joblib")
        self.target = None
        self.create_subscription(PoseStamped, "/target_pose", self.on_target, 10)
        self.create_subscription(JointState, "/joint_states", self.on_js, 10)
        self.cmd_pub = self.create_publisher(
            Float64MultiArray, "/arm_controller/commands", 10
        )

    def on_target(self, msg):
        self.target = np.array(
            [msg.pose.position.x, msg.pose.position.y, msg.pose.position.z]
        )

    def on_js(self, msg):
        if self.target is None:
            return
        q = np.array(msg.position[:6])
        state = np.concatenate([q, self.target]).reshape(1, -1)
        action = self.model.predict(state)[0]
        # SAFETY: clip per-joint velocity to a tiny fraction of the arm's max.
        action = np.clip(action, -0.2, 0.2)
        msg = Float64MultiArray()
        msg.data = action.tolist()
        self.cmd_pub.publish(msg)

def main():
    rclpy.init()
    rclpy.spin(BcPolicyNode())
```

That's the entire deployment.

## Safety — the part you cannot skip

A simulated arm cannot break anything. A real one can break itself,
break the rack, break the table, break a finger. **Three rules**
before you ever press "go" on the policy node:

### 1. Wrap every published action in a safety filter

The BC policy will sometimes predict nonsense — especially the
first time you run it on a fresh target. Always wrap the publish
call:

```python
action = clip_per_joint(action, MAX_SAFE_VELOCITY)     # cap speed
if outside_workspace(forward_kinematics(q + action * dt)):
    action = np.zeros_like(action)                     # stop instead
if estopped or joystick_deadman_released:
    action = np.zeros_like(action)
```

`MAX_SAFE_VELOCITY` should start at **10% of the arm's nominal max
velocity** and stay there until you've watched the policy behave
on 20+ random targets.

### 2. Hold-to-run "deadman" switch

The policy publishes commands **only** while you hold a button on
the gamepad. Release the button -> commands stop, arm halts. ROS
has a standard idiom for this with `joy_teleop` and the
`enable_button` field; for the myCobot Pi you can also wire a
single push button to a GPIO pin.

This is the difference between "AI controls the arm" (terrifying)
and "AI controls the arm while a human holds a button that they
can release at any moment" (acceptable).

### 3. A workspace bounding box

Before publishing any command, compute the next TCP pose
(`forward_kinematics(q + action * dt)`) and check it sits inside a
known-safe axis-aligned box around the work area. Outside the box
-> publish zeros, log a warning. This catches the BC policy
diving into the table, the wall, or itself.

## Comparing the sim run and the hardware run

- **Time to first useful policy**: sim ~10 seconds, hardware ~30
  minutes (recording 20 demos, syncing bags, training, debugging
  the deploy node).
- **Success rate at "8/10 within 3 cm"**: sim hits it easily,
  hardware sometimes needs DAgger (see IMPLEMENTATION_NOTES.md) or
  domain randomisation in sim before deploying.
- **Failure consequences**: sim run 10 fails -> a `FAIL` line.
  Hardware run 10 fails -> the arm crashes into something. That
  is why the safety wrapper above is non-negotiable.

## Where the autosampler comes in

The realistic use of BC for the HPLC autosampler isn't "reach this
target" — that's already solved by exercise 21. It's "the last
millimetre of lowering a vial into a slightly tilted slot":

1. Lead-through teleop the arm into 20 vial-drops while the rack is
   at slightly different angles. Record both `/joint_states` and
   the wrist F/T sensor reading (item 15).
2. Train BC with state = `(joint angles, target slot xyz, wrist
   force xyz)` and action = `(joint velocity)`. The force sensor
   tells the policy when it has touched the slot wall — the
   information that lets it "give and recover" instead of crashing.
3. Deploy in place of the final 5 mm descent in exercise 21. The
   policy adapts to misalignment; the rest of the pick-and-place
   stays hard-coded.

That's the realistic v2 of the autosampler — and a much more
interesting BC application than the toy 2D reach this exercise
covers, but built from exactly the same blocks.
