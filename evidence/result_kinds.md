---
status: draft
updated: 2026-08-20
---

# Evidence: result kinds, deformed shape, and derived visualisation

Three things the established tools do that this specification had no answer for, and one thing they do
that produces a documented, recurring misunderstanding.

### E-076 - Harmonic results are complex, and two axes are swept independently
- tier: T2
- url: https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/wb_sim/ds_harmonic_analysis_type.html
  and https://ansyskm.ansys.com/forums/topic/tips-about-postprocessing-options-for-harmonic-solution-in-mechanical/
- verified: 2026-08-20
- says: a harmonic response is complex; **amplitude is the square root of the sum of the squares of the
  real and imaginary parts**. A result is evaluated at a **frequency** and at a **phase angle**, and the
  two cannot both be swept at once: the tool sweeps frequency at a fixed phase, or phase at a fixed
  frequency, and the **Sweeping Phase** property is what animation over time uses. Amplitude may be
  requested directly, including as a maximum over frequency. A modal analysis characterises the system
  first, and a linear harmonic response may be built from those modes by superposition
- justifies: XC-131, GL-036
- note: tier T2 because the operational detail is drawn from the vendor's knowledge base and
  documentation pages rather than from a normative standard; the amplitude definition itself is
  arithmetic and not in doubt

### E-077 - Deformation is displayed scaled by default, and the scaling confuses readers
- tier: T2
- url: https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/act_script/mech_apis_Results_Display.html
  and https://ansyskm.ansys.com/forums/topic/why-the-total-deformation-plot-does-not-measures-correctly-on-scale-ruler-at-the-bottom-gui-window/
- verified: 2026-08-20
- says: result display offers **True Scale** - a multiplier on the actual deformation - and **Auto
  Scale**, an application-computed multiplier, with presets at half, twice and five times auto. The
  current factor is shown in the toolbar in the form `2.8e+002 (Auto Scale)`, and `1.0 (True Scale)`
  restores the real shape. **Auto scale is the default.** The vendor's own knowledge base carries
  repeated questions of the form *why does the deformation plot not measure correctly against the scale
  ruler at the bottom of the window* - which is the auto-scaled geometry disagreeing with the ruler
- justifies: XC-132, INV-024, INV-025
- note: the recurring question is the finding. Displaying the factor is necessary and demonstrably not
  sufficient, because a reader measuring the picture does not read the toolbar

### E-078 - A streamline is defined by its seeds and its integrator, not by the field alone
- tier: T1
- url: https://www.paraview.org/paraview-docs/nightly/python/paraview.simple.__init__.StreamTracer.html
  and https://docs.paraview.org/en/latest/UsersGuide/filteringData.html
- verified: 2026-08-20
- says: stream tracing takes a **seed source**, an **integrator type** - Runge-Kutta 2, 4, or adaptive
  4-5 - an **initial step size** which is fixed for the non-adaptive integrators, and a **maximum number
  of steps** past which integration is terminated. The adaptive integrator adds minimum and maximum step
  length and a maximum error. Change any of them and the lines change
- justifies: INV-025, XC-133

## What this evidence changes

It moves three things out of "obvious" and into "written down": that a result may be indexed by
something other than time, that a picture of a deformed body is a picture of a body that does not exist
at that shape, and that a streamline is a computation with parameters rather than a property of the
data. Each of the three is a place where a correct value can be presented in a way that reads as a
different, wrong one.
