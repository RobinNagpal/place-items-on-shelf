# 09 — Runbooks and Operator Training

The robot doesn't operate itself. A human starts it, checks on it,
fixes it when it stops. If that human is confused, the cell stops
producing value the moment the robotics engineer goes home.

This file is about the **documents and training** that turn a working
cell into a running operation.

## What you need before this step

- A cell that passed acceptance ([07](07-acceptance-tests.md)) and
  safety validation ([08](08-safety-validation.md)).
- The Layer-1 answer to "who operates it day-to-day."
- At least one **actual operator** available to read drafts.

## The four documents you need

### 1. The Quick-Reference Card (laminated, on the cell)

One side of A4. Lives next to the cell. Used 100 times a day.

Contents:

- **How to start the cell** — power-on sequence, 4–6 numbered steps.
- **How to stop the cell normally** — the *graceful* shutdown.
- **How to e-stop and reset** — the *emergency* stop and recovery.
- **What each stack-light colour means.**
- **Who to call** — name, phone, time-zone.

Nothing else. If it's longer than one side, it's not a quick
reference.

### 2. The Operator Runbook (longer; on the computer or a folder)

The complete manual. Sections:

- **Cell purpose** — one paragraph explaining what the cell does.
- **Safety summary** — what *not* to do, and why.
- **Daily startup procedure** — a longer version of the quick-ref.
- **During the shift** — what to watch for, when to intervene.
- **End-of-shift procedure** — graceful shutdown, log-off.
- **Common faults and fixes** — the "if X happens, do Y" list.
- **When to escalate** — exactly what counts as "call engineering."
- **Where to find logs and dashboards.**

Aim for **20 pages or less.** Longer manuals don't get read.

### 3. The Fault Tree / Troubleshooting Decision

A small flowchart or table:

| Symptom | First check | If still broken | Escalation |
|---------|-------------|-----------------|------------|
| Stack light is red | Read pendant message | Press Reset (twice if no change) | Call engineering |
| Arm runs but misses parts | Lighting changed? Clear camera lens | Wipe board, re-run calibration test | Call engineering |
| Cell is paused, nothing visible wrong | Network OK? Press Resume | Check Slack #robot-alerts | Call engineering |
| E-stop pressed | Identify cause; clear it; rotate to release; press Reset | If e-stop won't release, call engineering | — |
| Detection drift across the day | Adjust ambient light if you can | Reduce throughput target; flag for engineering | — |

Three to seven rows is right. More than that, the operator won't
read it.

### 4. The Maintenance Calendar

A simple monthly / quarterly calendar:

- **Daily:** wipe gripper, check stack light, glance at dashboard.
- **Weekly:** clean camera lens, check that all cables are still
  routed (no chafing).
- **Monthly:** check bolt torque, vacuum cabinet vents, review log
  for slow drift.
- **Quarterly:** re-run calibration, replace wear items (vacuum cups,
  gripper pads), review safety devices.
- **Annually:** full safety re-validation.

Print it. Stick it on the cell.

## The training session

Pure documents don't make a competent operator. Run a training session:

- **Duration:** 60–90 minutes for a desktop cell, longer for a
  production line.
- **Attendees:** every operator who will touch the cell, plus their
  shift manager.
- **Format:** show, do, watch.
  1. **Show** — robotics engineer walks through startup, normal run,
     stop, e-stop, reset.
  2. **Do** — each operator performs the same sequence with the
     engineer watching.
  3. **Watch** — operator runs the cell on real work for at least one
     cycle without prompts.

Sign and date that each operator has been trained. Keep the signed
sheet in the cell's documentation folder.

## A common-fault drill

Specifically rehearse the **most likely failure** in real conditions:

- Trip the e-stop. Have the operator reset it.
- Place an object outside the workspace. Have the operator recognise
  the fault, clear it, restart the cell.
- Briefly cover the camera. Operator must spot the issue and clean
  the lens or call engineering.

Operators who've rehearsed these stay calm when they happen for real.

## Hand-off to operations

The cell isn't *yours* once operators are running it. Specifically
hand off:

- **Maintenance calendar ownership** — to operations / facilities.
- **The on-call rota** — who answers if the cell faults at 3 a.m.
- **The change-management process** — operations can call you for
  config changes, but they don't make code changes themselves.
- **Permissions** — the operator account has limited access; admin
  is engineering's only.

Without an explicit hand-off, you keep getting paged forever.

## Output of this step

```
Quick-reference card on cell?:    yes / no
Operator runbook path:            ___ (pages: ___ )
Fault-tree table created?:         yes / no
Maintenance calendar posted?:     yes / no
Operators trained (count):         ___
Training signatures stored at:    ___
Drill performed (date):           ___
On-call rota source-of-truth:     ___ (PagerDuty / OpsGenie / Slack rota)
Change-management policy:         ___
Sign-off:                          operator manager (date) ___ , engineering (date) ___
```

## Common mistakes

1. **A 50-page manual.** Nobody reads it. Cap at 20.
2. **No quick-reference card.** Operator has to look up the runbook
   to start the cell every morning.
3. **Training in a sterile demo room.** Train in the actual
   environment, on actual work.
4. **No fault drill.** First real fault happens, operator panics.
5. **No hand-off.** Engineering keeps the pager forever.
6. **One operator trained.** That operator gets sick; nobody else
   knows how. Train at least two.

## What's next

Operators are trained. The cell is officially "in operation." The
last piece of Layer 4 is the Day-2 monitoring and incident response
that keeps it running.

→ Next: [10-monitoring-and-incident-response.md](10-monitoring-and-incident-response.md)
