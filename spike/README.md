# Spike measurements

Experiments that settle open questions in the specification. Each one exists to replace an assumed
number with a measured one, and the artefacts it produced are kept so the numbers can be re-checked
rather than believed.

| Script | Question it settles | Recorded in |
|---|---|---|
| `measure_export.py` | what the free HTML export path costs and what it drops | E-051, LIM-004, LIM-006 |
| `measure_workspace_document.py` | what a workspace document costs to save, load, list and add to as it grows (engine environment, no VTK) | E-209, LIM-016 |
| `measure_cross_check.py` | this product's numbers against the toolkit's own filters - the kernels ParaView runs - on the same files and quantities: what agrees, what differs and why (engine environment) | E-214, XC-287, `cross_check.json` |

Run with the spike environment, which is deliberately separate from anything the product will ship:

```bash
python -m venv .venv-spike
.venv-spike/Scripts/python -m pip install "vtk==9.5.2" "pyvista[jupyter]" trame-vtk trame-vuetify
.venv-spike/Scripts/python spike/measure_export.py
```

`artifacts/` holds the measured files. They are large and are not kept under version control; the
numbers in `results.json` are the record, and re-running reproduces them.
