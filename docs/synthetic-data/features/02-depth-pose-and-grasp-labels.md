# Feature 2 — Depth, Pose, and Grasp Labels

> **Poster wording.** "Depth at every pixel plus the position,
> orientation, and grasp points of every object. The data picking and
> assembly models need."

## What it is, in simple words

Three labels per frame, all bundled together because they answer the
same question — *where exactly is each object in 3D and how do I grab
it*:

- **Depth map.** A grayscale image the same size as the camera frame.
  Each pixel value is the distance from the camera to whatever is at
  that pixel (in metres). The simulator already knows this — it is
  literally the `z` buffer of the renderer.
- **6-DoF pose.** For every object, six numbers — `(x, y, z)` for
  position and three angles for orientation. Tells you exactly where
  the object sits in the world.
- **Grasp points.** For every object, a list of "places the gripper
  can grab it" — each one a 6-DoF pose for the gripper, plus a
  quality score. Comes from the object's CAD geometry plus the
  gripper's specs.

A finished dataset:

```
graspable_<project>/
├── images/         RGB frames
├── depth/          frame_00001.exr   (or .png, 16-bit)
├── poses/          frame_00001.json  (one entry per object, 6 numbers + class)
└── grasps/         object_<class>.json  (list of grasp poses per object class)
```

## Who will use it

The customer's **robotics engineer** or **grasp / manipulation
engineer**. They feed this data into a model that, given a new camera
frame at run-time, predicts *where to put the gripper* on each visible
object.

Job titles: *Manipulation Engineer*, *Grasp Engineer*, *Robotics
Engineer*, *Research Engineer (Manipulation)*.

## What models the customer trains with it

- **GraspNet / GraspNet-1Billion** — the standard open grasp model.
- **ContactGraspNet** — predicts grasps directly from a depth image.
- **AnyGrasp** — newer, also depth-based, often used for clutter.
- **Custom 6-DoF pose estimators** — DOPE (NVIDIA), PVNet, FoundationPose.
- **PointNet / PointNet++** — when the customer prefers point clouds
  over depth images.

## Libraries and frameworks involved

**On our side:**

- **Gazebo** with depth-camera plugin (publishes `sensor_msgs/Image`
  with `encoding=32FC1`) — the standard depth output.
- **Isaac Sim** depth sensor when noise / photo-real is needed.
- **GraspIt!** or **Isaac Sim Grasp Genie / Replicator Grasping** to
  generate grasp candidates from CAD.
- **Open3D** — turning depth maps into point clouds for sanity checks.

**On the customer's side:**

- **PyTorch3D** — common in 6-DoF pose research.
- **GraspNet API** — for training and evaluating GraspNet.
- **Open3D** — point-cloud processing.

## What we ship (the formats)

| Output | Default format |
|--------|----------------|
| Depth maps | 16-bit PNG (millimetres) or 32-bit EXR (metres) |
| 6-DoF poses | One JSON per frame: `[{class, position:[x,y,z], quaternion:[x,y,z,w]}, …]` |
| Grasp points | One JSON per object class: `[{grasp_pose, width, quality}, …]` |
| Point clouds (optional) | `.pcd` or `.ply` |
| Bundled | HDF5 with all four arrays per frame |

## How we generate it (the methods)

- **Procedural scenes** — randomise object positions on the table,
  random rotations, random clutter. So the depth + pose data covers
  the full operating range of the cell, not one staged layout.
- **Sensor noise modelling** — the real depth camera is **not**
  perfect. We add RealSense / Kinect noise models (speckle on glossy
  surfaces, dropouts at depth discontinuities). The model trains on
  the noise; the real depth no longer surprises it.
- **Domain randomisation** — varies texture and lighting on the RGB
  side because the customer often runs an RGB-D model that uses both
  streams.

Grasp generation is a separate step. We feed each object's CAD into
a grasp sampler (GraspIt or Isaac's grasp-generation tool), filter
the results against the gripper's geometry, and save the surviving
grasps.

## Pain points this solves

- **"We have CAD but no labelled depth data."** Sim is the only
  cheap source of perfectly-labelled depth.
- **"Our pose estimator works in good light but not in production."**
  Domain randomisation + sensor noise during training closes that gap.
- **"Real grasp data is impossible to collect."** Every real grasp
  requires the arm to try and (sometimes) fail. In sim, every grasp
  is free.

## What to say in a sales conversation

- "What gripper are you using?" *Parallel-jaw, suction, multi-finger?
  The grasp-generation step is gripper-specific.*
- "Do you have CAD for the objects?" *Required. Without CAD, no
  grasps and no perfect pose.*
- "What depth camera will the robot use in production?" *Tells us
  which noise model to apply — RealSense D435 has different speckle
  than a Photoneo PhoXi.*
- "Do you want point clouds or depth images?" *Some models eat one,
  some the other. We can ship both.*

## Typical scope and delivery

- **Inputs we need:** CAD of each object, gripper specs, scene
  description, the depth camera model and its mount position.
- **What we ship:** 10 000–30 000 RGB-D frames with the labels above,
  pre-computed grasp libraries per object, and a HDF5 bundle in case
  the customer prefers a single-file dataset.
- **Typical timeline:** 3–4 weeks (longer than feature 1 because
  grasp sampling adds a step).
