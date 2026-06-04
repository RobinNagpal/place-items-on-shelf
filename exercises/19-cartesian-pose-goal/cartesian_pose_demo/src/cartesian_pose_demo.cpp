// cartesian_pose_demo.cpp
//
// Cartesian pose "hello world" for the myCobot 280 in the HPLC
// autosampler cell. Implements checklist item 19 (autosampler tie-in)
// from docs/learning-checklist.md.
//
// What it does:
//   We hand MoveIt four (x, y, z, roll, pitch, yaw) targets in the
//   arm's base_link frame and let its IK solver (KDL) figure out the
//   joint angles. The four targets mimic the inner loop of an
//   autosampler vial transfer:
//
//     above_source  -> descend_source  -> lift_source  -> above_tray
//
//   This is the same Cartesian-goal pattern used in real production
//   cells; only the "open / close gripper" steps are missing (those
//   come from exercises 17 and 21).
//
// We do NOT define a new world here. The scene this exercise targets is
//   ../../../01-custom-gazebo-world/worlds/autosampler_cell.sdf
// The arm base is mounted at world (-0.18, 0, 0.775) on top of the
// bench, so every target below is expressed in the arm's base_link
// frame (world_x + 0.18, world_y, world_z - 0.775).
//
// "Done when" check (from the checklist): the end-effector arrives
// within 5 mm and 2 deg of each requested pose. We measure and log
// the error after each execute.

#include <chrono>
#include <cmath>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <rclcpp/rclcpp.hpp>
#include <tf2/LinearMath/Quaternion.h>

using moveit::planning_interface::MoveGroupInterface;
using namespace std::chrono_literals;

namespace
{
// Names from upstream addison's SRDF.
constexpr char kArmGroup[] = "arm";
constexpr char kTipLink[]  = "link6_flange";   // end-effector link
constexpr char kBaseLink[] = "base_link";      // planning frame

// "Done when" tolerances from checklist item 19.
constexpr double kPosTolM   = 0.005;   // 5 mm
constexpr double kOrientTolRad = 2.0 * M_PI / 180.0;  // 2 degrees

// A single Cartesian goal in the arm's base_link frame.
//
// Roll = pi gives "gripper facing down" - the flange's local +Z axis
// (which is "out of the tool") ends up pointing along world -Z, which
// is what we want when we're hovering above a vial cap.
struct PoseGoal {
  std::string name;
  double x, y, z;            // metres in base_link frame
  double roll, pitch, yaw;   // radians, ZYX intrinsic
};

geometry_msgs::msg::Pose make_pose(const PoseGoal & g)
{
  tf2::Quaternion q;
  q.setRPY(g.roll, g.pitch, g.yaw);

  geometry_msgs::msg::Pose p;
  p.position.x = g.x;
  p.position.y = g.y;
  p.position.z = g.z;
  p.orientation.x = q.x();
  p.orientation.y = q.y();
  p.orientation.z = q.z();
  p.orientation.w = q.w();
  return p;
}

// Angle (rad) between two quaternions. Used to check the "2 deg"
// orientation tolerance after execute.
double quat_angle(const geometry_msgs::msg::Quaternion & a,
                  const geometry_msgs::msg::Quaternion & b)
{
  // dot product, abs for double-cover, clamp to [-1, 1] before acos.
  const double dot = std::abs(a.x*b.x + a.y*b.y + a.z*b.z + a.w*b.w);
  return 2.0 * std::acos(std::min(1.0, dot));
}

bool go_to(MoveGroupInterface & arm, const PoseGoal & goal,
           const rclcpp::Logger & logger)
{
  RCLCPP_INFO(logger, "Planning to '%s' (%.3f, %.3f, %.3f).",
              goal.name.c_str(), goal.x, goal.y, goal.z);

  // 1. Start from where the arm actually is right now.
  arm.setStartStateToCurrentState();

  // 2. Hand MoveIt the goal pose. setPoseTarget runs IK internally
  //    via the kinematics_solver named in kinematics.yaml (KDL here).
  geometry_msgs::msg::PoseStamped target;
  target.header.frame_id = kBaseLink;
  target.pose = make_pose(goal);
  arm.setPoseTarget(target, kTipLink);

  // 3. Plan + execute.
  MoveGroupInterface::Plan plan;
  if (arm.plan(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "Planning to '%s' failed (likely IK or reach).",
                 goal.name.c_str());
    return false;
  }
  if (arm.execute(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "Execute on '%s' failed.", goal.name.c_str());
    return false;
  }

  // 4. Measure error vs the requested pose. Done-when check.
  const auto reached = arm.getCurrentPose(kTipLink).pose;
  const double dx = reached.position.x - goal.x;
  const double dy = reached.position.y - goal.y;
  const double dz = reached.position.z - goal.z;
  const double pos_err = std::sqrt(dx*dx + dy*dy + dz*dz);
  const double ori_err = quat_angle(reached.orientation, target.pose.orientation);

  RCLCPP_INFO(logger, "'%s' reached: pos_err=%.4f m, ori_err=%.3f deg.",
              goal.name.c_str(), pos_err, ori_err * 180.0 / M_PI);

  const bool within_tol = pos_err <= kPosTolM && ori_err <= kOrientTolRad;
  if (!within_tol) {
    RCLCPP_WARN(logger, "'%s' outside tolerance (>5 mm or >2 deg).",
                goal.name.c_str());
  }
  return within_tol;
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
    "cartesian_pose_demo",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto logger = node->get_logger();

  // Same spin pattern as exercise 18 - MoveGroupInterface needs a
  // running executor so its subscriptions to /joint_states and /tf
  // stay alive.
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spinner([&executor]() { executor.spin(); });

  MoveGroupInterface arm(node, kArmGroup);
  arm.setPlanningPipelineId("ompl");
  arm.setPlannerId("RRTConnectkConfigDefault");
  arm.setPlanningTime(3.0);              // 3 s: IK can take a moment
  arm.setNumPlanningAttempts(5);         // OMPL + IK is non-deterministic
  arm.setGoalPositionTolerance(0.001);   // 1 mm goal slop in the planner
  arm.setGoalOrientationTolerance(0.01); // ~0.6 deg goal slop
  arm.setMaxVelocityScalingFactor(0.3);
  arm.setMaxAccelerationScalingFactor(0.3);

  // Wait for move_group + first /joint_states message to land.
  std::this_thread::sleep_for(2s);

  // ---------------------------------------------------------------
  // The four Cartesian targets, expressed in the arm's base_link
  // frame. All sit comfortably inside the 280 mm reach envelope.
  //
  //   Arm base is at world (-0.18, 0, 0.775) (see SDF). To convert a
  //   world pose into the base_link frame: subtract that origin from
  //   the world coordinates.
  //
  //   Source rack center  : world (0.05, +0.12, 0.825) -> base (0.23, +0.12, 0.050)
  //   Tray center         : world (0.05, -0.12, 0.810) -> base (0.23, -0.12, 0.035)
  //
  //   The corners we hover above are picked closer to the arm to keep
  //   IK happy. 5 cm hover height clears any vial cap.
  // ---------------------------------------------------------------
  const std::vector<PoseGoal> goals = {
    // 5 cm above the source-rack corner nearest the arm.
    {"above_source",   0.185, +0.030, 0.090,  M_PI, 0, 0},
    // Descend to ~2 cm above the rack top (where a real grasp would happen).
    {"descend_source", 0.185, +0.030, 0.045,  M_PI, 0, 0},
    // Lift back to the hover height.
    {"lift_source",    0.185, +0.030, 0.090,  M_PI, 0, 0},
    // Cross over to the destination tray, 5 cm above the corner nearest the arm.
    {"above_tray",     0.185, -0.030, 0.090,  M_PI, 0, 0},
  };

  bool ok = true;
  for (const auto & g : goals) {
    ok = go_to(arm, g, logger) && ok;
  }

  RCLCPP_INFO(logger, "Sequence %s.", ok ? "OK (all goals within tol)" : "FAILED");

  rclcpp::shutdown();
  spinner.join();
  return ok ? 0 : 1;
}
