"""What a deliverable may weigh (LIM-006).

The limit is not a tidiness rule. A report is a file an engineer emails, and a mail system that
bounces it makes the deliverable useless in the one way its recipient cannot work around. So the
size is bounded, the boundary is here rather than in the writer, and a document that would exceed it
is **reduced and marked as reduced** rather than written silently oversized - the numbers in it stay
computed on the full data whatever the picture is reduced to (INV-001).

Named by LIM-006 as its source of truth. `validate/check_specs.py` compares the value below against
the specification, so moving one without the other fails the build.
"""

from __future__ import annotations

#: specs/05_limits.md LIM-006: 20 MB. Measured against E-051 - one million-point surface costs
#: 16.1 MB as compressed geometry and 34.4 MB through the free export path, so an unbounded document
#: of several views lands past what a mail system accepts.
MAX_REPORT_BYTES = 20971520
