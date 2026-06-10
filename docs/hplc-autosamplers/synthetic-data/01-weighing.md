# 01 — Synthetic data for Weighing

> **Project status: skipped.** This project's
> [`gazebo_worlds/`](../../../gazebo_worlds/) folder does **not**
> include a weighing scene because the workflow puts the
> pre-weighed ketchup paste straight into the dissolution beakers
> instead. The notes below exist for anyone extending the project
> later.
>
> **Source workflow doc:**
> [`02-hplc-autosampler/03-hplc-workflow/01-weighing.md`](https://github.com/RobinNagpal/robotics-research/blob/main/02-hplc-autosampler/03-hplc-workflow/01-weighing.md).

## What the robot would do

Place a weigh boat on an analytical balance. Tare. Add ketchup
sample (paste) until the reading hits a target mass (typically
~5 g, ±0.1 mg matters). Transfer the weighed paste to the
dissolution vessel.

## What the robot must see or feel

| Decision | Sensor that answers it |
|---|---|
| "Is the balance on and ready?" | Camera at the LCD panel |
| "What does the balance read right now?" | Camera (LCD digits) **or** subscribing to the balance's serial-out |
| "Have I hit the target mass?" | Same |
| "Did the weigh boat go down evenly on the pan?" | Wrist F/T sensor |
| "How much more paste do I need to add?" | Closed-loop on the LCD reading + a slow scoop motion |

The balance has a serial / USB output in real labs, so this is
**partly an OCR problem and partly a non-vision integration
problem**. Synthetic data is useful for the OCR side.

## Useful synthetic-data types

| Type (from [`00-types-of-synthetic-data.md`](00-types-of-synthetic-data.md)) | Purpose here |
|---|---|
| **8 — synthetic text / LCD renders** | Train (or smoke-test) an OCR / 7-segment reader on the balance display. Cheap to generate: paint a 7-segment font onto a textured plane in front of the balance with random mass values, save image + ground-truth number. |
| **6 — F/T time-series** | The balance itself is a force sensor; if the real balance is offline, a wrist F/T sensor + a known-tare scale can do a rougher job. Useful trace: pour onset (force ramp), pour stop (target hit), tare-button press (zero crossing). |
| **11 — demonstration trajectories** | Recording 20 scripted "scoop and sprinkle" demos in sim is the basis for an imitation-learning policy that handles the final-grams nudge. The action space is small (tap-the-spoon / no-tap) and the observation is the LCD reading. |
| **12 — failure cases** | Over-pour (read mass > target by > 0.5 g), spilled-on-pan, balance not zeroed, draft-shield door left open (image classifier on the shield). |

## Concrete dataset shape

For a sim Weighing scene that *did* get built, the on-disk shape
would look like:

```
synthetic_weighing/
├── images/
│   ├── lcd_0001.jpg          # balance LCD close-up at 0.003 g
│   ├── lcd_0002.jpg          # … at 1.245 g
│   ├── overhead_0001.jpg     # top-down of weigh boat on pan
│   └── overhead_0001.png     # matching depth frame
├── labels/
│   ├── lcd_0001.json         # {"mass_g": 0.003, "stable": false}
│   ├── overhead_0001.json    # poses of weigh_boat, balance_pan, scoop
│   └── overhead_0001.mask.png  # weigh-boat silhouette mask
└── traces/
    └── ft_pour_0001.csv      # Fz over time during a slow pour
```

`lcd_*.jpg` is the OCR set; `overhead_*` is the scene-pose set;
`traces/` is the F/T set for the slow-pour controller.

## What is NOT worth generating here

- **Full RGB scene + YOLO boxes for the balance.** The balance
  is a fixed-pose object — a single calibration is enough; you
  do not need to "detect" it on every frame.
- **A photorealistic weigh-boat dataset.** Weigh boats are
  cheap, swappable, and the prep workflow doesn't need to
  identify a specific brand. A simple silhouette mask is
  sufficient for "is there a boat on the pan."

## What's next

If anyone re-adds Weighing to the project later, the natural
follow-on is a small ROS 2 node that subscribes to the simulated
LCD images, runs `paddleocr` (or a hand-rolled 7-segment decoder),
and publishes a `mass_g` topic for the slow-pour controller to
close on.
