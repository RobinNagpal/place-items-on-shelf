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

## If you start from a `.blend` file

Sketchfab and other model sites often ship the original `.blend`
(Blender) file. Blender is not Gazebo, but it is a free one-stop
shop: open the `.blend`, delete what you do not need, then
**File → Export → Collada (.dae)** to get the Gazebo-ready mesh.
Install once with `sudo apt install blender`, open with
`blender path/to/file.blend`.
