// Minimal MoveIt 2 task for the myCobot 280 arm.
//
// Sequence: home (SRDF) -> ready (SRDF) -> explicit joint goal -> home (SRDF).
// Talks to a running move_group server; trajectories execute via the
// joint trajectory controller already loaded by mycobot_gazebo.

#include <chrono>
#include <memory>
#include <thread>
#include <vector>

#include <moveit/move_group_interface/move_group_interface.hpp>
#include <rclcpp/rclcpp.hpp>

using moveit::planning_interface::MoveGroupInterface;
using namespace std::chrono_literals;

namespace
{
constexpr char kArmGroup[] = "arm";

bool plan_and_execute_named(MoveGroupInterface & arm, const std::string & name, const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "Planning to named target: %s", name.c_str());
  arm.setStartStateToCurrentState();
  arm.setNamedTarget(name);

  MoveGroupInterface::Plan plan;
  const auto code = arm.plan(plan);
  if (code != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "Planning to '%s' failed (code %d)", name.c_str(), code.val);
    return false;
  }
  RCLCPP_INFO(logger, "Plan ok, executing.");
  return arm.execute(plan) == moveit::core::MoveItErrorCode::SUCCESS;
}

bool plan_and_execute_joints(MoveGroupInterface & arm, const std::vector<double> & joints, const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "Planning to explicit joint goal (%zu joints)", joints.size());
  arm.setStartStateToCurrentState();
  if (!arm.setJointValueTarget(joints)) {
    RCLCPP_ERROR(logger, "Joint goal rejected (limits / size mismatch).");
    return false;
  }

  MoveGroupInterface::Plan plan;
  const auto code = arm.plan(plan);
  if (code != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "Planning to joint goal failed (code %d)", code.val);
    return false;
  }
  RCLCPP_INFO(logger, "Plan ok, executing.");
  return arm.execute(plan) == moveit::core::MoveItErrorCode::SUCCESS;
}
}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "cobot280_move_to_named_pose",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto logger = node->get_logger();

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() { executor.spin(); });

  MoveGroupInterface arm(node, kArmGroup);
  arm.setPlanningPipelineId("ompl");
  arm.setPlannerId("RRTConnectkConfigDefault");
  arm.setPlanningTime(2.0);
  arm.setMaxVelocityScalingFactor(0.3);
  arm.setMaxAccelerationScalingFactor(0.3);

  std::this_thread::sleep_for(2s);

  bool ok = true;
  ok &= plan_and_execute_named(arm, "home", logger);
  ok &= plan_and_execute_named(arm, "ready", logger);
  ok &= plan_and_execute_joints(arm, {0.5, -0.3, 0.8, -0.5, 0.0, 0.0}, logger);
  ok &= plan_and_execute_named(arm, "home", logger);

  RCLCPP_INFO(logger, "Sequence finished: %s", ok ? "all stages succeeded" : "one or more stages failed");

  rclcpp::shutdown();
  spinner.join();
  return ok ? 0 : 1;
}
