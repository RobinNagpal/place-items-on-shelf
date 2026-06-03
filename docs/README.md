# Learning Robotic Arms — Step By Step

A beginner-friendly walkthrough of how to think about a robotic-arm problem
*from scratch*. Written for people who are new to robotics and want to learn
the field one layer at a time, in plain English, without diving into code.

We focus only on **robotic arms** (sometimes called manipulators). Mobile
robots, drones, and humanoids are out of scope here.

The series is built so each doc adds one layer on top of the previous ones.
Read them in order.

## Pattern of each doc

Every doc in this series follows the same shape:

1. **Why this layer matters** — the role this layer plays in the whole stack.
2. **The key questions / steps** — what you actually do at this layer.
3. **A checklist** — copy-paste it for any new problem.
4. **Common mistakes** — what beginners get wrong.
5. **Libraries / frameworks** — what tools exist for this layer, if any.
6. **What's next** — the layer that builds on top of this one.

## Reading order

1. **[01-understanding-the-problem.md](01-understanding-the-problem.md)** —
   The first step for any robotic-arm task: defining the problem before you
   touch any hardware or library. The 7 questions to ask, the checklist to
   fill in, and what to hand off to the next layer.

*(More layers will be added one at a time. This series is intentionally being
written slowly — each layer thoroughly before the next.)*

## What this series is **not**

- It is not a tutorial for one specific robot. The mycobot-280-pi specific
  recipes live under
  [`../robots/mycobot-280-pi/docs/`](../robots/mycobot-280-pi/docs/) and assume
  you already know roughly what you're doing.
- It is not a code reference. We stay at the concept and workflow level.
- It is not exhaustive — we aim for the **most useful 80%** of each topic,
  not every academic detail.

If you want depth on a specific topic after reading the relevant layer here,
follow the links to the robot-specific docs or to external resources at the
end of each chapter.
