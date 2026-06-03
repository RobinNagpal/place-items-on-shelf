# Contributing

This is a small, early-stage project. The conventions below are the ones that
exist today — they will grow as the repo does. If something here gets in your
way, file an issue or open a PR to update this document.

## Before you start

- Skim [`CLAUDE.md`](CLAUDE.md) at the repo root for the project's high-level
  shape and conventions.
- Read the doc section relevant to whatever you're touching:
  - Robot-specific work → start at
    [`robots/mycobot-280-pi/docs/README.md`](robots/mycobot-280-pi/docs/README.md).
  - Robot-agnostic concepts → start at [`docs/README.md`](docs/README.md).

  The existing docs already capture the subtle gotchas (controller-name typos,
  world-file edits, `execute: true`); duplicating that investigation in a fresh
  PR wastes time.

## Setting up a development environment

The full setup is documented in
[`robots/mycobot-280-pi/docs/setup/`](robots/mycobot-280-pi/docs/setup/). One-line
summary:

1. Ubuntu 24.04 + ROS 2 Jazzy + the apt deps in
   [`setup/01-system-prereqs.md`](robots/mycobot-280-pi/docs/setup/01-system-prereqs.md).
2. Create `~/ros2_ws`, clone addison's `mycobot_ros2` into `src/`, then clone
   this repo into the same `src/`.
3. `colcon build --symlink-install` from `~/ros2_ws`.

You should be able to run
`ros2 launch cobot280_moveit_task move_to_named_pose.launch.py` end-to-end
before you start changing things.

## Branch and PR workflow

- **Branch from `main`.** Use short kebab-case names that describe the change:
  `add-project-documentation`, `cobot280-moveit-task`, `restructure-docs`.
- **One PR, one focused change.** If you find yourself bundling a doc rewrite
  with a code fix and a build-system change, split them.
- **PR title:** under ~70 characters, imperative voice ("Add setup section",
  not "Added a setup section").
- **PR description:** explain the *why*. The *what* is in the diff.
- **Merge to `main` via the GitHub UI** once review is complete. Don't push
  directly to `main`.

## Code conventions

Until a formal style guide exists, follow what the surrounding code does. A few
specifics worth calling out:

- **C++** — C++17, `snake_case` for variables and functions, `kCamelCase` for
  constants (matching [`cobot280_moveit_task/src/move_to_named_pose.cpp`](robots/mycobot-280-pi/cobot280_moveit_task/src/move_to_named_pose.cpp)).
  Compiler warnings stay enabled (`-Wall -Wextra -Wpedantic`); don't introduce
  new ones.
- **Python launch files** — PEP 8, four-space indent. Top-of-file docstring
  explaining what the launch starts and what it depends on (see
  [`cobot280_moveit_task/launch/move_to_named_pose.launch.py`](robots/mycobot-280-pi/cobot280_moveit_task/launch/move_to_named_pose.launch.py)).
- **Comments** — explain *why* something is the way it is when the *what* isn't
  obvious from the code. Don't restate what the next line plainly says.

## Documentation conventions

Docs in this repo are written for **someone new to ROS 2 robotics who wants to
understand the whole pipeline**. A few rules of thumb that the existing pages
follow and new ones should too:

- **Plain English, then jargon.** Introduce the concept in everyday words first;
  the precise term comes after, often parenthetically.
- **One topic per file.** If you find yourself adding a second top-level heading
  to a page, that's probably a second file.
- **Pick the right tree.** Robot-agnostic concept docs go under top-level
  `docs/`. Robot-specific docs (concrete commands, exact logs, gotchas tied to a
  particular setup) go under `robots/<model>/docs/`. Don't mix.
- **Group by purpose, not by date.** Place new robot-specific docs in the right
  section (`setup/`, `concepts/`, `deep-dives/`, `recipes/`, `reference/`) and
  update the section's `README.md` index so the file is discoverable.
- **Add to the glossary.** Any new acronym or jargon term should get an entry
  in
  [`robots/mycobot-280-pi/docs/reference/glossary.md`](robots/mycobot-280-pi/docs/reference/glossary.md).
- **Code blocks should be runnable verbatim** (with the noted prerequisites).
  If a block needs a flag fixed before it works, say so right above it.
- **Cross-link liberally.** Use relative links to other docs. Each doc usually
  ends with a `→ Next:` arrow pointing to the next file in its reading order.

## Adding a new ROS package

If you're adding a package under `robots/<model>/`:

1. Place it next to the existing packages (`robots/<model>/<package_name>/`).
2. Make sure `package.xml`, `CMakeLists.txt`, and (if it has a launch file)
   `launch/` exist. Mirror the layout of `cobot280_moveit_task/`.
3. Add a short `README.md` inside the package with: what it does, how to build
   it, how to run it, and the troubleshooting list of "common ways it breaks".
4. Update the model's folder-level `README.md` (e.g.
   [`robots/mycobot-280-pi/README.md`](robots/mycobot-280-pi/README.md)) to
   mention the new package.

## Adding support for a new robot

1. Create `robots/<new-model>/` with the same shape as `robots/mycobot-280-pi/`
   (folder README, package subdirectories, `docs/` with the same five sections).
2. Update the top-level [`README.md`](README.md) to list the new robot.
3. Update [`CLAUDE.md`](CLAUDE.md) so AI agents discover the new folder.

## What *not* to put in a PR

- A `LICENSE` file. Licensing is a maintainer decision — ask first.
- An auto-generated `CHANGELOG.md`. We use git history and PR descriptions as
  the source of truth.
- New top-level tooling (CI workflows, lint configs, format runners) without
  prior discussion. These set conventions for every future package.

## Reporting issues

Open a GitHub issue with:

- What you did (the command, the doc you were following).
- What you expected.
- What actually happened (full log lines, not screenshots if possible).
- Your environment: OS, ROS distro, Gazebo version (`gz sim --version`).
