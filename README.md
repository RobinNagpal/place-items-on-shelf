# place-items-on-shelf

v1_simple_pick is a small ROS 2 + Gazebo Harmonic scripted pick-and-place demo.
The robot uses hardcoded poses to pick one item from a shelf and place it on its tray.
See v1_simple_pick/README.md for details.

v3_mycobot_pi is the real-hardware version, built around the Elephant Robotics
myCobot 280 Pi (6-DOF arm with onboard Raspberry Pi 4). Step 1 (this folder
today) is a URDF at the exact hardware dimensions, viewable in RViz with
joint sliders. Later steps add Gazebo physics, MoveIt, vision, and a real-
arm bringup. See v3_mycobot_pi/README.md for the full roadmap and run
instructions.
