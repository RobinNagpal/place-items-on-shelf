# Layer 2 — Hardware Selection

Now that you know what the robot has to do (Layer 1), you pick the hardware
that will actually do it.

**"Hardware" is not just the arm.** A working robot cell is many pieces:

- The arm — the moving thing.
- The gripper — the hand that touches the object.
- The sensors — the eyes, the sense of touch.
- The mount — the table or frame the arm bolts to.
- The power — wall socket, transformers, compressed air.
- The control hardware — the computer or box that runs the robot.
- The network — how all the pieces talk to each other.
- The cables — how power and data physically reach every piece.
- The safety equipment — what stops the robot when a human gets too close.
- The operator interface — how a person tells the robot what to do.

Skip any of these and the system is broken. So **Layer 2 is one file per
piece**, in the order you'd usually decide them.

## Read these in order

The arm and the gripper come first because they decide your reach, payload,
and mounting flange. Once you know those, the rest fall into place.

1. **[arm.md](arm.md)** — Degrees of freedom, payload, reach,
   repeatability. The popular arm brands and what each one is best for
   (hobby, cobot research, industrial).
2. **[gripper.md](gripper.md)** — The hand. Parallel jaw, vacuum, soft,
   multi-finger, magnetic. Popular makers (Robotiq, OnRobot, Schmalz,
   SCHUNK, Soft Robotics).
3. **[sensors.md](sensors.md)** — Cameras (2D and depth), force/torque,
   tactile, proximity. Popular models per family and where they mount.
4. **[mounting-and-mechanical-structure.md](mounting-and-mechanical-structure.md)** —
   The frame and table. Heavy steel base, aluminum extrusion, mobile cart.
   Vibration, footprint, reaction forces.
5. **[actuation-and-power-systems.md](actuation-and-power-systems.md)** —
   What feeds the motors. AC mains, DC, compressed air. Power supplies,
   transformers, compressors, UPS.
6. **[control-hardware.md](control-hardware.md)** — The computer that runs
   the robot. Vendor controller box, PLC, industrial PC, edge AI box,
   Raspberry Pi.
7. **[communication-and-networking.md](communication-and-networking.md)** —
   How the pieces talk. Ethernet, EtherCAT, PROFINET, Modbus, ROS 2 DDS,
   USB3, GigE Vision. Switches, isolation, wireless.
8. **[cable-management.md](cable-management.md)** — How wires survive a
   moving arm. Drag chains, service loops, flex-rated cable, slip rings.
9. **[safety-equipment.md](safety-equipment.md)** — Emergency stops, light
   curtains, safety scanners, safety relays. What ISO 10218 actually
   requires.
10. **[operator-interface.md](operator-interface.md)** — Teach pendants,
    HMI panels, stack lights, push buttons. How a human controls and
    monitors the robot.

## Reference (not a numbered step)

- **[`../latest-robots.md`](../latest-robots.md)** — A dated snapshot of
  newer hardware: humanoids actually shipping or in production pilots,
  "AI-included" manipulation platforms, foundation-model "robot brains".
  Useful when the established hardware in this layer can't do your task
  and you need to look at the bleeding edge.

## What you leave this layer with

A **bill of materials** — a list of every piece of hardware you'll buy or
build, with the model, the quantity, and a rough cost. Together with the
Layer-1 task spec, this is enough to start procurement.

You also have a clear picture of the **physical setup**: where every piece
sits, how cables run, who has access, how a human steps in if needed.

## What's next (later layer)

Layer 3 (to be written) will cover the **software side**: given the
hardware list you finish with here, what perception, planning, and control
software do you build vs. inherit from open libraries vs. buy from a
vendor?
