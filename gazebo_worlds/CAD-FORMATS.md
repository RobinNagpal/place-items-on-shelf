# CAD file formats and what Gazebo can use

Short reference for picking a mesh file when you want a real-world
shape instead of a `<box>` / `<cylinder>` / `<sphere>` primitive in
a Gazebo SDF.

## What CAD programs export

CAD programs (SOLIDWORKS, Fusion 360, Onshape, FreeCAD, Inventor,
Rhino, etc.) save / export to two different families of file.

### Solid / parametric formats — keep the *math* of the shape

These store the curves, dimensions, and feature history. Use them to
send a part to another CAD program or to a manufacturer.

| Extension | What it is |
|---|---|
| `.step` / `.stp` | Universal CAD interchange. Every CAD program reads it. |
| `.iges` / `.igs` | Older universal interchange. Still common. |
| `.sldprt` | SOLIDWORKS native part file. |
| `.f3d` | Autodesk Fusion 360 native file. |
| `.ipt` | Autodesk Inventor native part file. |
| `.x_t`, `.x_b` | Parasolid (used internally by many CAD kernels). |
| `.3dm` | Rhino native file. |

**Gazebo cannot read any of these directly.**

### Mesh / surface formats — the shape is "frozen" into triangles

These store only the triangle soup, not the underlying math. Used for
3D printing, rendering, and physics simulation.

| Extension | What it stores | Gazebo? |
|---|---|---|
| `.dae` (COLLADA) | triangles + colour + texture + materials + scene units | **Yes — preferred** |
| `.obj` (Wavefront) | triangles + colour + texture coordinates | **Yes — good** |
| `.stl` | triangles only, no colour, no units (3D-printer default) | **Yes — works, but you set colour in the SDF and you fix units manually** |
| `.fbx` | Autodesk interchange, animations, materials | No |
| `.gltf` / `.glb` | modern web 3D format | No (convert to DAE first) |
| `.3mf` | modern 3D-print format | No |
| `.ply` | research / scanner format | No |

## The rule

- If your CAD program offers **`.dae`, `.obj`, or `.stl`**, export to
  one of those — Gazebo loads it directly.
- If your CAD program only offers `.step` / `.iges` / a vendor-specific
  format, open it in **FreeCAD** (free) and re-export to `.dae` or
  `.stl`.

Almost every CAD program has at least **STL export** built in (it's
the 3D-print default), so in practice you can always get something
Gazebo can use, even if it costs one extra FreeCAD hop.

## Referencing a mesh from an SDF

The SDF block to replace a primitive `<cylinder>` / `<box>` with a
mesh:

```xml
<visual name="v">
  <geometry>
    <mesh>
      <uri>file://meshes/beaker_100ml.dae</uri>
      <scale>1 1 1</scale>
    </mesh>
  </geometry>
</visual>
<collision name="c">
  <!-- Keep collision as a primitive: physics is much faster. -->
  <geometry>
    <cylinder><radius>0.025</radius><length>0.070</length></cylinder>
  </geometry>
</collision>
```

The `file://` URI is relative to the **SDF file's own directory**, so
put mesh files in a `meshes/` subfolder next to the `.sdf`.

## Common gotchas

| Problem | Fix |
|---|---|
| Beaker shows up 1000× too big | The STL was in millimetres; Gazebo wants metres. Scale by 0.001 in Blender or set `<scale>0.001 0.001 0.001</scale>` in the SDF. |
| Beaker sinks half-way through the bench | The mesh origin is at its geometry centre, not at the base. Re-origin in Blender (Object → Set Origin → Origin to 3D Cursor) or shift `<pose>` z by +half-height. |
| Real-time factor drops once a mesh is loaded | Polygon count too high. Use Blender's *Decimate* modifier or MeshLab's *Quadric Edge Collapse* to target ≤ 20 k triangles for any single visible-but-secondary object. |
| `[Err] Mesh URI not found` | The `file://` path is wrong. Path is relative to the SDF, not the working directory. `ls` from the SDF folder to verify the mesh exists where the SDF says it does. |
| Mesh loads but has no colour in Gazebo | STL has no colour. Either switch to `.dae` (carries materials), `.obj` (carries colour), or set a `<material>` block inside the SDF `<visual>`. |
