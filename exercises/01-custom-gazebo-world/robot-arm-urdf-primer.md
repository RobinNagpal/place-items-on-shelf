# The robot-arm files — `.urdf.xacro` explained

The SDF in this exercise loads the myCobot 280 with a single
`<include><uri>model://mycobot_280</uri></include>`. Behind that one
line is a small tree of `.urdf.xacro` files in the upstream repo
[`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2).
This primer explains what that extension means and walks through the
two files that actually describe the arm.

## What does the `.urdf.xacro` extension mean?

It's two file types in one name:

- **`.urdf`** — Unified Robot Description Format. A plain XML file
  that describes a robot as a tree of rigid bodies (`<link>`) joined
  by joints (`<joint>`). MoveIt, RViz, Gazebo, and ros2_control all
  read URDF.
- **`.xacro`** — XML Macros. A small preprocessor that adds
  *variables*, *math*, *includes*, *conditionals*, and *macros*
  (reusable blocks) on top of XML. Solves the "URDF has way too much
  repetition" problem.

A `.urdf.xacro` file is therefore a **xacro source file that becomes a
URDF after expansion**. You do not feed it to MoveIt or Gazebo
directly. You run the `xacro` command first:

```bash
xacro mycobot_280.urdf.xacro > mycobot_280.urdf
```

That writes a flat URDF — every macro call replaced with its body,
every `${...}` expression evaluated, every `<xacro:if>` resolved.
ROS launch files do this in memory; nothing is written to disk in
production.

### Why use xacro at all?

A 6-DoF arm with no xacro has six near-identical `<joint>` blocks
that differ only in axis and origin. The mass and inertia are repeated
on every link. The Gazebo material block is repeated on every link.
That's ~700 lines of XML to write and to keep in sync. With xacro you
write one macro and call it six times — and you can ship two arm
variants (with / without gripper, with / without camera) from the same
source file.

### What you'll see in any `.urdf.xacro` file

| Xacro thing | What it does |
|---|---|
| `<robot xmlns:xacro="http://www.ros.org/wiki/xacro">` | the root tag of any URDF; the `xmlns:xacro` attribute turns on xacro |
| `<xacro:property name="x" value="0.12"/>` | declare a constant |
| `<xacro:arg name="x" default="..."/>` | declare an argument passed in from outside (e.g. from a launch file) |
| `${expression}` | evaluate Python-like math, e.g. `${pi/2}`, `${0.13156}` |
| `$(arg x)` | substitute the value of an `<xacro:arg>` |
| `$(find pkg)` | substitute the absolute path of a ROS package |
| `<xacro:if value="...">` | include the inner block only if the value is truthy |
| `<xacro:include filename="..."/>` | paste in another xacro file at this point |
| `<xacro:macro name="m" params="a b">…body…</xacro:macro>` | declare a reusable block |
| `<xacro:m a="1" b="2"/>` | call a macro — the body is pasted in with `a` and `b` substituted |

## The two arm files

The myCobot 280 is split into a **composer** at the top and a **mech**
file underneath that does the real work. Other mech files (the
G-shape base, the adaptive gripper) are pulled in the same way.

### Top-level composer: `mycobot_280.urdf.xacro`

Path in the upstream repo:
[`mycobot_description/urdf/robots/mycobot_280.urdf.xacro`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_description/urdf/robots/mycobot_280.urdf.xacro).

This file is short. It does **not** declare any links or joints
itself — it picks options and stitches sub-files together.

Walkthrough:

1. **Args block** — every customisation point of the robot:

   ```xml
   <xacro:arg name="robot_name" default="mycobot_280"/>
   <xacro:arg name="add_world"  default="true"/>
   <xacro:arg name="base_link"  default="base_link"/>
   <xacro:arg name="base_type"  default="g_shape"/>
   <xacro:arg name="flange_link" default="link6_flange"/>
   <xacro:arg name="gripper_type" default="adaptive_gripper"/>
   <xacro:arg name="prefix"     default=""/>
   <xacro:arg name="use_camera" default="false"/>
   <xacro:arg name="use_gazebo" default="false"/>
   <xacro:arg name="use_gripper" default="true"/>
   ```

   A launch file can override any of these. Defaults give you a
   working arm + gripper without setting anything.

2. **Optional `world` root link** — added when `add_world=true` so
   the URDF has a fixed `world` frame above `base_link`:

   ```xml
   <xacro:if value="$(arg add_world)">
     <link name="world"/>
     <joint name="$(arg prefix)virtual_joint" type="fixed">
       <parent link="world"/>
       <child  link="$(arg prefix)$(arg base_link)"/>
     </joint>
   </xacro:if>
   ```

3. **Pick a base** — only the `g_shape` base is implemented; the
   xacro:if pattern is set up so a second base type could be added
   later:

   ```xml
   <xacro:if value="${current_base == 'g_shape'}">
     <xacro:include filename=".../g_shape_base_v2_0.urdf.xacro"/>
     <xacro:g_shape_base base_link="$(arg base_link)" prefix="$(arg prefix)"/>
   </xacro:if>
   ```

4. **Include and call the arm macro** — this is the line that pulls
   in the six revolute joints:

   ```xml
   <xacro:include filename=".../mycobot_280_arm.urdf.xacro"/>
   <xacro:mycobot_280_arm
     base_link="$(arg base_link)"
     flange_link="$(arg flange_link)"
     prefix="$(arg prefix)">
     <origin xyz="0 0 0" rpy="0 0 0"/>
   </xacro:mycobot_280_arm>
   ```

5. **Optional gripper** — bolted onto `flange_link` with a small
   offset:

   ```xml
   <xacro:if value="$(arg use_gripper)">
     <xacro:if value="${current_gripper == 'adaptive_gripper'}">
       <xacro:include filename=".../adaptive_gripper.urdf.xacro"/>
       <xacro:adaptive_gripper parent="$(arg flange_link)" prefix="$(arg prefix)">
         <origin xyz="0 0 0.034" rpy="1.579 0 0"/>
       </xacro:adaptive_gripper>
     </xacro:if>
   </xacro:if>
   ```

6. **Gazebo + ros2_control plugins** — included unconditionally so
   the robot has a transmission and a control plugin attached:

   ```xml
   <xacro:include filename=".../gazebo_sim_ros2_control.urdf.xacro"/>
   <xacro:load_gazebo_sim_ros2_control_plugin
     robot_name="$(arg robot_name)" use_gazebo="$(arg use_gazebo)"/>
   <xacro:include filename=".../mycobot_280_ros2_control.urdf.xacro"/>
   <xacro:mycobot_ros2_control
     prefix="$(arg prefix)" flange_link="$(arg flange_link)"
     use_gazebo="$(arg use_gazebo)"/>
   ```

7. **Camera sensor** — the Intel RealSense D435 RGB-D camera xacro
   gets included so perception exercises have a camera to subscribe
   to:

   ```xml
   <xacro:include filename=".../intel_rgbd_cam_d435.urdf.xacro"/>
   ```

That's the whole top-level file. It is a **menu**, not a definition.

### The arm definition: `mycobot_280_arm.urdf.xacro`

Path in the upstream repo:
[`mycobot_description/urdf/mech/mycobot_280_arm.urdf.xacro`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_description/urdf/mech/mycobot_280_arm.urdf.xacro).

This is the file that actually creates `link1`–`link6` and the joints
between them. Four sections:

1. **Shared properties** — numbers reused across all six joints and
   all seven links:

   ```xml
   <xacro:property name="joint_effort"   value="56.0"/>
   <xacro:property name="joint_velocity" value="2.792527"/>
   <xacro:property name="joint_damping"  value="0.0"/>
   <xacro:property name="joint_friction" value="0.0"/>

   <xacro:property name="link1_mass" value="0.12"/>
   <xacro:property name="link2_mass" value="0.19"/>
   <xacro:property name="link3_mass" value="0.16"/>
   <xacro:property name="link4_mass" value="0.124"/>
   <xacro:property name="link5_mass" value="0.11"/>
   <xacro:property name="link6_mass" value="0.0739"/>
   <xacro:property name="flange_mass" value="0.035"/>
   ```

   The total arm mass `0.12 + 0.19 + 0.16 + 0.124 + 0.11 + 0.0739 +
   0.035 ≈ 0.85 kg` matches the spec sheet.

2. **Two small helper macros**:

   ```xml
   <xacro:macro name="link_inertial" params="mass ixx iyy izz">
     <inertial>
       <origin xyz="0 0 0.0" rpy="0 0 0"/>
       <mass value="${mass}"/>
       <inertia ixx="${ixx}" ixy="0.0" ixz="0.0"
                iyy="${iyy}" iyz="0.0"
                izz="${izz}"/>
     </inertial>
   </xacro:macro>
   ```

   Every link calls this with its own mass + diagonal inertia
   instead of writing the whole inertial block by hand.

   ```xml
   <xacro:macro name="material_visual" params="ref_link ambient diffuse specular">
     <gazebo reference="${ref_link}">
       <visual>
         <material>
           <ambient>${ambient}</ambient>
           <diffuse>${diffuse}</diffuse>
           <specular>${specular}</specular>
         </material>
       </visual>
     </gazebo>
   </xacro:macro>
   ```

   Gives every link its colour in Gazebo without repeating the
   whole `<gazebo>` block.

3. **The big macro: `mycobot_280_arm`** — wraps everything below.
   When the top-level file calls `<xacro:mycobot_280_arm ...>`,
   xacro pastes:

   - Seven `<link>` blocks (`link1`..`link6` and `link6_flange`),
     each with:
     - an inertial block (from `link_inertial`),
     - a visual using a `.dae` mesh from
       `meshes/mycobot_280/visual/linkN.dae`,
     - a simpler collision shape (box or cylinder).
   - One **fixed** joint `base_link_to_link1` — link1 is bolted to
     the base, no motion.
   - Six **revolute** joints (`link1_to_link2` through
     `link6_to_link6_flange`). They share `effort=56 Nm`,
     `velocity=2.79 rad/s`, axis `0 0 1` (in the parent frame), and
     limits `±2.879 rad` except the last joint which gets `±3.05`.
   - Seven `material_visual` calls to colour the links grey or white.

   See [`../02-read-and-annotate-urdf/annotation.md`](../02-read-and-annotate-urdf/annotation.md)
   for the full link / joint table and the autosampler reach check
   that uses these numbers.

4. **No real code outside the macro.** The arm only appears in your
   URDF if some other file calls `<xacro:mycobot_280_arm .../>` —
   which the top-level composer does.

## How the two files fit together

```
mycobot_280.urdf.xacro                   <-- composer (the menu)
  ├─ adds: <link name="world"/> + virtual_joint   (when add_world=true)
  ├─ includes + calls: g_shape_base_v2_0.urdf.xacro  → defines base_link
  ├─ includes + calls: mycobot_280_arm.urdf.xacro    → defines link1..link6_flange
  ├─ includes + calls: adaptive_gripper.urdf.xacro   → defines gripper on flange
  ├─ includes + calls: gazebo_sim_ros2_control.urdf.xacro
  ├─ includes + calls: mycobot_280_ros2_control.urdf.xacro
  └─ includes:        intel_rgbd_cam_d435.urdf.xacro

After `xacro` expansion the whole chain flattens into one URDF that
MoveIt, RViz, robot_state_publisher, and Gazebo can all read.
```

## How this exercise's SDF connects to all this

The SDF in this folder pulls the **Gazebo model** of the arm — not the
xacro directly. Gazebo packages a model by writing a small
`model.config` next to a `model.sdf` (or an expanded URDF), and that
folder is what `model://mycobot_280` resolves to via
`GAZEBO_MODEL_PATH` / `GZ_SIM_RESOURCE_PATH`.

If you want to see exactly what the SDF `<include>` loads, run
`xacro mycobot_280.urdf.xacro > /tmp/mycobot_280.urdf` and open the
result. Every link and joint in the table in
[`../02-read-and-annotate-urdf/annotation.md`](../02-read-and-annotate-urdf/annotation.md)
is right there.
