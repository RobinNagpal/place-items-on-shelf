# Run — Step 1: myCobot 280 Pi URDF viewer in RViz

This step opens RViz with the arm rendered at exact hardware scale and a slider GUI to move every joint. The launch file we use is **shipped by addison's `mycobot_description` package** — we don't author our own.

## Assumed layout

```
~/ros2_ws/
├── src/
│   └── place-items-on-shelf/
│       └── robots/
│           └── mycobot-280-pi/
│               ├── docs/...
│               └── src/mycobot_ros2/   <- git submodule (automaticaddison)
```

If you cloned the repo elsewhere, replace `~/ros2_ws` with your actual workspace path everywhere below.

## 0. Make sure you are on a branch that has this folder

If the PR introducing this folder is not yet merged to `main`, `git switch main` will leave you without the new files. Check:

```bash
cd ~/ros2_ws/src/place-items-on-shelf
git fetch origin
git switch add-elephant-robotics-best-option-task    # or `main` once the PR is merged
```

## 1. First-time only — initialise the submodule

If you cloned with `git clone --recurse-submodules`, skip to step 1b.

Otherwise:

```bash
cd ~/ros2_ws/src/place-items-on-shelf
git submodule update --init --recursive
```

Confirm it worked:

```bash
ls robots/mycobot-280-pi/src/mycobot_ros2/mycobot_description/urdf/robots/mycobot_280.urdf.xacro
# Expected: the path is printed back.
```

## 1b. First-time only — create the addison symlink (REQUIRED)

addison's launch files [hardcode the source-tree path](https://github.com/automaticaddison/mycobot_ros2/blob/a75c80d/mycobot_description/launch/robot_state_publisher.launch.py#L46) as `~/ros2_ws/src/mycobot_ros2/...`. We vendor the repo at a deeper path. Bridge the two with a symlink:

```bash
ln -sfT \
  ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/src/mycobot_ros2 \
  ~/ros2_ws/src/mycobot_ros2

# Verify it resolves
ls -ld ~/ros2_ws/src/mycobot_ros2
# Expected: lrwxrwxrwx ... ~/ros2_ws/src/mycobot_ros2 -> ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/src/mycobot_ros2
ls ~/ros2_ws/src/mycobot_ros2/mycobot_gazebo/launch/mycobot.gazebo.launch.py
# Expected: the path is printed back.
```

Without this symlink you'll see `[Errno 2] No such file or directory: '/home/<you>/ros2_ws/src/mycobot_ros2/mycobot_moveit_config/config/mycobot_280/ros2_controllers_template.yaml'` at launch time. The empty `robots/mycobot-280-pi/src/COLCON_IGNORE` file we ship makes colcon scan ONLY the symlinked path, so packages aren't built twice.

## 2. Source ROS 2

Use whichever distro you installed:

```bash
source /opt/ros/jazzy/setup.bash      # Ubuntu 24.04
# or
source /opt/ros/humble/setup.bash     # Ubuntu 22.04
```

> **If you see warnings about stale `AMENT_PREFIX_PATH` / `COLCON_PREFIX_PATH` paths** on the next colcon step, clear them in this shell:
>
> ```bash
> unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
> source /opt/ros/jazzy/setup.bash     # re-source after unsetting
> ```

## 3. Build addison's packages

For Step 1 we only need `mycobot_description`. From the workspace root:

```bash
cd ~/ros2_ws
colcon build --packages-select mycobot_description --symlink-install
```

> If a previous build of your workspace left stale `install/` directories from packages that no longer exist in `src/`, wipe them first: `rm -rf build install log` before the `colcon build` line.

`--symlink-install` means edits to URDFs / meshes show up without a rebuild. If the build finishes with `Summary: 1 package finished`, you are good.

> For Step 2 (Gazebo) you will build more packages; see [`run_sim.md`](run_sim.md).

## 4. Source the workspace

```bash
source ~/ros2_ws/install/setup.bash
```

You need to do this in every fresh terminal where you want to run the launch file. (Or add it to `~/.bashrc`.)

## 5. Launch the viewer

```bash
ros2 launch mycobot_description robot_state_publisher.launch.py
```

addison's launch file starts `robot_state_publisher`, `joint_state_publisher_gui`, and `rviz2` together. Defaults:

- `use_rviz=true` — RViz opens automatically.
- `jsp_gui=true` — joint sliders GUI is enabled.
- `use_gripper=true` — the adaptive gripper is attached.
- `use_camera=false`, `use_gazebo=false` — no camera, no sim plugin in this step.

Two windows open:

1. **RViz** showing the myCobot 280 with the adaptive gripper. Fixed frame is `base_link`. A grid is drawn on the floor; the arm reaches ~280 mm at full extension.
2. **joint_state_publisher_gui** with six sliders (one per joint) plus gripper sliders. Drag a slider — the arm moves in real time.

If you want to see the bare arm without the gripper:

```bash
ros2 launch mycobot_description robot_state_publisher.launch.py use_gripper:=false
```

## 6. Stopping it

`Ctrl-C` in the terminal kills RViz, the slider GUI, and the publisher in one shot.

## Common issues

- **`Package 'mycobot_description' not found`** — the submodule isn't checked out, or `colcon build` was skipped (step 3), or the workspace wasn't sourced after the build (step 4).
- **`... is not a valid package name`** at the end of `ros2 launch` — you accidentally passed a file path instead of `mycobot_description robot_state_publisher.launch.py`. Use the package + launchfile form.
- **WARNINGs about `.../install` paths during `colcon build`** — leftover env vars from a previous workspace. Use the `unset` block in step 2.
- **"Fixed Frame [base_link] does not exist"** in RViz — `robot_state_publisher` hasn't published the URDF yet. Wait a second; if it persists, check the terminal for a URDF parse error.
- **Meshes appear as untextured grey shapes** — that's normal for the `.dae` files. Lighting is rough.

## What this does NOT do

- No physics — RViz is a viewer, not a simulator. Gravity / collisions / contact don't apply. That's Step 2 ([`run_sim.md`](run_sim.md)).
- No motion planning — that's Step 3 (MoveIt 2).
- No real arm — no serial port, no `pymycobot`. Pure visualization.
