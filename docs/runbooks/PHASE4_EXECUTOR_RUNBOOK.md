# Phase 4 Executor Runbook

This package stages candidate files from the locked primaries and allowed reference sources into `staging\phase4\*` and writes execution manifests under `registry\phase4`.

It does not whole-merge repos. It creates a controlled staging layer for later promotion into `src\*`.
