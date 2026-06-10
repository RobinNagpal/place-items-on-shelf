# Data, Logging, and Observability

When a robot fails, you have one of two situations:

1. You logged what happened — you replay, diagnose, fix.
2. You didn't — you guess, you re-create the failure live, you ship a
   placebo patch.

Pick situation 1. **Log everything, from day one.**

This file is about what to log, how to log it, and what tools to use to
look at the logs later.

## What you check, before anything else

- **What do you actually need to debug?** Joint states + commanded
  trajectories + camera frames + the orchestrator's decisions covers
  most pick-and-place issues.
- **Storage budget?** Camera frames are big. A depth-camera stream at
  30 Hz can be tens of GB an hour. Plan the disk.
- **Privacy / regulation?** Some environments (medical, EU consumer)
  restrict what you can record and how long you can keep it.
- **Live monitoring vs. post-hoc analysis?** Both useful, different
  tools.

## What to log

A minimum useful log includes:

- **Joint states and commanded trajectories.** From the arm driver.
- **End-effector pose over time.** From tf2.
- **Perception outputs.** Detections, masks, poses with timestamps.
- **Orchestrator decisions.** Which BT node fired, which branch was
  taken, why a step failed.
- **Gripper state.** Open / closed / object detected.
- **Safety state.** E-stop, light curtain, safety scanner zones.
- **Camera frames.** RGB and depth. Compressed if at all possible.
- **System metrics.** CPU, GPU, memory, network, disk on the robot
  and the IPC.

If you can rebuild the failure from the log, you logged enough. If you
can't, log more.

## The main options

### rosbag2 — the ROS 2 native log format

The default ROS 2 recorder. Subscribes to topics you choose and writes
them to disk.

- **rosbag2** — the recorder + player.
- **Default storage plugin** — SQLite3 (`.db3`). Fine for development.
- **MCAP storage plugin** — recommended for production. Smaller,
  faster, better tooling support.

**Best for:** every ROS 2 project. Run a default recording always
(safety state + decisions) and on-demand recording (camera) when
debugging a specific issue.

### MCAP — the modern binary log format

A file format from the Foxglove team. Designed for robotics: efficient
random access, supports any message type, indexed for fast playback.

- **MCAP** — the format and reference libraries (C++, Python, Go,
  Rust, TypeScript).
- **MCAP CLI** (`mcap`) — inspect and filter logs.

**Best for:** long-term storage, sharing logs across teams, replay
into multiple tools.

### Foxglove

A desktop and web visualisation tool for robot logs. Plots, 3D scene
view, image panels, plot panels, layout per-task.

- **Foxglove Studio (free, self-hosted or desktop)** — the viewer.
- **Foxglove (paid, cloud)** — team log management, dashboards, alerts.

**Best for:** day-to-day debugging on rosbags / MCAPs. The de-facto
modern replacement for rqt-style ROS GUIs.

### RViz 2

The classic ROS visualiser. 3D scene, robot model, tf trees, camera
images. Built into ROS 2.

**Best for:** live operations, motion-planning visualisation, MoveIt
integration. Often paired with Foxglove (RViz for live; Foxglove for
recorded logs).

### Prometheus + Grafana

System metrics (CPU, GPU, memory, ROS 2 node health). Cell-level
dashboards.

- **Prometheus** — pull-based metrics scrape.
- **Grafana** — dashboards on top.
- **`node_exporter`, `nvidia_smi_exporter`** — for system + GPU.

**Best for:** "is the robot healthy right now?" dashboards. Pair with
rosbag for "what happened five minutes ago."

### Application / event logs

Standard structured logging libraries for the orchestrator and any
business-logic code.

- **`rclcpp` / `rclpy` loggers** — ROS 2 native, integrates with
  rosbag.
- **`spdlog` (C++), `structlog` (Python)** — structured logs for the
  rest of your app.
- **`journald` (systemd)** — system-level logs on Linux.

**Best for:** narrative "this is what the code was thinking" logs that
complement raw telemetry.

### Cloud log sinks

For fleets.

- **Foxglove Cloud, OpenContext, Tangram Vision** — robotics-specific
  log management.
- **AWS S3 + Athena, Google Cloud Storage + BigQuery** — generic
  cheap cold storage with query capability.
- **Datadog, Grafana Cloud, Honeycomb** — generic application
  observability you already know.

**Best for:** scaling beyond one robot. Cheaper than running your own
storage; more privacy thought needed.

### Replay simulators

A specialised use of simulation: replay a real rosbag into a sim and
see what *would* have happened with a different planner / detector.

- **Rosbag → Gazebo / Isaac Sim** — for replay-based regression
  testing.

**Best for:** CI tests where you re-run last week's failure on this
week's code.

## A pragmatic logging policy

Most cells benefit from a layered policy:

1. **Always-on, small** — joint state, tf, orchestrator decisions,
   safety. ≤ 1 MB/s. Keep forever.
2. **Always-on, medium** — perception inputs/outputs at reduced rate
   (e.g. every 5th frame). Keep weeks.
3. **On-demand, large** — full camera streams. Triggered by a button,
   a Slack command, or a fault. Keep until the bug is found.
4. **Continuous metrics** — Prometheus scrape every 15 s. Keep months.

## How to pick

1. **Single ROS 2 robot, default?** → rosbag2 with MCAP plugin +
   Foxglove for viewing.
2. **Fleet of robots?** → MCAP logs uploaded to a cloud bucket, plus
   Prometheus + Grafana for live metrics.
3. **Production cell with strict compliance?** → On-prem MCAP storage
   + role-based access; redact PII at recording time.
4. **Research lab?** → rosbag → MCAP for sharing across teams.
5. **Demos only?** → rosbag2 + rqt. Don't over-build.

## Output of this file — your logging plan

```
Recorder:                rosbag2 + MCAP / SQLite3 / vendor / none
Always-on topics:        joint_state, tf, /robot_decisions, /safety, …
On-demand topics:        /camera/color, /camera/depth, /detections
Storage location:        /var/log/robot/ … on which volume?
Retention:               always-on = ___ , on-demand = ___ , metrics = ___
Viewer:                  Foxglove Studio / Foxglove Cloud / RViz 2
Metrics stack:           Prometheus + Grafana / cloud APM / none
Alerting:                Slack / PagerDuty / email / none
Trigger for full-fidelity record: button / Slack command / fault state
```

## Common mistakes

1. **Logging only when things go wrong.** By the time you know,
   it's too late.
2. **Recording at full camera rate forever.** Disk fills up;
   recording silently stops.
3. **No timestamps from the actual sensor.** "Camera timestamp" set
   to "time received" is useless for latency analysis.
4. **Closed-source viewer-only logs.** If you can only see a log in
   one paid tool, you'll regret it. Default to MCAP.
5. **No log rotation.** SSD wears out. Set up rotation, monitor disk.
6. **PII in logs.** Faces of operators, customer order numbers.
   Redact at recording time.

## What's next

You have a robot that runs, fails gracefully, and logs everything. The
last question: how does the software actually **get onto the robot**,
and stay current?

→ Next: [10-build-deploy-and-maintenance.md](10-build-deploy-and-maintenance.md)
