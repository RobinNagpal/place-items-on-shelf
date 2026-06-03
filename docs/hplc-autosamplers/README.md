# HPLC Autosamplers — Project Task Folder

This folder is the **project-specific task description** for our robot
arm. The wider [`docs/`](..) tree is the *general* learning curriculum
(layer 1 — finalize requirements, layer 2 — hardware). This folder is
the **first real task** we apply that curriculum to.

**Short version of the task:**

> Build a small robot arm that **loads sample vials into the tray of
> an HPLC autosampler**. The HPLC instrument is already automatic for
> injection. The boring, error-prone, manual part — getting vials into
> the tray in the right order — is what we automate.

## Read these in order

The four files at this level explain the problem in plain English:

1. **[`01-what-needs-to-be-done.md`](01-what-needs-to-be-done.md)** —
   The whole task in one page. Skim this first to get the shape of
   the project.
2. **[`02-what-is-hplc-and-an-autosampler.md`](02-what-is-hplc-and-an-autosampler.md)** —
   Background. What HPLC actually is, what an autosampler is, why
   labs care about either.
3. **[`03-manual-steps-today.md`](03-manual-steps-today.md)** — The
   steps a human still does by hand today: sample prep, capping and
   labelling, tray loading, drawer in/out.
4. **[`04-why-automate-tray-loading.md`](04-why-automate-tray-loading.md)** —
   The case for automating *the tray-loading step specifically* (vs.
   the rest of the workflow).

Then the **requirements** — what the robot must actually deliver,
filled in against the framework in
[`../01-finalize-requirements/`](../01-finalize-requirements/):

5. **[`requirements/`](requirements/)** — One folder, six short
   files, each answering a slice of the Layer-1 questions for this
   specific project. **Requirements are the starting point** — every
   later hardware and software choice gets filtered against these
   numbers.

## Where this fits in the rest of the docs

- **[`../01-finalize-requirements/`](../01-finalize-requirements/)** —
  General framework: how to write *any* robot task spec.
- **[`requirements/`](requirements/)** — That framework, *filled in*
  for the HPLC autosampler problem.
- **[`../02-hardware-selection/`](../02-hardware-selection/)** —
  General framework: how to choose hardware once requirements are
  fixed.
- **[`../../robots/mycobot-280-pi/docs/`](../../robots/mycobot-280-pi/docs/)** —
  The specific arm we are starting with, and the existing simulated
  pick-and-place demo we will adapt.

## A note on numbers

The numbers in the requirements (vial size, tray slots, payload,
repeatability, budget) come from a quick scan of public datasheets and
how labs actually run today. They are **realistic, not exact** — pick
hardware against them and you will land in the right ballpark, but
expect to refine when we lock in the exact HPLC model and lab. Sources
are linked inline.
