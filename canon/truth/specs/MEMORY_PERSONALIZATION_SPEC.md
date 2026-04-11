# MEMORY AND PERSONALIZATION SPEC

## Purpose
Provide structured, policy-safe, confidence-aware continuity and deterministic adaptation.

## Memory layers
- session memory
- episodic memory
- stable profile memory
- policy memory
- goal graph
- failure memory

## Required components
- user model compiler
- personalization kernel
- contradiction detector
- memory governor
- confidence/decay scorer
- selective writeback controller
- initiative mode resolver
- abstraction resolver
- response contract generator

## Inputs
- current task
- recent episodes
- stable profile
- policy state
- workspace context
- confidence scores

## Outputs
- adaptation object
- initiative level
- blocked actions
- style contract
- memory write decisions

## Invariants
- policy memory separate from preference memory
- low-confidence memory cannot act as stable truth
- contradictions must be surfaced or downgraded
- writeback must be selective

## Tests required
- stale episodic memory isolation
- profile vs session conflict handling
- contradiction downgrade
- policy override behavior
- personalization determinism

## Done when
- personalization is driven by a deterministic kernel
- memory writes are reviewable, confidence-weighted, and policy-safe
