> **Repository authority status:** Historical/donor repository. Prospective NOVITAS Nexus authority is [NOVITAS_NEXUS](https://github.com/skylersemailaddress-debug/NOVITAS_NEXUS). Historical canonical language below is provenance only and does not override `REPOSITORY_STATUS.v1.yaml`.

# NexusV3 Bootstrap

This bootstrap creates the canonical `C:\NexusV3` repo skeleton and the separate `C:\NexusQuarantine` repo skeleton.

It also installs:
- canonical invariants
- runtime/auth/execution graph contracts
- merge and hygiene policies
- canon compiler scaffold
- gate runner scaffold
- runtime auditor scaffold
- git hook templates

## Enforced principle
No code or extracted subsystem should be promoted into `C:\NexusV3` unless it passes:
1. canon compile
2. gate execution
3. validation and proof requirements

## Recommended next step after apply
Wire the Git hooks and CI so `tools/canon/compile.py` and `assembly/gates/gate_runner.py` run on every change.
