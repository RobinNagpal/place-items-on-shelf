# Feature 5 — Non-Camera Sensors

> **Poster wording.** "Lidar point clouds, thermal frames, ultrasonic
> returns, and force readings with realistic noise. For robots that
> rely on more than cameras."

## What it is, in simple words

Most robots have more than a camera. They have:

- **Lidar** — a spinning laser that returns a 3D point cloud.
- **Thermal camera** — a camera that sees heat instead of colour.
- **Ultrasonic** — a sonar-style distance sensor.
- **Force / torque (F/T)** — a sensor at the wrist that measures
  the force the gripper feels (think: "did I touch the part yet?").
- **IMU** — measures acceleration and rotation.

Each of these sensors has its **own** stream of data and its **own**
model on top. The simulator can fake all of them, and we ship the
result as a labelled time-series.

```
sensors_<project>/
├── lidar/         frame_00001.pcd       (point clouds, one per scan)
├── thermal/       frame_00001.png       (16-bit thermal image)
├── ultrasonic/    sweep_00001.csv       (range vs angle)
├── ft/            episode_000.parquet   (Fx Fy Fz Tx Ty Tz per ms)
└── labels/        per-stream ground truth (object class, slip event, …)
```

## Who will use it

The customer's **sensing engineer** or **perception team** for that
specific modality. Each sensor usually has a dedicated owner:

- *Lidar Perception Engineer* — point-cloud segmentation, obstacle
  detection.
- *Thermal Engineer* — defect detection in welds / electronics.
- *Robotics Engineer* — F/T-based contact detection, slip detection.
- *Manipulation Engineer* — F/T for insertion / threading.

## What models the customer trains with it

- **PointNet / PointNet++** — point-cloud classification and
  segmentation.
- **PointPillars, CenterPoint** — automotive-lidar object detection,
  also used in warehouse robots.
- **MinkowskiEngine / SparseConv** — sparse 3D networks.
- **A small 1D-CNN** or **LSTM** for F/T traces (contact / slip
  detection).
- **Thermal CNNs** — usually the same backbones as RGB, retrained on
  one-channel thermal input.

## Libraries and frameworks involved

**On our side:**

- **Gazebo** plugins: `gazebo_ros_velodyne_laser` (lidar),
  `gazebo_ros_ft_sensor` (force/torque), `gazebo_ros_range` (sonar).
- **Isaac Sim** has built-in lidar (Velodyne, Hesai, Ouster
  catalogues), thermal, and IMU sensors with realistic noise models.
- **NVIDIA DRIVE Sim** when very-high-fidelity lidar is needed
  (this is mostly an AV concern, rarely a manipulation customer).
- **Open3D, PCL** — point-cloud post-processing.

**On the customer's side:**

- **Open3D, PCL** — point clouds.
- **PyTorch3D, MinkowskiEngine** — sparse 3D learning.
- **NumPy, pandas, SciPy** — F/T signal processing.

## What we ship (the formats)

| Sensor | Default format |
|--------|----------------|
| Lidar | `.pcd` (PCL) or `.bin` (KITTI-style) per scan |
| Thermal | 16-bit PNG |
| Ultrasonic | CSV (angle, range, intensity) |
| F/T | Parquet (Fx, Fy, Fz, Tx, Ty, Tz per timestep) |
| IMU | Parquet (ax, ay, az, gx, gy, gz, qw, qx, qy, qz) |
| Bundled | MCAP rosbag or HDF5 |

ROS 2 teams usually want the MCAP rosbag because they can replay it
straight into their stack.

## How we generate it (the methods)

- **Sensor noise modelling.** This is the *main* method for this
  feature. Real lidar has range-dependent variance, mixed pixels at
  depth discontinuities, and dropouts on shiny surfaces. Real F/T
  drifts with temperature. We layer those noise models on top of the
  perfect simulated reading so the customer's model trains on
  realistic data.
- **Procedural scenes.** Object positions, environment clutter, and
  motion trajectories vary every episode.
- **Domain randomisation.** Vary sensor mount position, temperature,
  ambient lighting (matters for thermal).
- **Photo-real rendering.** Mostly irrelevant here — these sensors
  do not produce RGB images. The exception is thermal, where Isaac
  Sim's path tracer with thermal materials gives the most realistic
  output.

## Pain points this solves

- **"Our lidar model trained on real data fails on the new sensor
  mount."** Re-render the data with the new sensor pose; no real
  collection needed.
- **"We can't get enough F/T data — every demo damages the part."**
  In sim, contact failures are free; we can dump thousands of
  contact events.
- **"Thermal data is essentially impossible to collect at scale."**
  Sim is the only way to get tens of thousands of labelled thermal
  frames without weeks of fieldwork.

## What to say in a sales conversation

- "What exact sensor model are you using?" *We pick the matching
  noise model — RealSense L515, Velodyne VLP-16, Ouster OS1-64, ATI
  Mini40 F/T, etc.*
- "What does the downstream model do?" *Detection? Segmentation?
  Contact detection? Drives the label schema.*
- "How does the sensor stream into your stack?" *ROS 2 topic? raw
  PCAP? Native SDK? Decides whether we ship MCAP, .pcd, or a custom
  binary format.*
- "Are there events you want labelled in the trace?" *"Touchdown",
  "slip", "jam" — we annotate these timestamps in the F/T parquet.*

## Typical scope and delivery

- **Inputs we need:** the sensor make and model, the mount pose on
  the robot, the customer's data schema (if any), and the events /
  labels they want flagged in the trace.
- **What we ship:** 1 000–50 000 sensor episodes (size depends on
  sensor type — F/T traces are small, lidar scans are big), label
  files per stream, and an MCAP rosbag of the same data for ROS 2
  teams.
- **Typical timeline:** 2–4 weeks. Noise-model tuning is the long
  pole — we usually want one real-world recording from the customer
  to calibrate against.
