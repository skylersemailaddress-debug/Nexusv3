# CRITIQUE REPAIR LOOP SPEC

## Purpose
Require multi-pass critique and repair before promotion.

## Required loop
1. build
2. critique
3. repair
4. re-validate
5. promote or reject

## Required components
- build artifact reviewer
- defect classifier
- repair planner
- regression checker
- promotion decision engine

## Invariants
- single-pass output cannot auto-promote
- repairs must be re-validated
- critique results must be stored

## Tests required
- failed build enters repair
- repaired build re-checked
- unchanged defects block promotion
