NEXUS V3 RUNTIME LOCK
=====================

This repo has crossed the minimum executable threshold.

Operational source of truth:
- runtime/control
- runtime/ui
- runtime/ops

Operational commands:
- runtime/ops/start-clean.ps1
- runtime/ops/start-all.ps1
- runtime/ops/validate-all.ps1
- runtime/ops/validate.ps1

Rule:
Do not add new feature layers until every change preserves:
1. API OK
2. API action OK
3. Dashboard status OK
4. UI OK
5. Nexus runtime validation PASSED
