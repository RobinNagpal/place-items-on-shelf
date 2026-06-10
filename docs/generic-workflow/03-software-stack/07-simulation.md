# Simulation

A simulator is a **virtual world with physics** that pretends to be your
robot. The arm, the table, the objects, the camera — all of it modelled
inside a computer. You point your real code at the simulator, see what
happens, and only when the simulated version works do you let it touch
the real arm.

You use simulation for:

- **Development.** Iterate on perception and planning without booking
  the real lab.
- **Continuous integration.** Run tests automatically on every commit.
- **Training.** Generate synthetic data to train ML models.
- **Sales / demos.** Show the robot moving without shipping hardware.

The point of this file is to pick *which* simulator you build on.

## What you check, before anything else

- **Are you on ROS 2?** Some simulators integrate natively (Gazebo,
  Isaac Sim). Others bridge over a custom interface.
- **Do you need contact physics?** "Tap an object" is easy; "stably
  grasp a sponge" needs serious physics fidelity.
- **Do you need photorealistic rendering?** Visualising the camera
  output for sales is easy. Training a vision model on synthetic
  images needs photorealism.
- **Sim-to-real?** If you're training a policy in sim and deploying to
  a real robot, the simulator's physics + sensor models matter much
  more than for visualisation.

## The main options

### Gazebo (Ignition / "modern Gazebo")

The default ROS 2 simulator. Open source. Decent physics (DART, Bullet,
Open Dynamics Engine, NVIDIA PhysX 5 via plugins), basic rendering.

- **Gazebo Harmonic / Ionic** — current releases. "Modern Gazebo,"
  formerly called Ignition.
- **Tight ROS 2 integration** via `ros_gz_bridge` / `ros_gz_sim`.

**Best for:**
- Pick-and-place demos.
- ROS 2-native development.
- CI / regression tests of motion code.
- This repo (`robots/mycobot-280-pi/`) uses Gazebo.

**Avoid for:** photorealistic renders, large-fleet training, very
contact-rich tasks (deformables, friction-critical grasps).

### NVIDIA Isaac Sim / Isaac Lab

NVIDIA's RTX-rendered simulator built on Omniverse. Photoreal, large
scenes, GPU-accelerated physics (PhysX).

- **Isaac Sim** — the full simulator.
- **Isaac Lab** — the RL / robot-learning workflow on top.
- **Isaac ROS** — packages that bridge to ROS 2.

**Best for:**
- Synthetic data generation for vision models.
- Training reinforcement-learning policies at scale.
- Demos with photoreal cameras.
- Anything humanoid / mobile-manipulation flavoured.

**Avoid for:** quick "does my code compile" runs. Heavyweight to start
up and resource-hungry.

### MuJoCo

The physics simulator from DeepMind / Google. Excellent contact
dynamics. Used heavily in research.

- **MuJoCo** — the simulator.
- **MuJoCo Menagerie** — open repository of high-quality robot models.
- **MuJoCo XLA / MJX** — JAX-accelerated MuJoCo for parallel rollouts.

**Best for:**
- Reinforcement learning research.
- Contact-rich manipulation tasks.
- Fast parallel rollouts in policy training.

**Avoid for:** out-of-the-box ROS 2 integration (it exists but is less
mature than Gazebo / Isaac Sim) and photorealistic rendering.

### PyBullet

The Python frontend for the Bullet physics engine. Lightweight, easy
to script. Used heavily in research before MuJoCo opened up.

**Best for:**
- Quick research demos in pure Python.
- Lightweight RL training where you don't need NVIDIA's stack.

**Avoid for:** production work, modern photorealism, ROS 2-native
projects.

### Webots

Open-source simulator from Cyberbotics. Multi-robot friendly, fast to
set up. Good in education.

**Best for:** school and university courses, multi-robot demos.

**Avoid for:** projects already committed to ROS 2 / Gazebo (less
shared tooling).

### CoppeliaSim (formerly V-REP)

Older commercial-with-free-edu simulator. Wide robot library.

**Best for:** if you already have a CoppeliaSim setup. Not the place
to start a new project in 2026.

### Vendor simulators

Most arm vendors ship their own. Worth knowing about because they're
what factory engineers reach for:

- **UR PolyScope simulator / URSim** — exact-behaviour offline
  simulator for UR cobots.
- **FANUC ROBOGUIDE** — Windows-only, FANUC controller-faithful.
- **ABB RobotStudio** — Windows-only, ABB controller-faithful.
- **KUKA.Sim** — KUKA's offline planning sim.
- **Yaskawa MotoSim** — Yaskawa equivalent.

**Best for:** programming and validating production cells in the
vendor's own language before deploying. Use **alongside** Gazebo /
Isaac Sim, not instead of.

### Headless / parallel simulators

If you're training policies, you want hundreds of environments in
parallel.

- **Isaac Lab + Isaac Gym** — NVIDIA's parallel RL stack.
- **MuJoCo XLA (MJX)** — JAX-accelerated MuJoCo.
- **Brax** — JAX-native physics, integrates with MJX.
- **DM Control / Gymnasium** — wrappers around several physics engines.

**Best for:** RL training at scale.

## What "good enough" simulation looks like

For most pick-and-place projects, you need:

1. The arm URDF / xacro, rendered with collision shapes.
2. A table at the right height.
3. A few rigid object meshes.
4. A virtual camera publishing to ROS 2 at a realistic rate.
5. Optional: deformables (cloth, soft objects) — only if your task
   needs them.

If you can do (1)–(4), Gazebo is plenty. You only move up to Isaac Sim
when (5) or photorealism becomes critical.

## How to pick

1. **Default for a ROS 2 pick-and-place project?** → Gazebo Harmonic.
2. **Training a vision model from synthetic data?** → Isaac Sim, with
   domain randomisation.
3. **RL on contact-rich tasks?** → MuJoCo or Isaac Lab.
4. **Validating production code for a UR / FANUC / ABB cell?** →
   Vendor simulator first, then Gazebo for the ROS 2 perception side.
5. **Teaching robotics in a classroom?** → Gazebo or Webots.

## Output of this file — your simulation plan

```
Primary simulator:     Gazebo Harmonic / Isaac Sim / MuJoCo / PyBullet / vendor
Physics engine:        ODE / DART / Bullet / PhysX / MuJoCo
Photorealistic?:       no / yes (RTX / path-traced)
Used for:              dev / CI / data generation / RL training / demos
Robot URDF / xacro:    (path: ___ )
Sensor models:         RGB camera / depth camera / F/T sensor / none
World assets:          (table, objects, fixtures: ___ )
ROS 2 bridge:          ros_gz_bridge / Isaac ROS / custom / N/A
```

## Common mistakes

1. **Simulating only one happy-path scene.** Real lighting, real
   object placements, real failure modes. Vary them.
2. **Trusting "it worked in sim."** The sim-to-real gap is real. Plan
   for at least one round of tuning on real hardware.
3. **Skipping the vendor simulator for UR / FANUC etc.** It's the
   only place to validate vendor scripts before they touch a real
   arm.
4. **Photorealism for things that don't need it.** Renders are
   expensive. Use them only when training a model needs them.
5. **Different units in sim and real.** Always cross-check at a known
   dimension (a 100 mm cube should render exactly 100 mm).

## What's next

You can simulate and execute single motions. Real tasks aren't single
motions — they're sequences ("go above the cup, descend, close gripper,
lift, move to bin, release"). Sequencing has its own software.

→ Next: [08-task-orchestration.md](08-task-orchestration.md)
