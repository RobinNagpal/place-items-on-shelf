"""ament_python setup for yolo_live_demo (exercise 04)."""

from glob import glob

from setuptools import setup

package_name = "yolo_live_demo"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        # Standard ament_python plumbing.
        ("share/ament_index/resource_index/packages",
         [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        # Launch + config files shipped with the package.
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/config", glob("config/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="place-items-on-shelf",
    maintainer_email="dev@example.com",
    description="Live YOLOv8 inference on a Gazebo camera (exercise 04).",
    license="MIT",
    entry_points={
        "console_scripts": [
            # ros2 run yolo_live_demo live_detector
            "live_detector = yolo_live_demo.live_detector_node:main",
        ],
    },
)
