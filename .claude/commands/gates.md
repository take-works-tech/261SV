---
description: Run every repository gate and the test suite, and report what each could not check
---

Run all of these, and do not stop at the first failure — the work list is more useful whole:

```bash
python validate/check_specs.py
python validate/check_boundaries.py
python validate/check_commands.py
python validate/check_constant_duplication.py
python validate/check_context_budget.py
python validate/check_dependency_pins.py
python validate/check_gates_wired.py
python -m pytest tests -q -rs
```

Report the result in one paragraph, leading with the outcome. Then state, explicitly:

- every **NOT checked** line the gates printed, because silence from a gate reads as coverage
- every test that **skipped** and why — a skip that CI would forbid is a finding, not a pass
- the context cost from `python validate/check_specs.py --report`, if you ran it

If everything is green, say so plainly with the numbers. Do not hedge a green result.
