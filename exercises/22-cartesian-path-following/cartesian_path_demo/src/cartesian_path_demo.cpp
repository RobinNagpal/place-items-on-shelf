// cartesian_path_demo.cpp
//
// Straight-line Cartesian path with MoveIt's computeCartesianPath.
// Implements checklist item 22 (autosampler tie-in) from
// docs/learning-checklist.md.
//
// WHAT THIS DOES
//
//   We tell MoveIt:
//     "Move the end-effector from where it is, IN A STRAIGHT LINE,
//      down 5 cm, then back up 5 cm."
//
//   computeCartesianPath interpolates the line in end-effector space
//   at 5 mm steps, runs IK at every step, and returns a joint
//   trajectory that traces the line. We then hand that trajectory to
//   execute() the same way we did for a regular plan in exercises
//   18-21.
//
// HOW THIS DIFFERS FROM THE TWO APPROACHES WE ALREADY USED
//
//   18: setNamedTarget("home")    -> SRDF lookup -> joint-space plan.
//                                    Where the gripper goes in 3D
//                                    space is not controlled.
//   19: setPoseTarget(pose)       -> IK at the goal -> joint-space
//                                    plan to those joint values. The
//                                    gripper visits the goal but the
//                                    CARTESIAN PATH between start and
//                                    goal is whatever the planner
//                                    invents (usually curved).
//   22 (this exercise):
//       computeCartesianPath([..]) -> IK at EVERY 5 mm step along the
//                                    straight line; trajectory traces
//                                    the line itself.
//
//   In short: 18 and 19 control endpoints; 22 controls the PATH.
//
// We do NOT define a new world here. The scene this exercise targets
// is the v1 world from exercise 1
//   ../../01-custom-gazebo-world/worlds/autosampler_cell.sdf
// and the planning scene is seeded with the same bench / rack / tray
// / housing-wall collision objects we used in exercises 20 and 21.

#include <chrono>
#include <cmath>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <moveit_msgs/msg/robot_trajectory.hpp>
#include <rclcpp/rclcpp.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>
#include <tf2/LinearMath/Quaternion.h>

using moveit::planning_interface::MoveGroupInterface;
using moveit::planning_interface::PlanningSceneInterface;
using namespace std::chrono_literals;

namespace
{
constexpr char kArmGroup[] = "arm";
constexpr char kTipLink[]  = "link6_flange";
constexpr char kBaseLink[] = "base_link";

// 5 mm step between IK evaluations along the Cartesian line. Smaller
// step = smoother trajectory + more IK calls. 5 mm is a common
// default in MoveIt 2 tutorials.
constexpr double kEefStep = 0.005;

// We treat anything >= 99 % of the line as success. computeCartesianPath
// returns 0.0..1.0; 1.0 means the full path was achievable.
constexpr double kSuccessFraction = 0.99;

geometry_msgs::msg::Pose make_pose(double x, double y, double z,
                                   double roll, double pitch, double yaw)
{
  tf2::Quaternion q;
  q.setRPY(roll, pitch, yaw);
  geometry_msgs::msg::Pose p;
  p.position.x = x;
  p.position.y = y;
  p.position.z = z;
  p.orientation.x = q.x();
  p.orientation.y = q.y();
  p.orientation.z = q.z();
  p.orientation.w = q.w();
  return p;
}

moveit_msgs::msg::CollisionObject make_box(
  const std::string & id, double cx, double cy, double cz,
  double sx, double sy, double sz)
{
  moveit_msgs::msg::CollisionObject obj;
  obj.header.frame_id = kBaseLink;
  obj.id = id;
  shape_msgs::msg::SolidPrimitive prim;
  prim.type = prim.BOX;
  prim.dimensions = {sx, sy, sz};
  geometry_msgs::msg::Pose pose;
  pose.position.x = cx;
  pose.position.y = cy;
  pose.position.z = cz;
  pose.orientation.w = 1.0;
  obj.primitives.push_back(prim);
  obj.primitive_poses.push_back(pose);
  obj.operation = obj.ADD;
  return obj;
}

// Move to a pose using the EXERCISE 19 approach (joint-space plan to
// an IK answer). We use this just to get the arm into the starting
// hover pose before the Cartesian segment.
bool go_pose(MoveGroupInterface & arm,
             const geometry_msgs::msg::Pose & pose,
             const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "[pose ] joint-space plan to (%.3f, %.3f, %.3f)",
              pose.position.x, pose.position.y, pose.position.z);
  arm.setStartStateToCurrentState();
  geometry_msgs::msg::PoseStamped t;
  t.header.frame_id = kBaseLink;
  t.pose = pose;
  arm.setPoseTarget(t, kTipLink);
  MoveGroupInterface::Plan plan;
  if (arm.plan(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "  plan FAILED");
    return false;
  }
  return arm.execute(plan) == moveit::core::MoveItErrorCode::SUCCESS;
}

// Move in a straight Cartesian line from the current EE pose to the
// goal pose. This is the new technique for exercise 22.
//
// The MoveIt 2 (Jazzy / Rolling) signature is:
//   double computeCartesianPath(
//     const std::vector<Pose>& waypoints,
//     double eef_step,
//     moveit_msgs::msg::RobotTrajectory& trajectory,
//     bool avoid_collisions = true,
//     moveit_msgs::msg::MoveItErrorCodes* error_code = nullptr);
//
// `fraction` is the share of the path that was achievable. 1.0 means
// the full line could be traced; less than 1.0 means MoveIt had to
// stop early (an IK call failed mid-line, or the path would have
// collided with something).
bool go_cartesian(MoveGroupInterface & arm,
                  const std::string & label,
                  const geometry_msgs::msg::Pose & goal,
                  const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger,
              "[cart ] computeCartesianPath -> %-12s (%.3f, %.3f, %.3f)",
              label.c_str(), goal.position.x, goal.position.y, goal.position.z);
  arm.setStartStateToCurrentState();

  std::vector<geometry_msgs::msg::Pose> waypoints = {goal};
  moveit_msgs::msg::RobotTrajectory trajectory;
  const double fraction = arm.computeCartesianPath(
    waypoints, kEefStep, trajectory, /*avoid_collisions=*/true);

  RCLCPP_INFO(logger, "  achieved fraction = %.2f (1.00 = full path)",
              fraction);
  if (fraction < kSuccessFraction) {
    RCLCPP_ERROR(logger,
                 "  '%s' did not trace the full line (fraction=%.2f). "
                 "An IK seed jumped, or part of the path was blocked.",
                 label.c_str(), fraction);
    return false;
  }
  return arm.execute(trajectory) == moveit::core::MoveItErrorCode::SUCCESS;
}
}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "cartesian_path_demo",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto logger = node->get_logger();

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() { executor.spin(); });

  MoveGroupInterface arm(node, kArmGroup);
  arm.setPlanningPipelineId("ompl");
  arm.setPlannerId("RRTConnectkConfigDefault");
  arm.setPlanningTime(3.0);
  arm.setNumPlanningAttempts(5);
  arm.setGoalPositionTolerance(0.001);
  arm.setGoalOrientationTolerance(0.01);
  arm.setMaxVelocityScalingFactor(0.3);
  arm.setMaxAccelerationScalingFactor(0.3);

  std::this_thread::sleep_for(2s);

  // -------------------------------------------------------------
  // Reuse the bench / rack / tray / housing wall collision objects
  // from exercises 20 and 21. computeCartesianPath respects the
  // planning scene when avoid_collisions=true, so these block the
  // line just like they would a joint-space plan.
  // -------------------------------------------------------------
  PlanningSceneInterface scene;
  scene.applyCollisionObjects({
    make_box("bench_top",                0.18,  0.00, -0.030, 0.60, 0.40, 0.005),
    make_box("source_rack",              0.23, +0.12,  0.050, 0.09, 0.18, 0.05),
    make_box("tray_block",               0.23, -0.12,  0.020, 0.16, 0.16, 0.03),
    make_box("autosampler_housing_wall", 0.18, +0.23,  0.20,  0.60, 0.02, 0.40),
  });
  std::this_thread::sleep_for(500ms);

  // -------------------------------------------------------------
  // Targets in the arm's base_link frame. We pick a point well
  // inside the reach envelope so the IK at every 5 mm step succeeds.
  //
  //   hover : 13 cm above the bench, in front of the arm.
  //   work  : 5 cm below hover -> simulates the descent into a well.
  //
  // Roll = pi: gripper points straight down throughout.
  // -------------------------------------------------------------
  const auto hover = make_pose(0.180, +0.100, 0.130, M_PI, 0, 0);
  const auto work  = make_pose(0.180, +0.100, 0.080, M_PI, 0, 0);

  bool ok = true;

  // Step 1: get to the hover pose using the exercise-19 approach.
  //         The Cartesian path between start (home) and hover here
  //         is whatever OMPL invents - that's fine, we don't care
  //         how we get to the start of the line.
  ok &= go_pose(arm, hover, logger);

  // Step 2: straight-line DESCENT from hover to work.
  ok &= go_cartesian(arm, "descend (5 cm)", work, logger);

  // Step 3: straight-line LIFT from work back to hover.
  ok &= go_cartesian(arm, "lift (5 cm)", hover, logger);

  RCLCPP_INFO(logger, "Sequence %s.", ok ? "OK" : "FAILED");

  rclcpp::shutdown();
  spinner.join();
  return ok ? 0 : 1;
}
