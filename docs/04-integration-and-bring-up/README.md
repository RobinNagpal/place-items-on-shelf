# Layer 4 — Integration and Bring-up

You finished Layer 3 with a software bill of materials. Now you actually
**glue everything together and get it running.** That's this layer.

Layer 4 is where most robotics projects die. The hardware was bought,
the software was picked, the demo worked once — and then it never
ran reliably again. The chapters below exist to keep your project out
of that pile.

**This layer is about workflows, not products.** Layer 2 told you *which*
arm. Layer 3 told you *which* simulator. Layer 4 tells you *what order
to do things in* to go from "boxes on a shelf" to "the cell runs
unattended for a week and we trust it."

## How this layer is organised

Some chapters in this layer are single files — they're checklists or
short recipes. Others have **many steps** and split into
sub-files: `01-a`, `01-b`, etc. The letter suffix means "this is one
step inside a longer workflow."

The four big multi-step workflows are:

1. **`01-*` — Simulation-first development.** You pick an arm and a
   simulator. Before you touch real hardware, you make the *virtual*
   version of the cell run end-to-end. Six steps: install the sim,
   build the virtual cell, bring up MoveIt, write a scripted task,
   fake the perception, stress-test.
2. **`02-*` — From simulation to real.** Five steps for crossing the
   sim-to-real gap without breaking anything: shared URDF + frames,
   `ros2_control` driver swap, hand-eye calibration, shadow mode +
   slow speeds, phased rollout.
3. **`04-*` — Imitation learning workflow.** Six steps for collecting
   teleop demos and training a policy from them: pick teleop
   hardware, install + calibrate leader-follower, record demos,
   curate, fine-tune, evaluate.
4. **`05`–`10`** — Single-file chapters covering bring-up checklists,
   pilot deployment, acceptance tests, safety validation, operator
   runbooks, and Day-2 monitoring.

## Read these in order

1. **[01-a-choose-and-install-simulator.md](01-a-choose-and-install-simulator.md)**
2. **[01-b-build-the-virtual-cell.md](01-b-build-the-virtual-cell.md)**
3. **[01-c-bring-up-moveit-in-sim.md](01-c-bring-up-moveit-in-sim.md)**
4. **[01-d-scripted-first-task.md](01-d-scripted-first-task.md)**
5. **[01-e-fake-perception-in-sim.md](01-e-fake-perception-in-sim.md)**
6. **[01-f-stress-test-in-sim.md](01-f-stress-test-in-sim.md)**
7. **[02-a-shared-urdf-and-frames.md](02-a-shared-urdf-and-frames.md)**
8. **[02-b-ros2-control-driver-swap.md](02-b-ros2-control-driver-swap.md)**
9. **[02-c-hand-eye-and-base-calibration.md](02-c-hand-eye-and-base-calibration.md)**
10. **[02-d-shadow-mode-and-slow-speeds.md](02-d-shadow-mode-and-slow-speeds.md)**
11. **[02-e-phased-rollout.md](02-e-phased-rollout.md)**
12. **[03-system-integration-on-real.md](03-system-integration-on-real.md)**
13. **[04-a-pick-teleop-hardware.md](04-a-pick-teleop-hardware.md)**
14. **[04-b-install-and-calibrate-leader-follower.md](04-b-install-and-calibrate-leader-follower.md)**
15. **[04-c-record-demos.md](04-c-record-demos.md)**
16. **[04-d-curate-and-clean-dataset.md](04-d-curate-and-clean-dataset.md)**
17. **[04-e-pick-and-fine-tune-policy.md](04-e-pick-and-fine-tune-policy.md)**
18. **[04-f-evaluate-and-iterate.md](04-f-evaluate-and-iterate.md)**
19. **[05-bring-up-checklist.md](05-bring-up-checklist.md)**
20. **[06-pilot-deployment.md](06-pilot-deployment.md)**
21. **[07-acceptance-tests.md](07-acceptance-tests.md)**
22. **[08-safety-validation.md](08-safety-validation.md)**
23. **[09-runbooks-and-operator-training.md](09-runbooks-and-operator-training.md)**
24. **[10-monitoring-and-incident-response.md](10-monitoring-and-incident-response.md)**

## When to skip ahead

The reading order above is the "starting from scratch" order. If you're
already partway through, jump in where you are:

- **No simulation yet?** → Start at `01-a`.
- **Sim works, never touched real?** → Start at `02-a`.
- **Real hardware boots but you've never run a task?** → Start at
  `03`.
- **You don't need a learned policy?** → Skip the `04-*` chapter.
- **You need a learned policy and don't know where to start?** → Read
  `04-a` after you've finished `02-*`.
- **Production cell, ramping up?** → Start at `05` and read through `10`.

## What you leave this layer with

- A **virtual version** of the cell that runs end-to-end in sim.
- A **real cell** that's been brought up, calibrated, and tested.
- A **bring-up record**: which calibrations were done, what their
  errors were, who signed off.
- A **pilot deployment plan**: shadow → supervised → unattended.
- An **acceptance test report** that says the cell meets Layer-1
  requirements.
- A **safety case** appropriate for who will be near the robot.
- **Operator runbooks** and a Day-2 monitoring setup.

Together with Layers 1–3, this is the full picture of a working
robot cell: what it must do, what metal does it, what software runs
on the metal, and the workflow that turned all of that into something
you can ship.

## What this layer is not

- **Not a textbook on ROS 2 / MoveIt / LeRobot.** We point at the
  tools; we don't teach their APIs. Read the upstream docs after this.
- **Not a substitute for a robotics integrator** when the cell is
  large or safety-critical. A trained integrator does this for a
  living; these docs help you talk to them.
- **Not exhaustive.** Each chapter is the 80% you actually need; the
  last 20% lives in the upstream library, the vendor manual, and
  hard-won experience.

## What's next (later, if at all)

Layer 5 (operations / fleet) and Layer 6 (continuous improvement) are
*not* in scope right now. They only become useful once a single cell
is rock-solid. Get there first.
