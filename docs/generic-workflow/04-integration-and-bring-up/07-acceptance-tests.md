# 07 — Acceptance Tests

The acceptance test is the **formal, agreed-in-advance** procedure
that says the cell does what Layer 1 said it should do. Pass it and
the cell is signed off. Fail it and the integrator owes the customer
work.

It's *not* the pilot. The pilot answers "does it hold up?". The
acceptance test answers "does it meet spec?".

## What you need before this step

- A pilot that passed ([06](06-pilot-deployment.md)).
- The Layer-1 task spec — concrete numbers.
- A stakeholder who will sign off.
- An hour or two of cell time uninterrupted.

## Two common test stages

In industry these have names:

- **FAT — Factory Acceptance Test.** Run at the integrator's site,
  before shipping to the customer. Verifies the cell does the task
  on representative samples.
- **SAT — Site Acceptance Test.** Run at the customer's site, after
  installation. Verifies the cell does the task **in its real
  environment** — real lighting, real conveyor, real parts.

If you're building one cell for yourself, just call them
"acceptance test" and "post-install retest." Same idea.

## What the test actually measures

Map each Layer-1 requirement to an acceptance criterion. Examples:

| Layer-1 requirement | Acceptance criterion |
|---------------------|----------------------|
| "Pick 200 parts/hour" | Cell completes ≥ 200 cycles in 60 min, observed |
| "Success rate ≥ 95%" | ≥ 95 / 100 cycles succeed across diverse part poses |
| "Recover from a missed grasp without human" | All 5 staged missed-grasp scenarios recovered automatically |
| "Run unattended overnight" | 8 h run with no human intervention, success ≥ 95% over the period |
| "Stop within 500 ms on e-stop" | Measured time-to-stop ≤ 500 ms, 3 trials |
| "Operate at 18–28 °C" | Cell runs ≥ 1 h at top of range with no thermal fault |

Each row becomes one numbered test in the test document.

## Design the test before running it

Write the test plan, get it signed, then run it. Don't make up the
plan as you measure.

The plan includes, per test:

- **What's being measured.**
- **Acceptance criterion** (the number).
- **Setup** — initial state of the cell.
- **Procedure** — exact steps the operator follows.
- **Measurement method** — stopwatch, rosbag, dashboard.
- **Pass / fail rule** — exact threshold.

If two of you can't read the plan and run the test the same way, the
plan isn't done yet.

## A pragmatic test suite

A small, real-world acceptance suite for a pick-and-place cell:

1. **Throughput.** Run cell for 60 min at production speed. Count
   successful cycles.
2. **Success rate, varied parts.** 100 cycles with parts spread
   across the work area. Tally successes.
3. **Edge-case manipulation.** 20 cycles with parts at the edge of
   reach. Tally.
4. **Missed-grasp recovery.** Deliberately offset 5 parts; the cell
   must retry and complete.
5. **Safety stop.** E-stop tested 3× in motion; measure time-to-stop.
6. **Resume from fault.** Simulate a fault (unplug a cable, briefly
   block the camera) and confirm the operator can resume without
   restarting the cell.
7. **Continuous run.** 8-hour run, unattended. Success rate over the
   period.
8. **Lighting / temperature variation** if the spec mentioned them.

Customise this list to your Layer-1 spec.

## Who's in the room

- **Integrator engineer** — operates the cell.
- **Customer engineer or stakeholder** — observes, signs.
- **Operator** — the one who'll use the cell daily. Watches.
- **Safety reviewer** — for any test involving safety devices.

If only one person signs the test, the test is weaker than it looks.

## What you bring

- The signed test plan.
- The cell, fully bring-up complete.
- A laptop showing the live dashboard.
- A timer / stopwatch.
- A camera to record runs (genuinely useful evidence later).
- Spare parts, in case a test damages something.

## Recording the result

For every test:

- Observed value (number).
- Pass / fail.
- Initial of the observer.
- Time of test.
- Rosbag / video file pointer.

Store the result in a single file (`acceptance_test_results.md` is
fine). Get it signed at the end.

## What happens on a fail

The test plan must specify, before the test, what counts as a
fail-and-stop vs. a fail-and-fix-now:

- **Hard fail** — a test that fails for safety, structural, or
  fundamental design reasons. Stop the test, do not continue.
- **Soft fail** — a tunable parameter is wrong (gripper closes
  late, lighting threshold off). Fix on the spot, re-run that test.

Don't keep running a fail-and-stop test "just to see." That's how
operators learn that paperwork doesn't really matter.

## Output of this step

```
Test plan signed off:        yes / no — date: ___
Test date:                   ___
Tests run:                   ___ / ___ in plan
Hard pass:                   ___
Soft pass (fixed-then-pass): ___
Hard fail:                   ___
Soft fail (now fixed):       ___
Sign-off:
  Integrator:                ___ (signature, date)
  Customer / stakeholder:    ___ (signature, date)
  Operator:                  ___ (signature, date)
  Safety reviewer:           ___ (signature, date) — for safety tests
Issues deferred to a punch list: ___
```

## Common mistakes

1. **No test plan.** Two engineers measure differently; nobody can
   agree if it passed.
2. **Test plan written *during* the test.** Same problem.
3. **One signer.** Acceptance needs at least the integrator + the
   stakeholder.
4. **No video record.** Three months later, someone disputes a
   result. No evidence.
5. **Including too many tests.** Aim for the 8–12 that map directly
   to Layer 1. Anything else belongs in regression tests.
6. **Skipping safety tests "because we already tested those."** Run
   them again, formally, with the safety reviewer present.

## What's next

Acceptance test passed. There's one more formal review before normal
operations: the safety case.

→ Next: [08-safety-validation.md](08-safety-validation.md)
