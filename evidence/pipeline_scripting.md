---
status: draft
updated: 2026-08-20
---

# Evidence: pipeline units and the scripting surface

How two established products - one a general 3D application with a large scripting community, one a
simulation suite used in engineering offices - solved the same four problems: naming things a script
can reach, letting users write expressions without letting them write code, repeating work a bounded
number of times, and deciding when a script may run.

### E-064 - Blender: names are unique within a type, and scripted operators skip undo by default
- tier: T1
- url: https://docs.blender.org/manual/en/latest/files/data_blocks.html and
  https://docs.blender.org/api/current/bpy.data.html and https://docs.blender.org/api/current/bpy.ops.html
- verified: 2026-08-20
- says: every data-block within a type carries a unique name, which the application enforces by
  appending a numeric suffix - a new object added while `Cube` and `Cube.001` exist becomes `Cube.002`,
  and no existing data-block is ever renamed to make room. Collections are indexed by that name as well
  as by position, so `bpy.data.objects["Cube"]` resolves to exactly one thing. Separately: operators
  invoked from Python **bypass undo by default**, so that a script does not push an undo step per
  operator; undo must be asked for per call or pushed manually
- justifies: XC-103, XC-102

### E-065 - Blender: a restricted expression subset evaluated without a Python interpreter
- tier: T1
- url: https://docs.blender.org/manual/en/2.93/animation/drivers/drivers_panel.html and
  https://developer.blender.org/D3698
- verified: 2026-08-20
- says: driver expressions written inside a documented subset - `+ - * / ( )`, `== != < <= > >=`,
  `and or not`, the ternary conditional, driver variables, `frame`, `pi`, `True`, `False` and a subset
  of the maths functions - are evaluated **without invoking the Python interpreter**, and continue to
  evaluate when script execution is disabled entirely. An expression outside the subset falls back to
  Python and therefore requires the file to be trusted, or the auto-run preference to be enabled, which
  is off by default
- justifies: XC-101, XC-102

### E-066 - Blender: repetition is bounded, and early exit on a condition is not offered
- tier: T1
- url: https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/repeat_zone.html
  and https://projects.blender.org/blender/blender/pulls/109164
- verified: 2026-08-20
- says: the repeat zone takes its iteration count as an input, evaluated before the zone runs. Stopping
  the repetition early on a dynamic condition is not supported; users emulate a break with a switch
  inside the loop, which still executes every iteration
- justifies: XC-100

### E-067 - Ansys: names are not unique, and derived parameters are expressions over other parameters
- tier: T2
- url: https://mechanical.docs.pyansys.com/version/stable/examples/gallery_examples/01_basic/bolt_pretension.html
  and https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/wb2_help/wb2h_parameters.html
- verified: 2026-08-20
- says: in Mechanical scripting, `DataModel.GetObjectsByName(name)` returns a **list** of every object
  carrying that name and the documented caveat is that it is robust only where namings are unique; the
  idiom in published examples is to take `[0]`. At project level, parameters are named positionally -
  `P1`, `P2` - reached as `Parameters.GetParameter(Name='P1')`, and a derived parameter is defined by an
  **expression over other parameters**, such as `max(P1,P2)` or `SetParameterExpression(param, "cos(1)")`.
  Design points are sets of parameter values, each producing one run
- justifies: XC-099, XC-101, XC-103
- note: tier T2 because the `[0]` idiom is read from published examples and forum answers rather than
  from a normative statement. The uniqueness caveat itself is documented; what engineers do about it is
  observed

## What this evidence does and does not settle

It settles the shape of three mechanisms - naming, expressions, repetition - because two independent
products converged on the same constraints and documented what happened when they did not. It settles
nothing about whether users of *this* product want to write pipelines in Python at all; that rests on
the product owner's judgement about the customer, recorded as E-001, and the Python surface is designed
so that a user who never opens it loses nothing.
