# Source Intake Doctrine

All repo/source intake into NexusV3 must run through:

1. Source registry
2. Batch extraction runner
3. Extraction engine
4. Ship validation

## Rules
- sources are registered, not ad hoc
- each source maps to a target subsystem
- disabled sources are skipped
- whole-repo merge remains forbidden
- extraction records are the only accepted intake evidence
