# Verify your environment

Run each block and check the expected output. If anything is wrong, fix it before continuing.

```bash
# 1) OS — expect: Ubuntu 24.04.x LTS
lsb_release -a

# 2) Python — expect: Python 3.12.x
python3 --version

# 3) ROS 2 Jazzy is installed
ls /opt/ros/jazzy/setup.bash

# 4) ROS 2 environment is sourced. (Note: `ros2 --version` does NOT exist;
#    use the checks below instead.)
source /opt/ros/jazzy/setup.bash
printenv ROS_DISTRO          # expect: jazzy
ros2 pkg list | head -5      # expect: a list of installed ROS packages

# 5) Build tool
which colcon                 # expect: a path, e.g. /usr/bin/colcon

# 6) Dependency resolver
rosdep --version             # expect: a version number (warnings about pkg_resources are fine)
ls ~/.ros/rosdep/sources.cache && echo "rosdep cache OK"

# 7) GUI packages the viewer needs
dpkg -l | grep -E 'ros-jazzy-(rviz2|robot-state-publisher|joint-state-publisher-gui|xacro)\s'
# Expect four lines, one per package, all marked installed.

# 8) git
git --version
```

## WSL-only: confirm GUI passthrough works

WSL 2 on Windows 11 has WSLg built in. If you are on WSL 1 or an older WSL 2, GUIs will not work without extra setup.

```bash
sudo apt install -y x11-apps  # only needed if xeyes is missing
xeyes
```

Expect: a small window with cartoon eyes pops up **on your Windows desktop**. If it appears, RViz will work. Close it with Ctrl+C in the terminal.

If you get `Error: Can't open display:` or nothing appears:
- Make sure you are on Windows 11 with the latest WSL: `wsl --update` from a Windows PowerShell.
- Or update WSL to version 2: `wsl --set-default-version 2`.
- Reboot Windows after updating WSL.
