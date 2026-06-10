# Type 7 — Camera calibration sets

## What it is

Two short collections of images, each used to verify a
specific piece of calibration code:

- **Intrinsics set.** Many simulated photos of a virtual
  **checkerboard** at different known poses. Used to check that
  `cv2.calibrateCamera` recovers the camera's focal length,
  principal point, and lens distortion correctly.
- **Hand-eye set.** Pairs of `(arm pose, marker-in-camera
  pose)` collected as the arm waves a marker in front of the
  camera. Used to check that `cv2.calibrateHandEye` recovers the
  camera-to-arm rigid transform correctly.

Both sets look the same on disk — a bunch of `.jpg` files plus
a small CSV of poses — but they answer different questions.

## When it is useful

The cell needs these two calibrations to work **before any 3D
math is trustworthy**. In a real lab:

- Intrinsics calibration happens once, when the camera is
  bolted in.
- Hand-eye calibration happens whenever the camera or the arm
  base is moved.

The trouble: a junior engineer often writes the calibration
code, runs it on the real camera once, and ships it. **If the
code has a bug, you find out months later when the placement is
off by 5 mm.** The synthetic set catches that bug **before** the
camera is ever bolted in.

## Who uses it

**No ML model.** Two plain OpenCV functions:

| Set | Consumer | What it returns |
|---|---|---|
| Intrinsics | `cv2.calibrateCamera(...)` | `K` (3×3 intrinsic matrix), `dist` (distortion coefficients) |
| Hand-eye | `cv2.calibrateHandEye(...)` | `T_camera_to_endeffector` (4×4 rigid transform) |

Because the simulator **already knows the true values** (you
wrote them into the SDF), you can compare what OpenCV returns
to what you wrote. Pass / fail is exact.

## How to produce it in Gazebo

Two recipes, one per set.

### Intrinsics set

#### 1. Build a virtual checkerboard model

A 9 × 6 inner-corner checkerboard with 25 mm squares is the
classic choice. The model is a flat plane with a checkerboard
texture:

```xml
<model name="checkerboard">
  <link name="board">
    <visual name="surface">
      <geometry>
        <plane>
          <size>0.300 0.225</size>     <!-- 9 squares × 6 squares × 25 mm -->
        </plane>
      </geometry>
      <material>
        <pbr>
          <metal>
            <albedo_map>textures/checkerboard_9x6_25mm.png</albedo_map>
          </metal>
        </pbr>
      </material>
    </visual>
  </link>
</model>
```

#### 2. Move the board around in a script

In a small ROS 2 / Gazebo Python node, programmatically:

```python
# pseudo-code — moves the board to 25 randomised poses
for i in range(25):
    pose = random_in_camera_frustum()
    spawn_or_move("checkerboard", pose)
    save_camera_frame(f"intrinsics_{i:03d}.jpg")
```

"Randomised but in-view" matters: at least 80 % of the board
must be visible in each frame or `cv2.findChessboardCorners`
will fail.

#### 3. Run the calibration

```python
images = sorted(glob.glob("intrinsics_*.jpg"))
img_pts, obj_pts = [], []
for f in images:
    found, corners = cv2.findChessboardCorners(cv2.imread(f), (9, 6))
    if found:
        img_pts.append(corners)
        obj_pts.append(world_pts_9x6_25mm)
err, K, dist, *_ = cv2.calibrateCamera(obj_pts, img_pts, image_size,
                                       None, None)
print("reprojection error:", err)         # should be < 0.5 px in sim
```

Compare `K` to the intrinsics in the SDF camera tag. They should
match to ≤ 0.5 % — if not, the calibration code has a bug.

### Hand-eye set

#### 1. Stick an ArUco marker on the arm's gripper

A `cv2.aruco` `DICT_4X4_50` marker, ID 0, 40 mm side. Texture
generated with `cv2.aruco.drawMarker`. Mount it as a thin plane
under the gripper.

#### 2. Drive the arm through 20 distinct poses

Same scripted-node idea:

```python
for i in range(20):
    arm_target = random_reachable_pose()
    move_arm(arm_target)
    rclpy.spin_once(node)                  # let TF settle
    img = save_camera_frame(f"handeye_{i:03d}.jpg")
    arm_pose  = read_tf("base", "tool0")
    cam_pose  = solve_pnp_for_aruco(img)   # see exercise 10
    log.append((arm_pose, cam_pose))
```

#### 3. Run the calibration

```python
R_handeye, t_handeye = cv2.calibrateHandEye(
    R_gripper2base = [p.R for p, _ in log],
    t_gripper2base = [p.t for p, _ in log],
    R_target2cam   = [c.R for _, c in log],
    t_target2cam   = [c.t for _, c in log],
)
```

Compare `R_handeye, t_handeye` to the SDF's known
camera-to-arm transform. They should match to ≤ 5 mm and ≤ 1°.

## What you end up with

```
synthetic_calibration/
├── intrinsics/
│   ├── intrinsics_000.jpg ... 024.jpg
│   ├── true_K.json                # ground truth from SDF
│   └── true_dist.json
└── handeye/
    ├── handeye_000.jpg ... 019.jpg
    ├── arm_poses.csv              # one row per pose
    └── true_T_camera_to_ee.json
```

This is generated **once** per camera + arm pair. You do **not**
need ketchup-step-specific versions — the same set covers all
of Steps 2 / 3 / 4 / 5 / 8.

## Existing project reference

[`exercises/12-hand-eye-calibration/`](../../../../exercises/12-hand-eye-calibration/)
already runs the eye-to-hand variant on the v1 autosampler
setup. The synthetic-set generator above is the input it
already expects.
