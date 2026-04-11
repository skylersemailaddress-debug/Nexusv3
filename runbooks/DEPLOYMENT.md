# Deployment Runbook

## Pre-deploy
- package validation passes
- codex validation passes
- CI workflow green
- baseline snapshot created

## Deploy path
1. promote to staging
2. validate staging
3. approve production promotion
4. validate production

## Rollback
- restore latest baseline
- rerun validation
