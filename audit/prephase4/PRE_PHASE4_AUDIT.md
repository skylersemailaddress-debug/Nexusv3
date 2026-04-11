# Pre-Phase-4 Audit: NexusV3 Canon Repo

## Executive verdict
The program is on track, but it is **not yet commercially locked** for Phase 4 extraction-by-implementation. The current repo is a strong governance and planning shell, not yet a clean integrated product/runtime codebase. The right move is **not** to start broad implementation extraction immediately. First lock the design with a small set of source-of-truth decisions and tighten the promotion rules.

Status:
- Program control: PASS
- Intake and quarantine discipline: PASS
- Phase sequencing: PASS
- Canon design lock: PARTIAL
- Commercial cleanliness: PARTIAL
- Build-readiness for broad Phase 4: HOLD UNTIL LOCKS APPLIED

## What is working
1. Canon/quarantine separation exists and is functioning.
2. Phase 1 intake succeeded and produced archive inventory and fingerprints.
3. Phase 2 scoring/selection exists and is internally consistent.
4. Phase 3 generated extraction plans, normalization map, conflict register, and canon stubs.
5. The repo is enforcing the correct principle: no whole-repo merges.

## What is not yet tight enough
1. **The repo is mostly scaffolding, not integrated implementation.**
   - The repo contains many directories for apps, engines, packs, tests, infra, and migrations, but a large share are empty placeholders.
   - The `src` tree contains extraction stubs, not actual promoted components.

2. **Phase 2 and Phase 3 diverge in source selection philosophy.**
   - Phase 2 extraction order implies a single primary per layer.
   - Phase 3 re-expands some layers into multi-source composites without enough lock rules.
   - This is acceptable for continuity, but dangerous for control-plane and shell unless narrowed.

3. **Continuity is under-constrained.**
   - Multiple continuity sources are planned simultaneously: SkyGPTAgent, SkylerGPTOS, SkylerOS, SkyOS, and SkyOSsplitoff.
   - This is the highest drift-risk area.
   - `SkyOS (3).zip` appears to be effectively placeholder-grade and should not remain an active target.

4. **Control-plane source mixing needs a strict boundary.**
   - `Nexus2.9` and `autobuilder2.9` are both targeting `control`.
   - This is correct only if one is runtime/API skeleton and the other is doctrine/control-pack material.
   - It is incorrect if both are allowed to compete as runtime authorities.

5. **Shell selection is still broader than necessary.**
   - `FrankV2` and `FrankCore` both target `shell`.
   - This is fine only if `FrankV2` is primary shell and `FrankCore` is component-reference-only.

6. **Commercial cleanliness is not yet proven.**
   - There is no integrated build proof for the canon tree.
   - No promoted app code exists in the canon `src` tree yet.
   - No end-to-end contract validation across truth/control/shell/proofs/continuity has happened.

## Repo-shape findings from direct inspection
- Total files: 113
- Total directories: 97
- Empty directories: 48
- Markdown files: 34
- PowerShell files: 33
- JSON files: 28
- Python files: 3
- TypeScript/TSX files promoted into canon tree: 0

Interpretation:
- This is a planning/governance-heavy bootstrap repo.
- It is commercially promising as a control-plane program shell.
- It is not yet a commercial product/runtime repo.

## Locked design decisions required before Phase 4
Apply these as law before any broad extraction:

### 1. Truth layer
- Primary: `SkylerOS-Truth (2).zip`
- Role: truth docs, invariants, gap methodology, contracts
- Rule: no alternate truth source

### 2. Control layer
- Runtime/API primary: `Nexus2.9 (10).zip`
- Doctrine/control-pack supplemental source: `autobuilder2.9 (3).zip`
- Rule: `autobuilder2.9` may contribute packs, gates, prompts, and policy artifacts; it may **not** become a parallel runtime authority.

### 3. Shell layer
- Primary shell: `FrankV2 (50).zip`
- Supplemental reference: `FrankCore.zip`
- Rule: `FrankCore` is reference/components only unless a specific component is proven superior.

### 4. Proof layer
- Primary: `ODP_clean (4).zip`
- Alternates: reference-only
- Rule: no parallel proof engines in canon.

### 5. Continuity layer
- Primary: `skyler-os.zip`
- Alternate/reference: `SkyGPTAgent (2).zip`
- Reference-only unless proven useful: `SkylerGPTOS (3).zip`, `SkyOSsplitoff32526 - Copy (2).zip`
- Exclude from active target list: `SkyOS (3).zip`
- Rule: continuity becomes one merged subsystem with one memory/state contract.

## Commercial cleanliness gates that should be added now
Before Phase 4 implementation extraction, require:
1. `DESIGN_LOCK.md` at repo root with the above locked primaries.
2. `PROMOTION_RULES.md` stating what each source family is allowed to contribute.
3. `EXCLUSION_LIST.json` for sources that are reference-only or excluded.
4. `CONTRACT_AUTHORITY.yaml` naming one authority for auth, state, execution graph, and memory schema.
5. `PHASE4_ENTRY_CHECKLIST.md` that fails if:
   - a layer has multiple runtime authorities,
   - excluded sources are still active extraction targets,
   - continuity lacks a single target contract,
   - shell lacks a single primary.

## Recommended hold points before Phase 4
Phase 4 should proceed **only after** these are true:
- one truth source locked
- one runtime/control authority locked
- one shell primary locked
- one proof primary locked
- one continuity primary locked
- placeholder continuity sources removed from active target list

## Go / no-go decision
Current recommendation: **GO with conditions**

Meaning:
- Do proceed toward Phase 4.
- Do **not** proceed with broad extraction until the design-lock and promotion-rule artifacts are written.

## Phase 4 should start with this narrow scope
1. Promote truth contracts from SkylerOS-Truth.
2. Promote runtime/control skeleton from Nexus2.9.
3. Promote shell structure from FrankV2.
4. Promote proof gates from ODP_clean.
5. Promote continuity contracts from SkylerOS only.
6. Pull only targeted references from autobuilder2.9, FrankCore, and SkyGPTAgent.

## Bottom line
The project is on track.
The repo is clean enough as a controlled bootstrap shell.
It is **not yet locked tightly enough** to call the design commercial-final.
The missing work is not more ideation; it is source-boundary discipline.

If those locks are added now, Phase 4 can start cleanly and with much lower drift risk.
