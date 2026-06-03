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
short recipes. Others have **many steps**, and each multi-step
workflow lives in **its own folder**. The folder name tells you what
the steps are about; the numbered files inside are the steps in
order.

The three multi-step workflow folders are:

1. **[`01-simulation-first-development/`](01-simulation-first-development/README.md)** —
   You pick an arm and a simulator. Before you touch real hardware,
   you make the *virtual* version of the cell run end-to-end. Six
   steps: install the sim, build the virtual cell, bring up MoveIt,
   write a scripted task, fake the perception, stress-test.
2. **[`02-sim-to-real-bridge/`](02-sim-to-real-bridge/README.md)** —
   Five steps for crossing the sim-to-real gap without breaking
   anything: shared URDF + frames, `ros2_control` driver swap,
   hand-eye calibration, shadow mode + slow speeds, phased rollout.
3. **[`04-imitation-learning-workflow/`](04-imitation-learning-workflow/README.md)** —
   Six steps for collecting teleop demos and training a policy from
   them: pick teleop hardware, install + calibrate leader-follower,
   record demos, curate, fine-tune, evaluate.

Plus single-file chapters at the top level — `03`, `05`–`10` —
covering on-real integration, the bring-up checklist, pilot
deployment, acceptance tests, safety validation, operator runbooks,
and Day-2 monitoring.

## Read these in order

Each folder has its own README that lists the steps inside; the
short version is below.

1. **[`01-simulation-first-development/`](01-simulation-first-development/README.md)** —
   six steps (`01`–`06`) inside.
2. **[`02-sim-to-real-bridge/`](02-sim-to-real-bridge/README.md)** —
   five steps (`01`–`05`) inside.
3. **[03-system-integration-on-real.md](03-system-integration-on-real.md)**
4. **[`04-imitation-learning-workflow/`](04-imitation-learning-workflow/README.md)** —
   six steps (`01`–`06`) inside (optional — only if you need a
   learned policy).
5. **[05-bring-up-checklist.md](05-bring-up-checklist.md)**
6. **[06-pilot-deployment.md](06-pilot-deployment.md)**
7. **[07-acceptance-tests.md](07-acceptance-tests.md)**
8. **[08-safety-validation.md](08-safety-validation.md)**
9. **[09-runbooks-and-operator-training.md](09-runbooks-and-operator-training.md)**
10. **[10-monitoring-and-incident-response.md](10-monitoring-and-incident-response.md)**

## When to skip ahead

The reading order above is the "starting from scratch" order. If you're
already partway through, jump in where you are:

- **No simulation yet?** → Start in
  [`01-simulation-first-development/`](01-simulation-first-development/README.md).
- **Sim works, never touched real?** → Start in
  [`02-sim-to-real-bridge/`](02-sim-to-real-bridge/README.md).
- **Real hardware boots but you've never run a task?** → Start at
  [`03-system-integration-on-real.md`](03-system-integration-on-real.md).
- **You don't need a learned policy?** → Skip the
  [`04-imitation-learning-workflow/`](04-imitation-learning-workflow/README.md)
  folder.
- **You need a learned policy and don't know where to start?** → Read
  [`04-imitation-learning-workflow/`](04-imitation-learning-workflow/README.md)
  after you've finished `02-sim-to-real-bridge/`.
- **Production cell, ramping up?** → Start at `05` and read through
  `10`.

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
