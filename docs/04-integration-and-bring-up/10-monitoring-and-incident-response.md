# 10 — Monitoring and Incident Response

The cell is in operation. It will fail. Not "if" — "when." The
question is whether you find out **in time** to do something about
it, and whether the response is fast, calm, and consistent.

Monitoring tells you *when* the cell needs attention. Incident
response is *what you do* when it does. This file covers both.

## What you need before this step

- Trained operators ([09](09-runbooks-and-operator-training.md)).
- The Layer-3 logging stack
  ([`../03-software-stack/09-data-logging-and-observability.md`](../03-software-stack/09-data-logging-and-observability.md))
  installed and recording.
- A communication channel (Slack, email, SMS) the on-call person
  reads.

## What "monitoring" actually means

Three layers:

1. **Live dashboard** — a screen anyone can glance at to see the
   cell's current state.
2. **Alerting** — proactive notification when something is wrong.
3. **Daily summary** — a digest of what happened in the last 24 h.

You need all three.

## The metrics that matter

A short list. Track every one.

| Metric | Why it matters | Target |
|--------|----------------|--------|
| **Cycle success rate** | The headline KPI | ≥ Layer-1 target |
| **Cycle time (p50, p95)** | Throughput | Layer-1 target |
| **Up-time (% of shift cell is producing)** | Real availability | ≥ 95% typical |
| **Mean time to recover (MTTR)** | How quick the operator gets it back | < 5 min typical |
| **Mean time between failures (MTBF)** | How stable it is | Increases over time |
| **Safety stops / day** | Should be near zero | ≤ 1 / week |
| **CPU / GPU / disk / network on each box** | Resource health | Within nominal |
| **Calibration touch-test result** | Drift detector | Within tolerance |
| **Per-failure-mode counts** | Where time is going | Mix shifts over time |

## A reasonable dashboard

One panel each:

- Big number: cycles completed today / target.
- Big number: success rate today.
- Time-series: cycle time over the last week.
- Stacked bar: failure modes per day.
- Heat map: success rate by hour of day (catches "this fails after
  lunch" issues).
- Resource utilisation on each compute box.
- Last 10 incidents — timestamp, severity, action taken.

Build it on Grafana ([Layer 3's logging file](../03-software-stack/09-data-logging-and-observability.md)),
Foxglove, or a tiny custom web page. Doesn't matter which — matters
that it exists.

## Alerting that doesn't burn out the on-call

Two failure modes for alerting:

- **Too few alerts** — broken things go unnoticed.
- **Too many alerts** — on-call ignores Slack pings; real problem
  arrives, also gets ignored.

A pragmatic set:

| Alert | Channel | Severity |
|-------|---------|----------|
| Safety stop | SMS + Slack | sev-1 |
| Cell down > 5 min | SMS + Slack | sev-1 |
| Success rate < 80% over last 30 min | Slack | sev-2 |
| Detection / calibration drift > threshold | Slack | sev-2 |
| Disk usage > 80% on a logging box | Slack | sev-3 |
| Daily summary | Email | informational |

Test each one. Fire a fake alert. Make sure the right person receives
it. **An alert nobody receives is worse than no alert** — false
confidence.

## The incident response runbook

Specifically for **after-hours** or **unattended** incidents:

1. **Notification.** Page fires. Acknowledge within agreed SLA
   (typical: 15 minutes for sev-1, 1 hour for sev-2).
2. **Triage.** Open the dashboard. Read the last alert. Read the
   live log.
3. **Stop the bleeding.** If the cell is in a dangerous state, e-stop
   remotely (if you have remote access) or have the on-site operator
   do it.
4. **Restore service.** Often a controlled restart; sometimes a
   software rollback (
   [`../03-software-stack/10-build-deploy-and-maintenance.md`](../03-software-stack/10-build-deploy-and-maintenance.md)
   for the rollback procedure).
5. **Verify.** Watch the cell complete 10 cycles before re-engaging
   unattended mode.
6. **Log the incident.** Time, what happened, what you did. A simple
   `INCIDENTS.md` file is fine.
7. **Post-mortem within 48 h** for any sev-1. Blameless. The aim is
   the *fix*, not the *blame*.

## A blameless post-mortem template

```
Incident date / time:        ___
Detected by:                 alert / operator / engineer noticed
Time to acknowledge:         ___
Time to recover:             ___
Severity:                    sev-1 / sev-2 / sev-3
What happened (narrative):    ___
Impact:                       cycles lost, parts damaged, safety implications
Root cause:                   ___
Contributing factors:         ___
What went well:               ___
What went poorly:             ___
Action items (with owners):  ___
```

Save these in a `postmortems/` folder, dated. They become an
institutional memory: "we've seen something like this before."

## Drift — the slow, silent killer

Cells fail acutely (alerts) or **slowly** (drift). Things that drift:

- **Camera focus, lens cleanliness.** Detection accuracy slowly
  drops.
- **Lighting.** A sun-facing window changes everything by season.
- **Mounting bolts.** Loosen with vibration over months.
- **Gripper pads.** Wear out, friction drops, picks fail.
- **Calibration.** Slowly degrades; do the periodic touch test.

Make the daily summary surface drift: success rate over the last
week, calibration touch-test trend, mean detection-confidence trend.
If the trend line points down for 5 days, investigate **before** the
cell crosses the alert threshold.

## On-call rota

For unattended cells with real consequences:

- **Primary** — engineer who can fix it.
- **Secondary** — operator / supervisor who can do a safe restart.
- **Rota tool** — PagerDuty, OpsGenie, or a simple Google Calendar.
- **Escalation path** — primary → secondary → engineering manager
  → cell owner.
- **Acknowledge SLA** — 15 min for sev-1; published, not implicit.

## Output of this step

```
Dashboard URL:                  ___
Logging stack:                   rosbag → MCAP / Foxglove / Grafana / cloud
Alert channels:                  Slack: #___ , Email: ___ , SMS: ___
Sev-1 acknowledge SLA:           ___ min
Sev-2 acknowledge SLA:           ___ min
On-call rota tool:               ___
Primary on-call rotation:        ___
Incident log path:               ___
Postmortem folder:               ___
Daily summary recipient list:    ___
Drift KPIs surfaced?:            yes / no
First fake alert fired (date):  ___ — received by ___
```

## Common mistakes

1. **No live dashboard.** "We have logs." Logs are post-mortem;
   dashboards are real-time.
2. **Alerts to a Slack channel nobody reads.** Fire a test, confirm
   reception, then trust the channel.
3. **Too-noisy alerts.** On-call learns to ignore. Tune until each
   alert is genuinely actionable.
4. **No on-call rota.** Same engineer carries the pager forever and
   burns out.
5. **Postmortems that find a person to blame.** Same person now hides
   the next incident.
6. **Ignoring drift.** Hard failures are loud. Drift is quiet and
   far worse.
7. **No rehearsed restore.** First time you try a rollback is during
   a real outage. Rehearse the rollback at least quarterly.

## What's next

Layer 4 is done. Together with Layers 1–3, you have:

- A clear task spec.
- A complete hardware list.
- A working software stack.
- A working, validated, monitored cell with trained operators.

Beyond this point lives **Layer 5+** (fleet operations, continuous
improvement). Those only become useful once a single cell is
rock-solid. Use what you have now first.

← Back to: [Layer 4 README](README.md)
