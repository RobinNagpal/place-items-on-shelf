# 01 — Understand The Problem First (Before You Touch Any Robot)

> **Who this is for:** Anyone who is new to robotic arms and has been given (or is
> dreaming up) a problem to solve. No code in this doc. No libraries yet. Just
> thinking.

## Why this is "Layer 1"

When people start learning robotics, the first instinct is usually to ask:

- "Which robot arm should I buy?"
- "Which software framework should I learn — ROS, MoveIt, something else?"
- "Should I use AI or classical algorithms?"

These are **good questions, but they are not the first question.** They cannot
be answered until you know *what the robot is supposed to do*. Choosing a robot
before you understand the task is like buying paint before you know what room
you're painting. You'll end up with the wrong color and the wrong amount.

So **Layer 1 is not about robots at all.** It's about the problem. Everything
later — the arm you pick, the libraries you use, the planner you choose, the
sensors you add — flows from the answers you write down here.

## A simple way to think about it

Imagine a friend who knows nothing about robots walks up to you and says:

> "I want a robot to do X."

Your job, before doing anything else, is to ask enough questions until you
could explain X to a 10-year-old. If you cannot explain the task in one
paragraph of plain English, **you are not ready to choose a robot or write any
code yet**. Go back and ask more questions.

That's the whole spirit of Layer 1.

## The 7 questions you must answer

These are the questions that turn a vague idea ("I want a robot to help in my
kitchen") into a concrete task description ("I want an arm that picks up a
specific cup from a specific counter and places it on a specific shelf, once
every few minutes").

### 1. What is the task, in one sentence?

Write the task in one plain-English sentence. No jargon. No "autonomous
manipulation system" — just "pick up cups and put them on a shelf".

Examples of one-sentence tasks:

- "Pick a red cylinder from a table and place it 30 cm away."
- "Pour liquid from one bottle into another."
- "Tighten a screw on a circuit board."
- "Insert a test tube into a rack of test tubes."

If you cannot write this sentence, you do not have a task yet — you have a
*wish*. Keep talking to whoever is asking for the robot.

### 2. What object(s) is the robot handling?

For every object the robot touches, you need to know:

- **Shape** — Is it a box, a cylinder, a sphere, a weird organic shape?
- **Size** — How big? (length × width × height in centimetres)
- **Weight** — How heavy? (grams or kilograms)
- **Material / surface** — Hard plastic? Slippery glass? Soft fruit? Wet?
- **Fragility** — Can the gripper squeeze it without breaking it?
- **How many different kinds of objects?** — Just one type, or many?

This tells you what kind of **gripper** (end-effector) you'll eventually need,
and how strong the arm must be (payload).

### 3. Where does the task happen? (The environment)

Robots behave very differently in different environments. Describe yours:

- **Structured or unstructured?** A factory line where everything is in a
  fixed place is *structured*. A kitchen where humans move things around is
  *unstructured*.
- **Indoor or outdoor?** Lighting, weather, dust.
- **Is it cluttered?** Are there other objects in the way?
- **Are humans nearby?** This is huge — if yes, safety becomes a top priority
  and you may need a "collaborative robot" (cobot).
- **Is the workspace fixed, or does the arm move around?** Most arms sit on
  a base; some are mounted on a mobile robot.

### 4. What are the success and failure conditions?

How will you know the robot did the task correctly? Be specific:

- "The cup must be placed on the shelf without falling over."
- "The screw must be tightened to the right torque."
- "The pick must succeed 95 out of 100 tries."

And what counts as failure? Be specific here too:

- "The cup must not be dropped or broken."
- "The robot must not collide with anything."
- "The whole task must finish in under 30 seconds."

A clear success rule is the only way to test the robot later.

### 5. How precise and how fast must it be?

Precision and speed cost money and complexity. Be honest about what you need:

- **Precision (accuracy)** — How exact does the position have to be? Millimetre?
  Centimetre? "Roughly in the bin"?
- **Repeatability** — Does it have to land in the exact same spot every time?
  Or just close to the same spot?
- **Cycle time** — How fast does one task need to finish? Are you doing one
  task per day, or one per second?

"As fast and accurate as possible" is **not** an answer. Real arms have
trade-offs; you must pick a target.

### 6. What is the workspace and reach?

How far does the arm need to reach?

- Sketch the area. Even on paper. How wide, how deep, how tall?
- Where is the arm mounted? On a table? On the floor? Upside-down on a frame?
- Are there obstacles inside the workspace it must avoid? (Walls, shelves,
  other machines, the human worker?)

This will rule out arms that are too small or too big.

### 7. What are the practical constraints?

The "boring" but important questions:

- **Budget.** A hobby arm is a few hundred dollars; an industrial arm is tens
  of thousands.
- **Power supply.** Wall socket? Battery? How much current?
- **Safety requirements.** Especially if humans are nearby. Some workplaces
  legally require certified safety standards (ISO 10218, ISO/TS 15066).
- **Software you must integrate with.** Existing factory PLC? An app? A
  database?
- **Where will it be maintained?** Who fixes it when it breaks?

These often eliminate options that would otherwise look perfect on paper.

## A fill-in-the-blank checklist

For *every* new problem, copy this template and fill it in. Don't skip lines.
"N/A" or "I don't know yet" are valid answers — but you should know which is
which.

```
Task one-liner:
  ____________________________________________________________

Object(s) handled:
  - Object 1:
      Shape: ___   Size: ___   Weight: ___   Material: ___   Fragility: ___
  - Object 2 (if any):
      Shape: ___   Size: ___   Weight: ___   Material: ___   Fragility: ___

Environment:
  Structured / unstructured? ___
  Indoor / outdoor?          ___
  Cluttered?                 ___
  Humans nearby?             ___
  Arm mounted where?         ___

Success condition:
  ____________________________________________________________
Failure condition:
  ____________________________________________________________

Precision required:        ___ mm  (or ___ cm)
Repeatability required:    same spot every time? ___
Cycle time:                ___ seconds per task

Workspace dimensions:      ___ wide × ___ deep × ___ tall
Obstacles in workspace:    ____________________________________

Budget:                    ___
Power available:           ___
Safety standard required?  ___
Existing systems to integrate with: ___
```

## What this step gives you (the "output")

When you finish Layer 1, you should be holding **one short document** —
sometimes called a *task specification*, *requirements doc*, or just a
*problem statement*. It should fit on one page and contain answers to all
seven questions above.

This document is what you'll show to:

- A teammate, to make sure they agree on what's being built.
- A customer or stakeholder, to confirm you understood them.
- Yourself in three months, when you've forgotten the original ask.

You'll also use it as a **filter** in the next layers:

- When you compare arms, you'll filter by reach, payload, precision — all
  numbers from your spec.
- When you choose a gripper, you'll filter by object shape, weight, fragility.
- When you pick a planner, you'll consider cycle time and obstacles.

Without this document, every later choice is a guess.

## Common mistakes at this layer

1. **Picking the robot first.** "We bought this arm, now what can it do?" is
   the wrong order. The arm should follow the task, not lead it.
2. **Skipping the object analysis.** "We'll figure out the gripper later" —
   then later, you discover no gripper exists that can handle wet, slippery,
   irregular objects of that size.
3. **Vague success criteria.** "It should pick things up nicely" gives you no
   way to test the robot.
4. **Ignoring humans.** If a person is anywhere near the arm, safety stops
   being optional. Decide that early.
5. **Believing "we can change the spec later".** You can, but every change
   ripples through every later layer. Better to be slow here than rebuild
   everything later.

## "Are there libraries or frameworks for this layer?"

Mostly no — this is a thinking step, not a coding step. There are no Python
packages that will define your problem for you.

But there *are* a few helpful tools and templates:

- **Requirements templates** from systems-engineering practice (e.g. the
  "user story" format, or a simple "Given / When / Then" success criteria
  format). Any of these are fine — the format matters less than actually
  filling it in.
- **Whiteboards and sketches.** Drawing the workspace from the side and from
  above catches more problems than any document.
- **Talking to whoever asked for the robot.** The single most valuable
  "tool" at this layer. Ten minutes of conversation will save weeks of
  rework later.

Software libraries (ROS, MoveIt, OpenCV, etc.) come *after* this layer, not
during it. You won't use any of them yet.

## What's next

Once you have a filled-in task specification, you are ready to move down to
the **physical layer**: choosing the actual arm hardware (degrees of freedom,
payload, reach, repeatability) and the end-effector (gripper, suction cup,
tool). That will be the next doc in this series.

For now: pick a real problem you care about, sit with the seven questions,
and fill in the checklist. That is the entire homework for Layer 1.
