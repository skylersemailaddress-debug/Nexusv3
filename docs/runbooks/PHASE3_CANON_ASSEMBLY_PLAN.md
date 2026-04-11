# Phase 3 Canon Assembly Plan

## Objective
Create the first canon tree from Phase 2 winners without whole-repo merges.

## Targets
- control <= autobuilder2.9 (3).zip [autobuilder2.9]
- shell <= FrankCore.zip [FrankCore]
- shell <= FrankV2 (50).zip [FrankV2]
- control <= Nexus2.9 (10).zip [Nexus2.9]
- proofs <= ODP_clean (4).zip [ODP]
- continuity <= SkyGPTAgent (2).zip [SkyGPTAgent]
- continuity <= SkylerGPTOS (3).zip [SkylerGPTOS]
- continuity <= skyler-os.zip [SkylerOS]
- truth <= SkylerOS-Truth (2).zip [SkylerOS-Truth]
- continuity <= SkyOS (3).zip [SkyOS]
- continuity <= SkyOSsplitoff32526 - Copy (2).zip [SkyOSsplitoff]

## Normalization requirements
- auth: unify_before_promotion (single_contract_required)
- state: unify_before_promotion (single_runtime_truth)
- execution_graph: unify_before_promotion (single_execution_graph_root)
- memory_schema: normalize_before_promotion (tiered_memory_contract)

## Active conflicts
- Nexus2.9: duplicate_control_plane_variants :: primary_locked_alternate_quarantined
- SkyGPTAgent: duplicate_continuity_variants :: primary_locked_alternate_quarantined
- ODP: multiple_proof_variants :: primary_locked_alternates_reference_only

## Deliverables
- phase3_extraction_plan.json
- phase3_normalization_map.json
- phase3_conflict_register.json
- extraction stubs under src\*
