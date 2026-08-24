"""Capacity limits, held once.

These are the values `specs/05_limits.md` declares, and the specification linter compares the two on
every run: a number changed here without changing the specification, or the reverse, fails the build.
That is the point of the file - not to centralise constants, but to make the specification testable.

Two machine classes are supported (XC-086). The values below are the integrated-graphics class, which
is what has been measured; the workstation class is unmeasured and inherits them, which understates it.
"""

from __future__ import annotations

# specs/05_limits.md LIM-001: dataset held in memory per case. 8 GiB, written in the internal unit -
# the glossary makes bytes the internal unit for memory, and a name carrying its unit is the rule
# (GL-020). An earlier version of this line read `MAX_DATASET_BYTES = 8`, which the parity check
# accepted because the specification also said 8: both were literally 8, a billion-fold apart.
MAX_DATASET_BYTES = 8589934592

# specs/05_limits.md LIM-002: measured on integrated graphics with every frame verified distinct
MAX_INTERACTIVE_TRIANGLES = 10000000

# specs/05_limits.md LIM-005: cases in one workspace, still an assumption
MAX_CASES_PER_WORKSPACE = 500

# specs/05_limits.md LIM-007: how deep a pipeline may nest before it stops being readable
MAX_PIPELINE_DEPTH = 3

# specs/05_limits.md LIM-008: iterations one loop unit may run. The count is resolved before the loop
# starts (XC-100), so this catches a formula that yields a million iterations at edit time rather than
# after a night of running.
MAX_LOOP_ITERATIONS = 1000

# specs/05_limits.md LIM-009: background content per view. Appearance must not spend the frame budget
# the result itself needs, so this sits below the interactive ceiling rather than sharing it.
MAX_BACKGROUND_PRIMITIVES = 4000000

# specs/05_limits.md LIM-012: run output in one @Workspace before the product asks about it. Twenty
# gigabytes, in the internal unit (GL-020) - the specification states it in gigabytes and a name that
# does not carry its unit is how `MAX_DATASET_BYTES = 8` happened. Not a refusal: the point at which
# the workspace says how much space is in use and offers to prune by run (XC-141).
MAX_OUTPUT_BYTES = 21474836480

