"""Rendering budgets, held once and compared against the specification by the linter.

See `specs/05_limits.md` for what each value means and how it was arrived at. The field-buffer limit
comes from the platform's documented default rather than from a measurement here, and says so.
"""

from __future__ import annotations

# specs/05_limits.md LIM-003: the platform's default maximum storage-buffer binding, 128 MiB
MAX_FIELD_BUFFER_BYTES = 134217728
