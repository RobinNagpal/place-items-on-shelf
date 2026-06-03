# Layer 1 — Finalize The Requirements

Before you pick a robot, a gripper, or anything else, you need to **know what
the robot is supposed to do.** This sounds obvious. People skip it anyway.
Then they buy the wrong arm.

This layer is just thinking and writing. No code. No shopping. No software.
You sit down with whoever wants the robot and turn their wish into a clear,
short document.

## Read these in order

1. **[understanding-the-problem.md](understanding-the-problem.md)** — The
   seven core questions every project must answer. The task, the objects,
   the place, success and failure, speed, reach, and the boring practical
   limits (money, power, safety, who fixes it when it breaks).
2. **[additional-requirements-to-consider.md](additional-requirements-to-consider.md)** —
   The questions people often miss in the first pass: how often does this
   run, how long must it last, who operates and maintains it, what happens
   when it fails, what other systems must it talk to, what records must it
   keep, and is there a regulator who cares.

## What you leave this layer with

One short document — a **task specification** or just a **problem
statement.** It fits on a page or two and lists clear answers to every
question in both files above.

You show this document to:

- The person who asked for the robot, to confirm you understood them.
- A teammate, to make sure they agree on what's being built.
- Yourself in three months, when you've forgotten the original ask.

You also use it as a **filter** for the next layer. When you compare arms,
grippers, sensors, mounts, power supplies, you compare each against the
numbers in this document. Without it, every later choice is a guess.

## What's next

Layer 2 — [`../02-hardware-selection/`](../02-hardware-selection/) — takes
this document and turns it into a full hardware shopping list. Not just the
arm and the gripper, but the mounting structure, power, control hardware,
networking, cables, safety equipment, and the operator interface. The whole
physical setup, decided one piece at a time.
