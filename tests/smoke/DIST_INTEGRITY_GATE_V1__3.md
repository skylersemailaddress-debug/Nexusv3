# Dist Integrity Gate v1

This adds an evidence-first integrity gate:

- Runs the pipeline twice (via `GATE_RUN_LAYOUT_V1`)
- Computes a deterministic SHA-256 manifest of every file under `dist/` (excluding `__pycache__` and `*.pyc`)
- Writes the manifest into each run's `EVIDENCE/` folder
- Fails if the manifests differ between the two runs
- Also asserts a minimal runtime file set exists inside `dist/`

No changes are made to `dist/` itself; the manifest lives in `EVIDENCE/`.
