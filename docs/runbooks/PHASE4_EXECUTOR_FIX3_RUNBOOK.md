# Phase 4 Executor Fix3 Runbook

This package replaces the Phase 4 executor with a semantic filter version.

It excludes low-signal staging from:
- .git
- .venv
- node_modules
- site-packages
- dist-info
- generated/quarantine/archive trees
- LOCK/LOG/REQUESTED/.py.typed/.gitkeep/.d.ts noise

It stages only layer-relevant candidate files.
