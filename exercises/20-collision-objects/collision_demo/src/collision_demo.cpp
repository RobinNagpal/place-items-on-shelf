// collision_demo.cpp
//
// Collision objects in the MoveIt planning scene. Implements checklist
// item 20 (autosampler tie-in) from docs/learning-checklist.md.
//
// WHAT THIS DOES
//
// 1. We add four obstacles to MoveIt's planning scene:
//      - bench_top                 (so the arm can't dive below the bench)
//      - source_rack               (the 5x10 rack body)
//      - tray                      (the destination tray plate)
//      - autosampler_housing_wall  (the back wall, visible in v2.sdf)
//      - no_fly_a1                 (a cylinder above vial_a1's cap,
//                                   marking the "already loaded" slot)
//
//    Each of these has a matching SHAPE in
//    ../worlds/autosampler_cell_v2.sdf so what you see in Gazebo
//    matches what the planner is reasoning about.
//
// 2. We run TWO Cartesian goals to show both halves of the behaviour:
//
//    Goal A  - hover above vial_a3 (the green-cap one, in the middle
//              of the rack). The straight-line path between the arm's
//              current pose and this point would clip the housing
//              wall, so the planner has to BEND the path around it.
//              EXPECTED: succeeds; you can see the path route around
//              obstacles in RViz's "Planned Path" view.
//
//    Goal B  - descend onto vial_a1 (the red-cap one, the
//              already-loaded slot). The end-effector pose is INSIDE
//              the no_fly_a1 cylinder, so collision checking on the
//              goal state fails.
//              EXPECTED: fails. Planner reports no IK / no plan.
//
// Same launch / move_group / Gazebo flow as exercises 18 and 19.
// We do NOT define a new world tag in the SDF here, we just point
// the gazebo launch at autosampler_cell_v2.sdf instead of v1.

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
constexpr char kArmGroup[] = "arm";
constexpr char kTipLink[]  = "link6_flange";
constexpr char kBaseLink[] = "base_link";

// ---------- helpers to build collision objects ----------

// Build a BOX collision object in the planning frame (base_link).
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

// Build a vertical CYLINDER collision object in the planning frame.
moveit_msgs::msg::CollisionObject make_cylinder(
  const std::string & id, double cx, double cy, double cz,
  double radius, double height)
{
  moveit_msgs::msg::CollisionObject obj;
  obj.header.frame_id = kBaseLink;
  obj.id = id;

  shape_msgs::msg::SolidPrimitive prim;
  prim.type = prim.CYLINDER;
  // SolidPrimitive::CYLINDER order: [height, radius]
  prim.dimensions = {height, radius};

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

// ---------- helper to send a pose goal and report what happened ----------

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

enum class Expected { Success, Failure };

bool try_goal(MoveGroupInterface & arm, const std::string & name,
              const geometry_msgs::msg::Pose & pose, Expected expected,
              const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "Trying goal '%s' (%.3f, %.3f, %.3f). Expected: %s.",
              name.c_str(), pose.position.x, pose.position.y, pose.position.z,
              expected == Expected::Success ? "success (path bends around obstacles)"
                                            : "REFUSED (goal inside an obstacle)");

  arm.setStartStateToCurrentState();
  geometry_msgs::msg::PoseStamped target;
  target.header.frame_id = kBaseLink;
  target.pose = pose;
  arm.setPoseTarget(target, kTipLink);

  MoveGroupInterface::Plan plan;
  const bool planned =
    arm.plan(plan) == moveit::core::MoveItErrorCode::SUCCESS;

  if (expected == Expected::Success) {
    if (!planned) {
      RCLCPP_ERROR(logger, "  '%s' was supposed to succeed but planning FAILED.",
                   name.c_str());
      return false;
    }
    if (arm.execute(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
      RCLCPP_ERROR(logger, "  '%s' plan ok but execute FAILED.", name.c_str());
      return false;
    }
    RCLCPP_INFO(logger, "  '%s' OK - arm moved.", name.c_str());
    return true;
  }

  // expected == Failure
  if (planned) {
    RCLCPP_ERROR(logger, "  '%s' was supposed to be REFUSED but plan succeeded.",
                 name.c_str());
    return false;
  }
  RCLCPP_INFO(logger, "  '%s' correctly REFUSED by planner.", name.c_str());
  return true;
}
}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "collision_demo",
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

  // Wait for move_group + first /joint_states.
  std::this_thread::sleep_for(2s);

  // -------------------------------------------------------------
  // 1. Push the obstacles into MoveIt's planning scene.
  //
  // Positions below are in the arm's base_link frame. The arm base is
  // mounted at world (-0.18, 0, 0.775); subtract that origin to go
  // from world coords to base_link coords (see exercise 19 README for
  // the full conversion).
  // -------------------------------------------------------------
  PlanningSceneInterface scene;

  std::vector<moveit_msgs::msg::CollisionObject> obstacles;

  // Bench top: a thin slab right at z=0 in base_link (= world z=0.775).
  // Pulled 5 mm below so it doesn't touch base_link itself.
  obstacles.push_back(make_box("bench_top",
    /* center */ 0.18, 0.0, -0.030,
    /* size   */ 0.60, 0.40, 0.005));

  // Source rack: world (0.05, 0.12, 0.825) -> base (0.23, 0.12, 0.050).
  obstacles.push_back(make_box("source_rack",
    0.23, +0.12, 0.050,
    0.09, 0.18, 0.05));

  // Destination tray + alignment plate together as one box.
  // world (0.05, -0.12, 0.795) -> base (0.23, -0.12, 0.020).
  obstacles.push_back(make_box("tray_block",
    0.23, -0.12, 0.020,
    0.16, 0.16, 0.03));

  // Housing back wall: world (0, 0.23, 0.975) -> base (0.18, 0.23, 0.20).
  obstacles.push_back(make_box("autosampler_housing_wall",
    0.18, 0.23, 0.20,
    0.60, 0.02, 0.40));

  // No-fly cylinder above vial_a1: world (-0.018, 0.160, 0.905) ->
  // base (0.162, 0.160, 0.130). Radius 2 cm, height 10 cm.
  obstacles.push_back(make_cylinder("no_fly_a1",
    0.162, 0.160, 0.130,
    /* radius */ 0.02, /* height */ 0.10));

  scene.applyCollisionObjects(obstacles);
  RCLCPP_INFO(logger, "Added %zu collision objects to the planning scene.",
              obstacles.size());
  // Give the planning scene monitor a moment to update.
  std::this_thread::sleep_for(500ms);

  // -------------------------------------------------------------
  // 2. Two demo goals.
  //
  //   Goal A: hover above vial_a3 (green cap, middle of rack).
  //           Straight-line from "home" would clip the housing wall;
  //           the planner has to swing around it.
  //
  //           vial_a3 world = (0.000, 0.160, 0.841 + cap)
  //           hover 5 cm above = world (0, 0.160, 0.895)
  //                            = base (0.18, 0.160, 0.120).
  //
  //   Goal B: descend onto vial_a1 (red cap, already-loaded slot).
  //           Goal pose is INSIDE the no_fly_a1 cylinder -> refused.
  //
  //           vial_a1 world = (-0.018, 0.160), cap top z = 0.855.
  //           descend to 1 cm above cap = world (-0.018, 0.160, 0.865)
  //                                     = base (0.162, 0.160, 0.090).
  //
  // Roll = pi for both ("gripper facing down" - see exercise 19).
  // -------------------------------------------------------------
  const auto goal_a = make_pose(0.180, +0.160, 0.120, M_PI, 0, 0);
  const auto goal_b = make_pose(0.162, +0.160, 0.090, M_PI, 0, 0);

  bool ok = true;
  ok &= try_goal(arm, "above_vial_a3 (route around housing)", goal_a,
                 Expected::Success, logger);
  ok &= try_goal(arm, "descend_onto_vial_a1 (into no_fly zone)", goal_b,
                 Expected::Failure, logger);

  RCLCPP_INFO(logger, "Demo %s.",
              ok ? "OK (Goal A succeeded, Goal B refused as expected)"
                 : "DID NOT MATCH EXPECTED BEHAVIOUR");

  rclcpp::shutdown();
  spinner.join();
  return ok ? 0 : 1;
}
