# COMPUTER-USE OPERATOR SPEC

## Purpose
Execute bounded real-world digital work across APIs, browser, files, and desktop fallbacks.

## Required components
- action router
- API-first execution path
- browser execution path
- desktop fallback path
- verification loop
- recovery loop
- checkpoint/resume engine
- trust calibration
- action classes
- domain workflow packs

## Inputs
- action request
- workspace permissions
- environment state
- approval state
- prior checkpoints

## Outputs
- verified action result
- recovery steps
- checkpoints
- operator proofs

## Invariants
- verify before declaring success
- recovery before abandonment when safe
- trust/risk class must be attached to action
- domain workflows must be bounded by policy

## Tests required
- browser change recovery
- missing login handling
- stale layout recovery
- API-first success path
- checkpoint resume after interruption

## Done when
- the operator stack can execute and recover across multi-step workflows with proofs
