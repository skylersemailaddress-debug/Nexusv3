# Git / Codex Activation Next Step

## Current blocker
`C:\NexusV3` is not a Git repository, so:
- `git status` fails
- GitHub Actions cannot run from this folder
- Codex PR automation cannot attach to a remote repo yet

## Next exact sequence
1. `git init`
2. `git branch -M main`
3. `git add .`
4. `git commit -m "Nexus V3 technical path complete"`
5. create remote GitHub repo
6. `git remote add origin <REMOTE_URL>`
7. `git push -u origin main`

## After push
- enable branch protection on `main`
- require PRs
- require CI status checks
- connect secrets
