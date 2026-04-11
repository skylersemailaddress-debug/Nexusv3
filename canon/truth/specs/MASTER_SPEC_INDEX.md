# MASTER SPEC INDEX

## Purpose
This index is the authoritative entrypoint for unfinished-but-required Nexus subsystems.

## Required spec domains
- runtime_authority
- control_plane
- memory_personalization
- capability_router
- operator_execution
- ui_product_intelligence
- full_stack_launchability
- telemetry_evolution
- enterprise_hardening
- product_completion

## Rules
1. These specs outrank repo ambiguity.
2. No implementation may create a second authority for runtime, auth, state, or execution graph.
3. Missing behavior should be added by spec extension, not repo guessing.
4. Every subsystem must define:
   - purpose
   - authority
   - inputs
   - outputs
   - invariants
   - required components
   - required tests
   - proof of done
