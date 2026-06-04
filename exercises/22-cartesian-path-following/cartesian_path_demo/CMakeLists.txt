cmake_minimum_required(VERSION 3.16)
project(cartesian_path_demo)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(shape_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)

add_executable(cartesian_path_demo src/cartesian_path_demo.cpp)
ament_target_dependencies(cartesian_path_demo
  rclcpp
  geometry_msgs
  shape_msgs
  moveit_msgs
  tf2
  moveit_ros_planning_interface
)

install(TARGETS cartesian_path_demo
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
