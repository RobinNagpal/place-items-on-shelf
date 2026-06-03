# How Perception Identifies The Cylinder (No AI Required)

## Short answer: no AI, no machine learning, no neural networks

Despite how "smart" it looks when the robot correctly picks the red cylinder, there
is **no AI model** involved. No neural network. No training data. No GPU. The
perception code is pure geometry — algorithms from the 1980s and 1990s that you
could write down on paper and run by hand if you had enough patience.

This doc explains, in plain English, what's actually happening.

## The "blindfolded sorting" analogy

Imagine you have a basket of fruit and you're blindfolded. You can feel each fruit
with your hands. By touch alone you can still tell:

- A banana — long, curved, soft.
- An apple — round, palm-sized, firm.
- A watermelon — huge, round, heavy.

You're not "seeing" anything. You're matching the **shape** of what you feel to
shapes you already know about.

The robot's perception works the same way. It can't read labels or recognize that
"this red thing is a cylinder I've seen before". Instead, it gets a cloud of 3D
points from the camera, groups them into clusters, and tries to fit each cluster to
simple shapes it already knows about (cylinders and boxes).

## Step by step in plain language

### Step 1 — The camera gives the robot a cloud of 3D dots

The depth camera works by measuring how far away each pixel is. So for every pixel
in its view, the camera knows both the **color** (R, G, B) and the **distance**.
Combine those and you get a 3D dot at the right place in space, with the right color.

For our 424×240 camera, that's roughly **100,000 dots per frame**, ~30 times per
second. This big collection of dots is called a **point cloud**.

### Step 2 — The robot crops the cloud

A lot of those 100,000 dots aren't useful — points behind the robot, points way up
in the sky, points way far past the table. They get discarded. What's left is dots
in a defined "workspace" box where the robot can actually reach.

### Step 3 — The robot finds the table

This is the clever part. For each remaining dot, the algorithm looks at its
neighboring dots and asks: **"What direction is the local surface facing?"**

- Dots on a horizontal floor or table → the local surface faces straight up.
- Dots on a vertical wall → the local surface faces sideways.
- Dots on the side of a cylinder → the local surface faces outward.

These "surface directions" are called **surface normals**. They're calculated from
the relative positions of nearby dots — pure geometry, no AI.

Then: **find the biggest patch of dots whose normals all point up** at roughly the
robot's base height. That patch is the table.

### Step 4 — The robot removes the table dots from the cloud

Everything left in the cloud is now "stuff that's above the table" = objects.

### Step 5 — The robot groups the leftover dots into clusters

Dots that are physically close to each other in 3D get grouped together. In our
scene with 5 well-spaced YCB objects, the algorithm gets ~5 separate clusters. Each
cluster is assumed to be one object.

If two objects are touching, they'd get merged into one cluster — that's a known
weakness of this approach. But for well-spaced objects it works perfectly.

### Step 6 — For each cluster, the robot tries to fit a shape

This is where the "identification" happens. For each cluster, the algorithm asks:

- "If I assume this is a cylinder, what cylinder best matches these dots?"
- "If I assume this is a box, what box best matches these dots?"

Whichever assumption produces the better fit (more of the dots agree with the
shape) is the assumed identity of the cluster.

### Step 7 — How fitting works (RANSAC, in a nutshell)

To fit a cylinder to a cluster of dots, the algorithm uses a technique called
**RANSAC** (RANdom SAmple Consensus). The idea:

1. Pick a few random dots from the cluster.
2. Compute the unique cylinder that passes through those random dots.
3. Count how many of the OTHER dots in the cluster lie ON or NEAR that cylinder.
   That's the "score" of this candidate cylinder.
4. Repeat steps 1–3 thousands of times with different random dots.
5. Keep the cylinder with the highest score (the most agreeing dots).

This is surprisingly robust to noise. Even if 30% of the cluster's dots are weird
(reflections, measurement errors), enough of the "good" dots will agree with the
right cylinder that it wins on score. RANSAC was invented in 1981 — decades before
"AI" was a buzzword.

The same approach works for fitting boxes, lines, or any other geometric primitive.

### Step 8 — Read off the dimensions

Once a cylinder fit is locked in, the algorithm has direct mathematical access to
the cylinder's:
- Center position (x, y, z)
- Radius
- Height
- Orientation

These are just **parameters of the equation** of the fitted cylinder. No estimation
needed beyond what RANSAC already did. Same for fitted boxes (width, height, depth,
orientation).

That's why you saw in the logs:
```
Added cylinder collision object: id=cylinder_1, height=0.349, radius=0.012,
    position=(0.220, 0.119, 0.175), yaw=0
```

`0.349 m` height and `0.012 m` radius are the parameters of the cylinder that best
fit the red-cylinder cluster of dots — measured directly from the fit, not guessed.

### Step 9 — The robot picks the "target"

Now the algorithm has a list of fitted shapes: 4 boxes (cardboard, mustard, cheezit,
small thing) and 2 cylinders (the red one and the coke can).

The user (our config file) said: **"Find a cylinder of roughly 0.35 m height and
0.0125 m radius."** The algorithm compares each detected cylinder's dimensions to
that target:

- `cylinder_1`: height 0.349, radius 0.012 → very close match → similarity score ~1.00
- `cylinder_0` (coke can): height 0.124, radius 0.032 → poor match → low score

`cylinder_1` wins. That's the target.

## Why this works (and when it doesn't)

### Why it works for our scene

- The objects are simple shapes (cylinders, rough boxes).
- They sit on a flat horizontal surface.
- They're physically separated from each other.
- The camera has a clear top-down view (no occlusion).
- The lighting is consistent (it's a simulation, perfect rendering).

### Where this approach struggles

- **Weird shapes**: a teapot or a banana isn't a cylinder or a box. The fit will be
  bad and the algorithm either picks the "least bad" wrong match or rejects the
  cluster entirely.
- **Touching objects**: two cylinders pressed together look like one cluster. The
  algorithm can't split them.
- **Occlusion**: if half the cylinder is hidden behind something, only half the dots
  are available and the fit is unreliable.
- **Cluttered scenes**: 50 objects packed tightly is much harder than 5 spread apart.
- **Reflective or transparent surfaces**: depth cameras can't see through glass or
  off a mirror, so those parts are missing from the cloud.

## Could we have used AI here?

Yes, absolutely. There are AI-based perception models (YOLO, Mask R-CNN, SAM, etc.)
that would take the camera image, run it through a neural network, and output a
bounding box or pixel mask for "red cylinder". A separate small algorithm would then
convert that 2D detection into a 3D pose.

AI would be more flexible — handles weird shapes, partial occlusion, cluttered
scenes — but heavier: needs a GPU, a model file, and training data (or a
pre-trained model that happens to know what a "red cylinder" looks like).

For our project, addison chose **classical geometry** because:
- It's simpler to explain and reason about.
- It runs fast on a CPU (no GPU needed).
- It works perfectly for the simple shapes (boxes and cylinders) we deal with.
- There's no need for training data or model management.

If we ever needed to handle complex shapes (e.g. picking up a teapot, or identifying
an HPLC vial inside a rack of similar vials), we'd switch to an AI-based approach.
That's a future-project decision.

## TL;DR

- **No AI, no ML, no neural networks.** Pure geometry algorithms.
- The robot:
  1. Gets ~100,000 colored 3D dots from the camera each frame.
  2. Finds the table by looking for big horizontal patches of dots.
  3. Removes the table dots; groups what remains into clusters (one per object).
  4. Fits each cluster to a cylinder OR box using **RANSAC** (try thousands of
     random fits, keep the best).
  5. Reads off the dimensions directly from the fitted shape's equation.
  6. Compares the fitted cylinders' dimensions to the target (`0.35 × 0.0125`) and
     picks the closest match. That's the cylinder the robot will pick up.
- This works because our scene is simple (clean shapes, separated objects, top-down
  view, no occlusion).
- For complex scenes, AI-based methods would be more flexible — but heavier and
  harder to debug. Out of scope for now.

→ Next: [how-planning-works.md](how-planning-works.md) — companion to this doc on the
planning side: how the arm decides which joint angles to use once perception has
identified the target.
