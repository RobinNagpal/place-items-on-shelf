# 04-a — Pick Teleop Hardware

You want the robot to learn a skill from human demonstrations. The
first decision is **how the human moves the robot**. That's the
teleop hardware.

Get this right and recording demos is a one-evening job. Get it wrong
and you'll never collect enough data.

## What you need before this step

- A real robot that's been brought up through
  [03](03-system-integration-on-real.md) — you can drive it from
  ROS 2 and see its joint states.
- A clear idea of the task you want it to learn (Layer 1 task spec).
- Some budget — teleop hardware ranges from a couple hundred dollars
  to tens of thousands.

## What teleop hardware actually does

Teleop hardware lets a human move the robot **the way you'd want it
to move on its own**. Every motion you make is recorded as a
training example. The neural network learns to copy it.

A good teleop rig:

- **Maps naturally to the robot's joints.** You don't think; you
  just move.
- **Is fast.** Recording a 50-demo session shouldn't take all day.
- **Doesn't get in your way.** Light enough to hold, easy to start /
  stop / discard a take.
- **Records the right channels.** Joint angles + camera frames at
  matched timestamps.

## The categories

### 1. Leader-follower arm pair (the gold standard)

A second arm — usually a cheaper copy of the production arm — is the
**leader**. You move it by hand. The production (**follower**) arm
mirrors it. The robot records both.

Best-in-class because the leader and the follower share the same
*kinematics*: anything you can do with the leader, the follower can
do.

| Rig | Approx. cost | Notes |
|-----|------|------|
| **ALOHA / Mobile ALOHA** (Stanford) | $20–40 k all-in | Bimanual setup, two follower arms (ViperX 300) + two leaders + mobile base option. The reference for serious imitation-learning research. |
| **GELLO** (Stanford) | $200–500 (parts) | 3D-printed leader compatible with UR5 / xArm / Panda. Open-source. |
| **SO-100 / SO-ARM100** (HuggingFace + The Robot Studio) | ~$110 per arm — $220/pair | Sub-$250 leader-follower. Designed for LeRobot. The cheapest serious setup. |
| **Koch v1.1, Moss v1** | ~$300–500/pair | Similar educational arms with LeRobot drivers. |
| **Vendor pair (UR5e leader + UR5e follower)** | $50–100 k+ | If money isn't a constraint. Used in industry. |

**Best for:** any project where the follower is a 6-DOF arm. If the
production arm is a UR5e, get a UR5e leader (or GELLO that mimics
one).

### 2. SpaceMouse / 6-DOF joystick

A small 3DConnexion / 3Dconnexion-style joystick that moves the
arm's **end effector** in 6-DOF Cartesian space.

| Device | Approx. cost | Notes |
|--------|--------------|-------|
| **3Dconnexion SpaceMouse Compact / Pro** | $100–350 | The classic CAD-mouse repurposed for teleop. |
| **NimbRo / Vention 6-DOF controllers** | $300–500 | Robotics-specific variants. |

**Best for:** Cartesian teleop, quick prototypes, light manipulation
tasks. Less natural than a leader arm for fine grasping.

### 3. VR controllers (Quest 3, Vision Pro)

A VR headset + controllers. The user reaches into the workspace; the
arm follows.

| Device | Approx. cost | Notes |
|--------|--------------|-------|
| **Meta Quest 3** | $500 | Increasingly the standard VR-teleop platform. |
| **Apple Vision Pro** | $3500 | Higher fidelity, used in some research labs. |
| **HTC Vive Pro / Index** | $500–1000 | Pre-VR-headset era; still works. |

**Best for:** humanoids, dual-arm setups, mobile manipulation, tasks
where you want a "first-person" feel. Becoming common in 2025–2026
for foundation-model data collection.

### 4. Kinaesthetic teaching ("grab and move")

You physically grab the arm and move it. Only works on arms that
support gravity compensation and zero-impedance modes.

| Arm | Supports it natively? |
|-----|----------------------|
| **Franka FR3** | Yes — built in |
| **KUKA LBR iiwa** | Yes — built in |
| **UR e-series with Force Mode** | Sort of — workable with care |
| **Most industrial arms** | No |
| **Cobots without torque sensors** | No |

**Best for:** Franka / iiwa users. Beautifully natural when it
works. Not an option for most cheaper arms.

### 5. Mouse / keyboard / web UI

Type joint angles or click a pose. Worst for IL data — it's slow and
unnatural. Useful only for sparse waypoint demos.

## What you also need with whatever rig you pick

Regardless of category:

- **A foot pedal or button** to mark "start recording" / "stop
  recording" / "discard this take". Hands-free start-stop is huge for
  productivity.
- **At least one camera** at the planned production camera location.
  Multiple cameras is better (~3 is typical for ALOHA-style setups —
  one overhead, one wrist, one fixed).
- **A mat or jig** to put objects on consistently between takes.
- **A computer fast enough to record** — typically 32 GB RAM and an
  NVMe SSD; video adds up fast.

## A pragmatic recommendation by budget

| Budget | What to buy |
|--------|-------------|
| Under $300 | SO-100 leader-follower pair + a USB webcam. Use LeRobot. |
| $500–1500 | GELLO + your existing UR5/xArm/Panda + a RealSense camera. |
| $5k+ | ALOHA full kit, or a VR rig (Quest 3 + custom mapping). |
| $30k+ | Production-grade leader-follower in the same arm family as the production cell. |

If you're new to imitation learning, the SO-100 + LeRobot path is by
far the lowest-friction. You can buy it tomorrow and record demos by
the weekend.

## Output of this step

```
Teleop rig type:           leader-follower / SpaceMouse / VR / kinaesthetic / web
Hardware bought:           ___ (model, count)
Cost total:                ___
Cameras during teleop:     count: ___ — placements: overhead / wrist / fixed
Foot pedal / start button: yes / no
Recording computer specs:  CPU ___ , RAM ___ , GPU ___ , disk ___
Will use LeRobot?:         yes / no
Will use ALOHA stack?:     yes / no
```

## Common mistakes

1. **A leader arm with different kinematics from the follower.**
   The arm motions you record don't map cleanly to the production
   arm. Match kinematics or pay later.
2. **One camera only, when you'll use three in production.** Your
   demos lose half the input signal vs. what you'll deploy with.
3. **No foot pedal.** Recording 100 demos takes twice as long with a
   keyboard.
4. **Wrong camera lens.** Wide-angle vs. narrow changes everything
   the policy sees. Match what you'll deploy.
5. **Recording floor / lighting that won't match production.**
   Lighting is a domain shift. Match it now.

## What's next

You have the hardware. Time to plug it in and confirm the leader
moves the follower (or the VR controller moves the arm), reliably,
with synchronised cameras.

→ Next: [04-b-install-and-calibrate-leader-follower.md](04-b-install-and-calibrate-leader-follower.md)
