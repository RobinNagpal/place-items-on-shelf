// park_pose_demo.cpp
//
// Joint-space "hello world" for the myCobot 280 in the HPLC autosampler
// cell. Implements checklist item 18 (autosampler tie-in) from
//   docs/learning-checklist.md.
//
// Sequence:
//
//     home (SRDF) -> ready (SRDF, our "park between trays") -> home (SRDF)
//
// We do NOT define a new world here. The scene this exercise targets is
//   ../../../01-custom-gazebo-world/worlds/autosampler_cell.sdf
// where the source rack sits at y = +0.12 m and the destination tray
// sits at y = -0.12 m. The SRDF "ready" pose
//   [0, 0, 1.5708, 1.5708, 0, 0] rad
// folds the elbow and wrist up, holding the gripper above and in front
// of the shoulder - clear of both peripherals. That makes "ready" the
// natural autosampler park pose.
//
// We talk to a running move_group action server; the trajectory is
// executed by whatever joint trajectory controller mycobot_gazebo
// brought up. See README.md for the 3-terminal launch flow.

#include <chrono>
#include <memory>
#include <string>
#include <thread>

#include <moveit/move_group_interface/move_group_interface.hpp>
#include <rclcpp/rclcpp.hpp>

using moveit::planning_interface::MoveGroupInterface;
using namespace std::chrono_literals;

namespace
{
// Planning group from addison's SRDF.
constexpr char kArmGroup[] = "arm";

// Plan and execute a goal named in the SRDF (e.g. "home", "ready").
// Returns true only if both the plan and the execute step succeeded.
bool go_to(MoveGroupInterface & arm, const std::string & name,
           const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "Planning to '%s'.", name.c_str());

  // Always start planning from where the arm actually is right now.
  arm.setStartStateToCurrentState();
  arm.setNamedTarget(name);

  MoveGroupInterface::Plan plan;
  if (arm.plan(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "Planning to '%s' failed.", name.c_str());
    return false;
  }

  RCLCPP_INFO(logger, "Plan ok, executing.");
  return arm.execute(plan) == moveit::core::MoveItErrorCode::SUCCESS;
}
}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  // automatically_declare_parameters_from_overrides lets the launch
  // file hand us robot_description_semantic, kinematics.yaml,
  // joint_limits.yaml and the trajectory_execution config without us
  // having to declare each one by name here.
  auto node = std::make_shared<rclcpp::Node>(
    "park_pose_demo",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto logger = node->get_logger();

  // MoveGroupInterface spins the node behind the scenes; we still
  // add it to our own executor so future subscriptions / services
  // attached to this node get spun too.
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() { executor.spin(); });

  // Configure the planning group. RRTConnect is a fast, well-tested
  // OMPL planner that works well for joint-space goals on a 6-DoF arm.
  MoveGroupInterface arm(node, kArmGroup);
  arm.setPlanningPipelineId("ompl");
  arm.setPlannerId("RRTConnectkConfigDefault");
  arm.setPlanningTime(2.0);
  // Move slowly in sim so a beginner watching can see what's happening.
  // For production code these would come from a config file.
  arm.setMaxVelocityScalingFactor(0.3);
  arm.setMaxAccelerationScalingFactor(0.3);

  // Give MoveGroupInterface a moment to latch onto move_group's state
  // (the action server has to be ready before our first plan call).
  std::this_thread::sleep_for(2s);

  // The whole "task" is three named goals.
  const bool ok = go_to(arm, "home", logger)
               && go_to(arm, "ready", logger)
               && go_to(arm, "home", logger);

  RCLCPP_INFO(logger, "Sequence %s.", ok ? "OK" : "FAILED");

  rclcpp::shutdown();
  spinner.join();
  return ok ? 0 : 1;
}
