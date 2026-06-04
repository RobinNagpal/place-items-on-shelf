// pick_and_place_demo.cpp
//
// Hardcoded pick-and-place for one vial in the HPLC autosampler cell.
// Implements checklist item 21 (autosampler tie-in).
//
// "Hardcoded" means: every pose, every gripper command, and the
// order they happen in is BAKED INTO THE SOURCE FILE. There is no
// perception, no state machine, no planner intelligence above the
// motion-planning layer. A human picked the numbers; MoveIt does the
// motion in between them.
//
// This exercise mixes BOTH approaches from earlier exercises:
//   - exercise 18 (setNamedTarget): for the named SRDF states
//     "home" (arm group) and "open" / "closed" (gripper group).
//   - exercise 19 (setPoseTarget):  for the four mid-air target
//     points (above_pick, grasp, above_drop, release).
//   - exercise 20 (PlanningSceneInterface): bench + rack + tray +
//     housing wall are added as collision objects so the planner
//     refuses paths that pass through them.
//
// We do NOT actually grasp the vial in Gazebo. The gripper opens and
// closes at the right moments, but the simulated vial does not stick
// to the gripper - that requires AttachedCollisionObject + either a
// gazebo grasp plugin or a fixed_joint, which is intentionally out of
// scope for this "hardcoded sequence" exercise. The point is the
// SEQUENCE, not the grasping physics.

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
#include <rclcpp/rclcpp.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>
#include <tf2/LinearMath/Quaternion.h>

using moveit::planning_interface::MoveGroupInterface;
using moveit::planning_interface::PlanningSceneInterface;
using namespace std::chrono_literals;

namespace
{
constexpr char kArmGroup[]     = "arm";
constexpr char kGripperGroup[] = "gripper";
constexpr char kTipLink[]      = "link6_flange";
constexpr char kBaseLink[]     = "base_link";

// ---------- helpers (same shape as exercise 20) ----------

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

// Plan + execute a named SRDF state on whichever group is passed
// (works for the arm group AND the gripper group).
bool go_named(MoveGroupInterface & group, const std::string & name,
              const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "[named] %s -> '%s'", group.getName().c_str(), name.c_str());
  group.setStartStateToCurrentState();
  group.setNamedTarget(name);
  MoveGroupInterface::Plan plan;
  if (group.plan(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "  plan FAILED");
    return false;
  }
  return group.execute(plan) == moveit::core::MoveItErrorCode::SUCCESS;
}

// Plan + execute a Cartesian pose target on the arm group.
bool go_pose(MoveGroupInterface & arm, const std::string & label,
             double x, double y, double z,
             const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "[pose ] arm  -> %-12s (%.3f, %.3f, %.3f)",
              label.c_str(), x, y, z);
  arm.setStartStateToCurrentState();
  geometry_msgs::msg::PoseStamped t;
  t.header.frame_id = kBaseLink;
  t.pose = make_pose(x, y, z, M_PI, 0, 0);   // always gripper-down
  arm.setPoseTarget(t, kTipLink);
  MoveGroupInterface::Plan plan;
  if (arm.plan(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "  plan FAILED");
    return false;
  }
  return arm.execute(plan) == moveit::core::MoveItErrorCode::SUCCESS;
}
}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "pick_and_place_demo",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto logger = node->get_logger();

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() { executor.spin(); });

  // Two MoveGroupInterface handles - one for the arm chain, one for
  // the gripper joint. The "gripper" SRDF group has its own controller
  // (see addison's moveit_controllers.yaml), so this is the standard
  // way to drive gripper open / close from a high-level script.
  MoveGroupInterface arm(node, kArmGroup);
  MoveGroupInterface gripper(node, kGripperGroup);

  arm.setPlanningPipelineId("ompl");
  arm.setPlannerId("RRTConnectkConfigDefault");
  arm.setPlanningTime(3.0);
  arm.setNumPlanningAttempts(5);
  arm.setGoalPositionTolerance(0.001);
  arm.setGoalOrientationTolerance(0.01);
  arm.setMaxVelocityScalingFactor(0.3);
  arm.setMaxAccelerationScalingFactor(0.3);

  gripper.setPlanningTime(1.0);
  gripper.setMaxVelocityScalingFactor(0.5);

  std::this_thread::sleep_for(2s);

  // -------------------------------------------------------------
  // Collision objects - same as exercise 20 minus the no-fly
  // cylinder (because here we ARE picking from that slot).
  // -------------------------------------------------------------
  PlanningSceneInterface scene;
  std::vector<moveit_msgs::msg::CollisionObject> obstacles = {
    make_box("bench_top",                0.18,  0.00, -0.030, 0.60, 0.40, 0.005),
    make_box("source_rack",              0.23, +0.12,  0.050, 0.09, 0.18, 0.05),
    make_box("tray_block",               0.23, -0.12,  0.020, 0.16, 0.16, 0.03),
    make_box("autosampler_housing_wall", 0.18, +0.23,  0.20,  0.60, 0.02, 0.40),
  };
  scene.applyCollisionObjects(obstacles);
  RCLCPP_INFO(logger, "Added %zu collision objects.", obstacles.size());
  std::this_thread::sleep_for(500ms);

  // -------------------------------------------------------------
  // The 11-step hardcoded sequence.
  //
  // Coordinates are in the arm's base_link frame, picked to stay
  // comfortably inside the 280 mm reach envelope with the gripper-
  // down orientation (roll = pi).
  //
  //   "pick" side  : front of the source rack
  //   "drop" side  : front of the destination tray
  //   z = 0.130 m  : hover height (5 cm above well rim)
  //   z = 0.080 m  : "grasp / release" height (just above rim)
  //
  // Numbers are intentionally not tied to a specific vial pose -
  // the point of this exercise is to demonstrate the SEQUENCE and
  // mixing of approaches, not to land on a particular cap.
  // -------------------------------------------------------------
  constexpr double kHover = 0.130;
  constexpr double kWork  = 0.080;
  constexpr double kPickX = 0.180, kPickY = +0.120;
  constexpr double kDropX = 0.180, kDropY = -0.120;

  bool ok = true;

  //  1. Reset arm.
  ok &= go_named(arm, "home", logger);
  //  2. Open gripper so we can pick.
  ok &= go_named(gripper, "open", logger);

  //  3. Hover above the source well.
  ok &= go_pose(arm, "above_pick", kPickX, kPickY, kHover, logger);
  //  4. Descend to grasp height.
  ok &= go_pose(arm, "grasp",      kPickX, kPickY, kWork,  logger);
  //  5. Close gripper on the (imaginary) vial.
  ok &= go_named(gripper, "closed", logger);
  //  6. Lift back to hover.
  ok &= go_pose(arm, "lift_pick",  kPickX, kPickY, kHover, logger);

  //  7. Cross over to the destination at hover height.
  ok &= go_pose(arm, "above_drop", kDropX, kDropY, kHover, logger);
  //  8. Descend to release height.
  ok &= go_pose(arm, "release",    kDropX, kDropY, kWork,  logger);
  //  9. Open gripper to drop the vial.
  ok &= go_named(gripper, "open",  logger);
  // 10. Lift back to hover.
  ok &= go_pose(arm, "lift_drop",  kDropX, kDropY, kHover, logger);

  // 11. Return arm to home.
  ok &= go_named(arm, "home", logger);

  RCLCPP_INFO(logger, "Sequence %s.", ok ? "OK" : "FAILED");

  rclcpp::shutdown();
  spinner.join();
  return ok ? 0 : 1;
}
