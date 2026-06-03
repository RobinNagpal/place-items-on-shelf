# 02-e — Phased Rollout

The cell runs reliably under direct supervision. The point of this
step is to **move that confidence forward in stages** until you're
willing to let it run unattended.

Skipping phases is how cells silently break. Each phase filters out a
different class of failure.

## What you need before this step

- A cell that passes the slow/normal-speed bring-up in
  [step 4](04-shadow-mode-and-slow-speeds.md).
- A clear definition of **"success"** for one pick. This usually
  comes from your Layer-1 task spec, but if it didn't, write it now:
  - The object ended in the correct location, oriented correctly,
    undamaged.
  - The cycle completed within the time budget.
  - No safety stop or operator intervention was needed.
- An **incident log** — a simple shared doc where you record every
  unexpected event and what was done about it.

## The four phases

Each phase has an **entry criterion** (what passed before), a
**duration** (how long you run in this state), and an **exit
criterion** (what must be true to advance).

| Phase | Code | Arm motion | Operator | Duration | Exit |
|-------|------|-----------|----------|----------|------|
| **1. Supervised** | full | yes | hand on e-stop | 1 working day or ≥ 100 cycles | ≥ 95% success, 0 safety stops, all incidents logged & resolved |
| **2. Attended** | full | yes | nearby, alert | 2 working days or ≥ 500 cycles | ≥ 95% success, ≤ 2 minor incidents, no severe |
| **3. Periodically checked** | full | yes | checks every ~30 min | 1 week or ≥ 2000 cycles | ≥ 95% success, no severe incidents, mean-time-to-recover < 5 min |
| **4. Unattended** | full | yes | no human present | ongoing | continuous monitoring (see [10](10-monitoring-and-incident-response.md)) |

The exact numbers depend on your cycle time and risk tolerance — tune
them to Layer 1's "how often does it run" and "what happens if it
fails" answers.

## What "success rate" actually means

Be honest about what you count:

- **Cycle success** — the pick + place actually completed and the
  object is where it should be. *Not* "the code didn't crash."
- **Soft failures** — the cell *retried* and succeeded eventually.
  Count these. A 95% first-try rate is different from a 95% with-
  retry rate.
- **Operator interventions** — every "I just nudged the object" or
  "I restarted the launch file" counts as a failure.

The number you publish at the end of each phase is **(successful
cycles) / (total attempts)** with retries called out separately.

## How to record incidents

A two-line entry per event:

```
2026-06-04 14:22 — pick failed on cup at edge of reach. Code returned to HOME, retried, succeeded.
Cause: object pose at edge of reachable workspace. Action: shrink reachable region in task code by 20 mm.
```

After each phase, group incidents by **root cause**. If two incidents
share a cause, fix the cause once — don't tally them as two.

## Going backwards is normal

If a phase finds a new failure mode you can't fix on the spot, **drop
back one phase**. Don't push forward to hit the date.

Example: in Phase 3 (periodic checks), a network hiccup causes a hang
that nobody saw for 20 minutes. You don't push to Phase 4 with "we'll
fix it later." You go back to Phase 2, add a watchdog and a Slack
alert, and re-run Phase 2 until it's clean.

## The role of monitoring during rollout

By Phase 3 you need basic monitoring already in place:

- **A live dashboard** with success rate, cycle time, last error.
- **Alerts** on Slack / email / SMS for any safety stop or any
  > 5-minute outage.
- **Daily summary** auto-generated from the rosbag / log files.

The full setup lives in
[10-monitoring-and-incident-response.md](10-monitoring-and-incident-response.md);
have the basics running before Phase 3 starts.

## Exit criteria — what "done" looks like

A cell is ready for unattended operation when:

- **≥ 95% cycle success** at full speed over ≥ 2000 cycles.
- **No severe safety incident** in the last 1000 cycles.
- **All incident root causes** are either fixed, mitigated, or
  formally accepted as "won't fix" with operator awareness.
- **Operator runbook** ([09](09-runbooks-and-operator-training.md)) is
  written and the actual operator has read it.
- **Monitoring + alerting** ([10](10-monitoring-and-incident-response.md))
  is live and tested (you've fired a fake alert at least once).
- **Safety case** ([08](08-safety-validation.md)) signed off.

If any of those is missing, the cell isn't unattended-ready — it's
just *temporarily quiet*.

## Output of this step

```
Phase 1 (Supervised):
  Cycles: ___ | Success: ___ % | Incidents: ___
Phase 2 (Attended):
  Cycles: ___ | Success: ___ % | Incidents: ___
Phase 3 (Periodic checks):
  Cycles: ___ | Success: ___ % | Incidents: ___ | MTTR: ___ min
Phase 4 (Unattended):
  Started date: ___ | Monitoring URL: ___
Incident log path:                 ___
Severe incidents to-date:          ___
Sign-off date for unattended ops:  ___
```

## Common mistakes

1. **Skipping phases to hit a deadline.** The phases catch different
   bugs. Skipping is borrowing time you'll repay with interest.
2. **Counting "code didn't crash" as success.** Define cycle success
   in terms of the *object*, not the *process*.
3. **No incident log.** Memory of last week's bug fades. Write it
   down.
4. **Tally without root cause.** Twenty incidents with the same root
   cause is one bug, not twenty data points.
5. **Going to unattended without monitoring.** Unattended = nobody
   sees the failures. Monitoring is *the* substitute.
6. **Treating unattended as "done."** Cells drift. Camera lens gets
   dusty, friction changes, calibration shifts. Schedule re-checks.

## What's next

Sim and real now run the same code, calibrated, supervised, ramped.
There's one more piece of "real world" stuff you must handle once,
on real hardware only: the physical bring-up — wiring, power, the
literal first-boot of the cell.

→ Next: [03-system-integration-on-real.md](../03-system-integration-on-real.md)
