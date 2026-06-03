# Build, Deploy, and Maintenance

You've picked an OS, middleware, drivers, planner, perception, AI,
simulator, orchestrator, and observability stack. None of it matters
if **the code can't get onto the robot reliably** and **stay updated.**

This file is about that last mile: how source code becomes a running
robot, and what happens when you need to update or roll back.

## What you check, before anything else

- **How many robots will run this code?** One development arm has very
  different needs than a fleet of fifty.
- **Who deploys?** A robotics engineer typing `colcon build`? Or a
  technician who clicks "update"?
- **Internet access on the robot?** A factory robot often has none.
  A delivery robot often has 4G/5G.
- **What's the rollback story?** If a new version breaks the cell,
  how fast can you go back?
- **Who owns dependencies?** A pinned `apt` list? A container? A
  Yocto image?

## The main options

### Bare-metal builds (the simple start)

Source code on the robot, build with `colcon` / `cmake`, install with
the system package manager.

- **`colcon`** — the ROS 2 build tool. Wraps `cmake` / `ament`.
- **`rosdep`** — resolves package dependencies into `apt` packages.
- **`apt` pins / `apt-mark hold`** — keep critical packages from
  surprise updates.

**Best for:** development. Don't ship this way to more than two or
three robots.

**Avoid for:** fleets, production updates, anyone who isn't fluent in
Linux.

### Containers (Docker / Podman)

Ship your code as an image. The robot pulls a versioned tag and
restarts the container.

- **Docker** — the standard. Even on the robot.
- **Podman** — rootless alternative; some teams prefer it.
- **Compose** — `docker compose up` describes the per-robot stack
  (driver, planner, perception, …) in one file.
- **Buildx + multi-arch** — build x86 + arm64 images so the same tag
  runs on a Jetson and an Intel IPC.

**Best for:** any team with more than one robot or more than one
developer. The dependable production pattern in 2025–2026.

**Watch out for:**
- Real-time and containers — `PREEMPT_RT` kernel scheduling works,
  but you must give the right kernel capabilities to the container.
- GPU containers — install `nvidia-container-toolkit` on the Jetson /
  IPC.

### Snap / Flatpak / OSTree-based systems

System-level packaging.

- **Snap** — Canonical's packaging, used in some Ubuntu Core / IoT
  setups.
- **Ubuntu Core** — read-only base + snaps. Designed for unattended
  devices.
- **OSTree / rpm-ostree (Fedora IoT, CoreOS)** — atomic OS updates
  with rollback.

**Best for:** fleets where you'd rather update the entire OS than
patch packages.

### Yocto / custom Linux images

Build a custom Linux image for the robot. Smaller, slower to develop
on, easier to ship as a product.

**Best for:** robots you sell to customers, where you don't want
field engineers running `apt update`.

### Vendor robot OS / update channels

Cobots and industrial robots have their own update flow.

- **UR firmware over USB / pendant** — manual, infrequent.
- **FANUC / ABB / KUKA / Yaskawa controllers** — vendor-controlled
  firmware. You don't update those casually.
- **NVIDIA Jetson / JetPack** — bundles OS, drivers, CUDA, TensorRT.
  Big, periodic releases.

You usually pair the vendor firmware (rarely updated) with your own
container-based application stack (continuously updated).

## CI / CD for robots

The same idea as for any software, with robotics-specific touches.

- **GitHub Actions, GitLab CI, BuildKite, Jenkins** — generic CI for
  building images, running tests.
- **ROS 2 CI patterns** — colcon-based test jobs, `industrial_ci`
  template, `pre-commit` hooks for `clang-format`, `ament_lint`.
- **Simulation-based regression** — run a Gazebo scene as a test;
  fail if the robot drops the object.
- **Hardware-in-the-loop (HiL)** — a real arm in the CI rack, used to
  validate driver changes.

**Best practice:** every PR triggers a build + a sim run. Real-hardware
tests run on merge to a release branch, not every commit.

## Deployment patterns

### Manual pull

`docker compose pull && docker compose up -d`, run by an engineer. Fine
for 1–3 robots.

### Pull-based fleet updates

The robot polls a registry every N minutes. New tag → pull → restart.

- **Watchtower, Diun** — lightweight Docker auto-update tools.
- **Mender, Balena, Foundries.io** — purpose-built device-update
  platforms.

### Push-based fleet updates

A central controller decides "robot X gets version Y now."

- **Ansible, Salt** — generic IT push.
- **Kubernetes / k3s on the robot** — heavy but powerful. Used by
  some delivery-robot companies.

### OTA frameworks

- **Mender** — open-source OTA, image- or container-based.
- **Balena** — managed container deployments to fleets.
- **AWS IoT Greengrass, Azure IoT Edge** — cloud-managed edge fleets.
- **NVIDIA Fleet Command** — for Jetson-based fleets, ties into Isaac
  ROS.

**Best for what:**
- Mender — open-source, image-based atomic updates.
- Balena — managed container fleets, fastest to start with.
- AWS / Azure / NVIDIA Fleet Command — if you already live in that
  cloud.

## Configuration management

The code is the same across robots; the *configuration* differs (this
robot's IP, this robot's calibration, this robot's gripper). Keep
configuration **out of the image** and load it at start.

- **ROS 2 parameters** — for in-process config.
- **Mounted config volumes** — per-robot YAML.
- **Vault / SSM / sealed-secrets** — for credentials.

## Rollback

The rollback question is more important than the deploy question.

- **Image-based** — keep the previous container image; restart it.
- **OSTree / rpm-ostree** — atomic rollback to the prior commit.
- **Snapshot the calibration files** with the image. Mismatched
  calibration is a common silent rollback failure.

Aim for a **one-command rollback** you can run from a phone. If you
can't do that, you're not really rolled back; you're crossing fingers.

## How to pick

1. **One development arm?** → bare metal + colcon. Move on.
2. **A small team and 2–10 robots?** → Docker Compose + a shared
   container registry. Rolling tags per robot, manual pulls.
3. **A real fleet?** → Balena or Mender, or k3s if you have the
   appetite. Image-based atomic updates, signed.
4. **Shipping a product?** → Yocto / Ubuntu Core + atomic OS updates
   + remote logging.
5. **Production cobot in a factory?** → Vendor firmware (rarely
   touched) + containerised application stack (continuously updated)
   + PLC integration tested in vendor sim.

## Output of this file — your deploy plan

```
Build tool:               colcon / cmake / docker buildx
Container registry:       Docker Hub / GHCR / ECR / private / N/A
Deploy method:            manual / Watchtower / Balena / Mender / k3s / Ansible
OS updates:               apt+hold / Ubuntu Core / OSTree / Yocto / vendor
Configuration source:     per-robot YAML / Vault / SSM / env vars
Calibration files:        bundled with image / mounted volume / S3 + checksum
Rollback procedure:       one-command (yes/no) — documented at: ___
CI:                       GitHub Actions / GitLab / Buildkite / Jenkins
Sim-based regression:     Gazebo / Isaac Sim / none
Hardware-in-the-loop test: yes (rack location: ___ ) / no
Security updates policy:  weekly / monthly / on-CVE / ad-hoc
```

## Common mistakes

1. **No version pin.** "Latest" pulled from Docker Hub silently breaks
   when an upstream image rebuilds.
2. **No rollback.** A bad deploy strands the cell until you SSH in.
3. **Calibration outside version control.** Robot moves to wrong
   place after a redeploy.
4. **Network secrets baked into images.** Image leaks; secret leaks.
5. **Updating in the middle of the workday.** Update windows exist
   for a reason.
6. **No remote access plan.** Robot 4-hours-away has a bug; nobody
   can reach it. Plan VPN / Tailscale / vendor remote access from
   day one.

## What's next (later layer)

Layer 4 (to be written) will cover **integration, testing, and
ramp-up** — the bridge from "all pieces work" to "the cell runs
unattended for a week and we trust it." Among the topics: pilot
deployments, acceptance tests, the human side of handing a system over
to operators, and incident response patterns.

Until that lands: with everything in this layer set up, you can build,
deploy, and update the robot. That's the end of the software story for
now.

← Back to: [Layer 3 README](README.md)
