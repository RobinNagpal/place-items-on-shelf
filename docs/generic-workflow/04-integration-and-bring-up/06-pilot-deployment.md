# 06 — Pilot Deployment

The cell is bring-up complete. The checklist is signed. Now it
operates **for someone other than the people who built it**, on
**real work**, for the **first time**.

That's the pilot. It's the bridge between "we proved it works" and
"we trust it." The phased rollout from
[02-sim-to-real-bridge/05](02-sim-to-real-bridge/05-phased-rollout.md) is the *operational* protocol; this
file covers the *business* side of the pilot — stakeholders,
duration, exit criteria.

## What you need before this step

- A cell that passed bring-up
  ([05](05-bring-up-checklist.md)).
- A pilot **partner** — the team, line, or customer whose real work
  the cell will do.
- Their **commitment**: time, space, a person to interact with the
  cell daily.

## What "pilot" actually means

A pilot is **not a demo**. A demo runs once and tells you nothing.
A pilot runs for days or weeks with a real human relying on the
output, and tells you:

- Does the cell hold up under continuous use?
- Does the operator's experience match what we promised?
- Do edge cases we didn't simulate appear?
- Are the failure modes acceptable?
- Does the data we're collecting actually answer the business
  question?

## Define success before you start

Before turning anything on, write down — with the pilot partner —
what "pilot succeeded" looks like:

- **Throughput target.** Cycles per hour. Realistic, not aspirational.
- **Success rate target.** Often 90–99% depending on Layer 1.
- **Uptime target.** Hours per day of trouble-free operation.
- **MTBF / MTTR targets.** Mean time between failures, mean time to
  recover.
- **Operator effort budget.** How many minutes per day of touch-up
  is acceptable?

Get this in writing before pilot day one. After-the-fact targets
turn into arguments.

## Choose a pilot scope, not "full production"

Common pilot scopes, in order of risk:

1. **One specific work order or product variant.** Lowest risk.
2. **One shift per day** (e.g. day shift only).
3. **One station** in a multi-station line.
4. **One operator** at a time.
5. **Full production** — only after 1–4 have passed.

Aim for scope **1 or 2** for the first pilot. A failed pilot at scope
5 wastes a quarter; a failed pilot at scope 1 costs a day.

## Duration

Rules of thumb:

- **At least 1 week**, calendar time.
- **At least 500 cycles**, real work.
- **At least one full work day end-to-end** without a robotics
  engineer touching the cell.
- **Include at least one weekend or evening run** to catch
  scheduling / cooling / time-of-day issues.

Shorter pilots miss the slow-drift problems (lens dust, vibration
loosening bolts, lighting changes across the day).

## What you instrument during the pilot

The Layer-3 logging stack
([`../03-software-stack/09-data-logging-and-observability.md`](../03-software-stack/09-data-logging-and-observability.md))
should already be on. During the pilot, you watch:

- **Live dashboard** of success rate, cycle time, last error.
- **Alert channel** (Slack / email / SMS) for safety stops and
  multi-minute outages.
- **Daily summary** at end of shift — auto-generated, sent to the
  whole pilot team.
- **Failure-mode tally**, growing.

If you don't have those running, [10](10-monitoring-and-incident-response.md)
covers the minimum.

## A daily ritual

Every day during the pilot:

1. **Morning check.** Robotics engineer reads yesterday's log,
   reviews any incidents, decides if pilot continues.
2. **Operator standup (5 min).** "How did it feel? Anything weird?"
3. **The cell runs.**
4. **End-of-shift summary.** Cycles run, success rate, incidents,
   open items.
5. **Triage** — anything that needs fixing before tomorrow gets
   queued.

Lock the ritual on day one. Skipping a day is how pilots silently
fail.

## Stop-loss criteria

Pre-agree the conditions under which the pilot stops:

- Severe safety event → stop, investigate, restart from
  [05](05-bring-up-checklist.md).
- Two consecutive days under success-rate target → stop, root-cause,
  schedule a fix.
- Operator reports the cell is "unusable in practice" → stop,
  re-evaluate the operator experience.

Without stop-loss, pilots drag on, blame accumulates, the project
loses credibility.

## Exit criteria — pilot to production

The pilot ends with a written decision:

- **Pass.** Targets met. Cell promoted to wider scope.
- **Pass with conditions.** Targets met but specific issues must be
  fixed before promotion (e.g. "needs better lighting", "needs
  operator training v2").
- **Pause and iterate.** Targets not met. Identify what to fix and
  run pilot v2.
- **Fail.** Targets not met and the gap is structural. Re-scope.

Whichever happens, write the decision in the same doc that holds the
targets. Future you needs to remember why.

## Output of this step

```
Pilot scope:                  ___
Pilot start / end dates:      ___ / ___
Stakeholder partner(s):       ___
Daily ritual lead:            ___
Success criteria (target → actual):
  Throughput:                 ___ → ___
  Success rate:               ___ → ___
  Uptime / day:               ___ → ___
  MTBF:                        ___ → ___
  MTTR:                        ___ → ___
  Operator touch time / day:  ___ → ___
Incidents (severe / minor):   ___ / ___
Pilot decision:               pass / pass-with-conditions / pause / fail
Next step:                    ___
```

## Common mistakes

1. **No written targets.** You'll argue about whether the pilot
   succeeded for weeks afterward.
2. **Pilot scope too wide.** "Full production day one" is a recipe
   for spectacular failure.
3. **No daily ritual.** Two-week pilot becomes two weeks of "we
   didn't notice that broke."
4. **No stop-loss.** Pilots drag.
5. **Treating the pilot as a demo.** Demos run once; pilots run
   continuously.
6. **No operator standup.** The operator sees things you don't.
   They're your most important data source.

## What's next

Pilot passed. The cell needs a **formal acceptance test** before it's
signed off for normal operations.

→ Next: [07-acceptance-tests.md](07-acceptance-tests.md)
