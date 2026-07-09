# 01 — How labs automate sticky-paste weighing today (short version)

A one-screen summary. The wider survey of HPLC-adjacent commercial
products lives in
[`../../research/05-existing-solutions.md`](../../research/05-existing-solutions.md).

The honest truth: **most food labs still weigh ketchup by hand.**
There is no widely-deployed off-the-shelf machine that gravimetrically
dispenses thick pastes to a 1 mg target. The list below is what
*partially* exists.

| System | What it does for sticky-paste weighing | Use it ourselves? |
|---|---|---|
| **Watson-Marlow 323Dud peristaltic pump + Mettler analytical balance** | Closed-loop on balance reading: pump runs, balance watches, pump stops at target. Works up to ~10,000 cP (ketchup at room temp is ~50,000 cP, near the limit — labs warm to 30 °C). ~$2,500 for the pump. | **Yes — copy the pattern.** |
| **Chemspeed SWING viscous-liquid head** | Positive-displacement syringe with a heated nozzle, gravimetric closed loop. Solves the problem fully. Sold only inside a complete $200k+ workstation. | Pattern OK; price too high. |
| **preeflow eco-PEN piston dispenser** | Industrial glue/silicone dispenser; handles 100,000+ cP. Cleaner shut-off than peristaltic. ~$3,000. | Fallback if Watson-Marlow's after-drip overshoots. |
| **Hamilton STAR / Tecan Fluent** | Pipetting workstations. Their syringes clog instantly on ketchup. | No — wrong tool. |

**The one line we take away:** copy Watson-Marlow's "pump + balance,
mass-based stop" pattern. Mount the pump statically on the bench; the
robot just places the empty beaker on the pan and picks it up filled.
That keeps the bead-break problem on the pump side, not the arm side
— which lets us use the same arm and gripper as the paracetamol case.

The full hardware reasoning is in
[`02-hardware-choice.md`](02-hardware-choice.md).
