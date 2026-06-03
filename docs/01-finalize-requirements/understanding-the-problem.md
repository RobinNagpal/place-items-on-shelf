# Understanding The Problem First (Before You Touch Any Robot)

> **Who this is for:** Anyone new to robotic arms who has been given a task
> (or is dreaming one up). No code in this doc. No libraries. Just thinking.

## Why this is the first thing

When people start learning robotics, the first instinct is to ask:

- "Which robot arm should I buy?"
- "Which software framework should I learn?"
- "Should I use AI or normal programming?"

These are good questions, but they are not the first question. You cannot
answer any of them until you know *what the robot has to do*. Picking a
robot before you understand the task is like buying paint before you know
which room you're painting. You end up with the wrong colour, the wrong
amount, or both.

So **Layer 1 is not about robots at all.** It's about the task. Everything
later — the arm, the gripper, the sensors, the libraries, the planner — comes
out of what you write down in this layer.

## A simple way to think about it

Imagine a friend who knows nothing about robots walks up and says:

> "I want a robot to do X."

Your job, before doing anything else, is to ask questions until you could
explain X to a 10-year-old. If you cannot explain the task in one short
paragraph of plain English, **you are not ready to choose a robot or write
any code yet**. Go back and ask more questions.

That's the whole spirit of this layer.

## The 7 questions you must answer

These are the questions that turn a vague idea ("I want a robot to help in
my kitchen") into a real task description ("I want an arm that picks a
specific cup from a specific counter and places it on a specific shelf,
once every few minutes").

### 1. What is the task, in one sentence?

Write the task in one plain sentence. No fancy words. Not "autonomous
manipulation system" — just "pick up cups and put them on a shelf".

Examples of one-sentence tasks:

- "Pick a red cylinder from a table and place it 30 cm away."
- "Pour liquid from one bottle into another."
- "Tighten a screw on a circuit board."
- "Put a test tube into a rack of test tubes."

If you cannot write this sentence, you don't have a task yet. You have a
*wish*. Keep talking to whoever is asking for the robot.

### 2. What objects is the robot handling?

For every object the robot touches, you need to know:

- **Shape** — Is it a box, a cylinder, a sphere, a weird shape?
- **Size** — How big? (length, width, height in cm)
- **Weight** — How heavy? (grams or kilograms)
- **Material** — Hard plastic? Slippery glass? Soft fruit? Wet?
- **Fragility** — Can the gripper squeeze it without breaking it?
- **How many different kinds?** — Just one type, or many?

This tells you what kind of **gripper** you'll need later, and how strong
the arm has to be.

### 3. Where does the task happen? (The environment)

Robots behave very differently in different places. Describe yours:

- **Tidy or messy?** A factory line where everything has a fixed spot is
  tidy. A kitchen where humans move things around is messy.
- **Indoor or outdoor?** Lighting, weather, dust.
- **Cluttered?** Are other objects in the way?
- **Are humans nearby?** This is huge. If yes, safety becomes the top
  priority and you probably need a "collaborative robot" (cobot).
- **Is the workspace fixed, or does the arm move around?** Most arms sit on
  a base. Some sit on a mobile robot.

### 4. What counts as success? What counts as failure?

How will you know the robot did the task right? Be specific:

- "The cup must end up on the shelf without falling over."
- "The screw must be tight to the right torque."
- "The arm must succeed 95 times out of 100."

And what counts as failure? Be specific here too:

- "The cup must not be dropped or broken."
- "The robot must not hit anything."
- "The whole task must finish in under 30 seconds."

A clear success rule is the only way to test the robot later.

### 5. How precise and how fast must it be?

Precision and speed cost money. Be honest about what you need:

- **Precision** — How exact does the position have to be? A millimetre? A
  centimetre? "Roughly in the bin"?
- **Repeatability** — Does it have to land on the same spot every time? Or
  just close?
- **Cycle time** — How fast does one task need to finish? One task per
  day? One per second?

"As fast and as accurate as possible" is **not** an answer. Real arms
trade speed for precision. Pick a target.

### 6. What is the workspace and reach?

How far does the arm need to reach?

- Sketch the area. Even on paper. How wide, how deep, how tall?
- Where is the arm mounted? On a table? On the floor? Upside-down on a
  frame?
- Are there obstacles inside the workspace it must avoid? (Walls, shelves,
  other machines, the human worker?)

This rules out arms that are too small or too big.

### 7. What are the practical limits?

The boring but important questions:

- **Budget.** A hobby arm costs a few hundred dollars. An industrial arm
  costs tens of thousands.
- **Power supply.** Wall socket? Battery? How much current?
- **Safety rules.** Especially with humans nearby. Some workplaces legally
  require certified safety standards (ISO 10218, ISO/TS 15066).
- **Software you must connect to.** An existing factory PLC? A web app? A
  database?
- **Maintenance.** Who fixes it when it breaks?

These often kill options that look perfect on paper.

## A fill-in-the-blank checklist

Copy this for every new project. Don't skip lines. "N/A" or "I don't know
yet" are valid answers — but you should know which is which.

```
Task one-liner:
  ____________________________________________________________

Object(s) handled:
  - Object 1:
      Shape: ___   Size: ___   Weight: ___   Material: ___   Fragility: ___
  - Object 2 (if any):
      Shape: ___   Size: ___   Weight: ___   Material: ___   Fragility: ___

Environment:
  Tidy / messy?              ___
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
Other systems to connect to: ___
Who maintains it:          ___
```

## What this step gives you (the output)

When you finish this doc, you should be holding **one short document** —
sometimes called a task specification, requirements document, or just a
problem statement. It fits on one page and contains answers to all seven
questions above.

This document is what you'll show to:

- A teammate, to make sure you agree on what's being built.
- A customer, to confirm you understood them.
- Yourself in three months, when you've forgotten the original ask.

You'll also use it as a **filter** in the next layers:

- When you compare arms, you filter by reach, payload, precision — all
  numbers from your spec.
- When you choose a gripper, you filter by object shape, weight, fragility.
- When you pick sensors, you filter by what perception the task needs.

Without this document, every later choice is a guess.

## Common mistakes at this step

1. **Picking the robot first.** "We bought this arm, now what can it do?"
   is the wrong order. The arm should follow the task.
2. **Skipping the object analysis.** "We'll figure out the gripper later" —
   then later, you discover no gripper exists that can handle wet,
   slippery, irregular objects of that size.
3. **Vague success rules.** "It should pick things up nicely" gives you no
   way to test the robot.
4. **Ignoring humans.** If a person is anywhere near the arm, safety stops
   being optional. Decide that early.
5. **Thinking "we can change the spec later".** You can, but every change
   ripples through every later layer. Better to be slow here than rebuild
   everything later.

## Tools you can use at this step

Mostly nothing — this is a thinking step, not a coding step. There are no
Python libraries that will write your problem for you.

But a few simple things help:

- **Requirements templates** from engineering practice — the "user story"
  format, or "Given / When / Then". Any of these is fine. Filling it in
  matters more than the format.
- **Whiteboards and sketches.** Drawing the workspace from the side and
  from above catches more problems than any document.
- **Talking to whoever asked for the robot.** The single most valuable
  tool at this step. Ten minutes of conversation saves weeks of rework.

Software libraries (ROS, MoveIt, OpenCV, AI models) come after, not now.
You won't use any of them yet.

## What's next

The seven questions above cover the basics. There are more questions that
many people miss in the first pass — about how often the task runs, how
long the system must last, who operates it, what happens when it fails,
what records you must keep, and so on. Those live in the next doc:

→ Next: [additional-requirements-to-consider.md](additional-requirements-to-consider.md)
