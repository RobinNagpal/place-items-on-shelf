# From YOLO to MoveIt — the six steps

How a camera image becomes a Cartesian goal the arm can act on.

**1. YOLO box (exercise 03/04).**
Output: `(class="red_cap", bbox=(x_min, y_min, x_max, y_max), confidence=0.91)`.
The `(x, y)` numbers are **pixels on the camera image**, not metres. This is not yet useful for the arm — you can't send the gripper to "pixel 412". You can only say *which* objects you saw and roughly where they are *in the image*.

**2. YOLO-seg mask (exercise 07).**
Same detection, but now instead of a rectangle you get a per-pixel boolean mask. This matters when two red caps overlap in the image — the box would include some of the wrong cap's pixels, the mask would not. **The mask is still 2D.** Its only job is to tell us *exactly which pixels belong to this object* so the next step looks at the right depths.

**3. Depth camera.**
A depth (RGBD) camera gives a second image, aligned to the colour one, where each pixel holds a **distance from the camera** in metres (Z). If the mask says "200 pixels are this red cap", you read 200 Z values from the depth image — one per pixel.

Those 200 Z values are **not all identical** — the cap is curved, and the camera might be slightly off-axis, so pixels nearer the edge see a slightly farther surface. We don't pick one — we **aggregate**, usually the median (robust to a few bad depth pixels). One number per object.

**4. Pixels + depth → 3D (camera intrinsics).**
This is the bit that bridges 2D-image to 3D-metres. Every camera has four numbers from a one-time calibration: `fx, fy` (focal length in pixels) and `cx, cy` (where the optical axis hits the image). With those, every `(u, v, Z)` triple becomes a 3D point in the camera's own frame:

```
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
Z = Z              (already the distance)
```

So for the cap, you take the **centroid of the masked pixels** `(u̅, v̅)`, the **median depth** `Z̅`, and the formula gives you one 3D point `(X, Y, Z)` in metres, in the camera's frame. This is exactly what exercise 08 publishes on `/objects/centroids`.

**5. Camera frame → robot base frame (hand-eye calibration, exercise 12).**
The 3D point from step 4 lives in the **camera's coordinate system**. The arm doesn't know where the camera is — it only knows poses in its own **base frame**. Hand-eye calibration is a one-time procedure where you wave an ArUco marker around in front of the camera while recording where the arm thinks the marker is and where the camera thinks the marker is. `cv2.calibrateHandEye` solves for the 4×4 transform between the two frames.

Once you have that 4×4 matrix, every 3D point coming out of step 4 gets multiplied by it, and now you have the cap's position **in robot base frame** — exactly what the arm needs.

**6. MoveIt (exercises 19, 21).**
You hand the base-frame point to `setPoseTarget(...)`, MoveIt runs inverse kinematics + plans a collision-free trajectory, and the arm goes there. The fact that the source was YOLO + depth + calibration is invisible to MoveIt — it just sees a Cartesian goal.
