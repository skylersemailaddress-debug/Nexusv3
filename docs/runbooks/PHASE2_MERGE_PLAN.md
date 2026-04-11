# Phase 2 Merge Plan

## Objective
Select one primary source per canon role and preserve alternates for controlled extraction. No whole-repo merges.

## Recommended primaries by family
- autobuilder: autobuilder - Copy (3).zip [control_pack_doctrine] score=91
- autobuilder2.9: autobuilder2.9 (3).zip [integrated_control_plane_skeleton] score=105
- autobuilderv2: autobuilderv2 (4).zip [control_pack_doctrine] score=89
- Botomatic: Botomatic.zip [experimental_reference] score=73
- FrankCore: FrankCore.zip [conversation_shell_and_blocks] score=114
- FrankV2: FrankV2 (50).zip [conversation_shell_and_blocks] score=118
- Nexus: Nexus.zip [control_pack_doctrine] score=94
- Nexus2.8: Nexus2.8 (4).zip [transitional_api_runtime_reference] score=98
- Nexus2.9: Nexus2.9 (10).zip [integrated_control_plane_skeleton] score=123
- NexusV2: NexusV2 - Copy (5).zip [control_pack_doctrine] score=92
- NexusV3: NexusV3.zip [bootstrap_canon_repo] score=99
- ODP: ODP_clean (4).zip [assembly_and_release_proofs] score=107
- SkyGPTAgent: SkyGPTAgent (2).zip [continuity_and_operator_os] score=106
- SkylerGPTOS: SkylerGPTOS (3).zip [continuity_and_operator_os] score=81
- SkylerOS: skyler-os.zip [continuity_and_operator_os] score=107
- SkylerOS-Truth: SkylerOS-Truth (2).zip [truth_gap_methodology] score=121
- SkyOS: SkyOS (3).zip [continuity_and_operator_os] score=81
- SkyOSsplitoff: SkyOSsplitoff32526 - Copy (2).zip [continuity_and_operator_os] score=84

## Extraction order
- B1: truth <= SkylerOS-Truth :: truth docs, gaps, invariants, canon contracts
- B2: control-plane <= Nexus2.9 :: admin/control-plane API and runtime skeleton
- B3: conversation-shell <= FrankV2 :: operator shell and block UI patterns
- B4: proofs <= ODP :: assembly gates and release proofs
- B5: continuity <= SkylerOS :: continuity, operator OS, stateful memory concepts

## Deliverables
- phase2_repo_scores.csv
- phase2_selection_plan.json
- phase2_extraction_batches.json
- this merge plan
