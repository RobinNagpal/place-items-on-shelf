# Saved maps

After running `slam.launch.py` and driving the robot around with teleop
until the room looks complete in RViz, save the map here so the next
Nav2 PR can load it.

From a sourced terminal (with the SLAM launch still running):

```bash
cd ~/ros2_ws/src/place-items-on-shelf/v2/pos_v2_navigation/maps
ros2 run nav2_map_server map_saver_cli -f backroom
```

That writes two files into this folder:

- `backroom.pgm` — the actual occupancy grid (greyscale PNG-style image).
- `backroom.yaml` — metadata (resolution, origin, free/occupied
  thresholds, path to the `.pgm`).

After saving, rebuild the workspace (`colcon build --packages-select
pos_v2_navigation --symlink-install`) so the installed share/ copy
picks up the new files. Nav2 will load them in a follow-up PR.

The `.pgm` is a binary image; if you want it to render in GitHub diffs,
convert with `convert backroom.pgm backroom.png` and commit both. Don't
delete the `.pgm` — Nav2's map server reads it, not the `.png`.
