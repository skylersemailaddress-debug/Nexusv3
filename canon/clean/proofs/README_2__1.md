# Step 5 — Operator

This adds Operator tooling under `assembly/ai/`.

## Setup (once)
PowerShell:
- `setx OPENAI_API_KEY "your_key_here"` (optional but recommended) citeturn0search1
- `pwsh -File tools/ai/SETUP_OPERATOR.ps1` installs the OpenAI Python SDK (`pip install openai`). citeturn0search0turn0search2

## Run triage
- `pwsh -File tools/ai/RUN_TRIAGE.ps1`

Outputs:
- `assembly/ai/out/triage_summary.md`
- `assembly/ai/out/triage_plan.json`
