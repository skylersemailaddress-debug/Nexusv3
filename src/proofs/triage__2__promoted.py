#!/usr/bin/env python3
"""
ODPv3 Operator: triage.py

Reads latest FAILURE_PACKET and writes:
- assembly/ai/out/triage_summary.md
- assembly/ai/out/triage_plan.json

Fail-closed principle:
- If OPENAI_API_KEY is missing, still writes a useful local summary and a conservative plan.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

OUT_DIR = Path("assembly/ai/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def find_latest_run(out_root: Path) -> Path | None:
    if not out_root.exists():
        return None
    runs = [p for p in out_root.iterdir() if p.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0]

def load_failure_packet(run_dir: Path) -> dict:
    fp = run_dir / "FAILURE_PACKET"
    if not fp.exists():
        return {"has_failure_packet": False}

    fail_reason = read_text(fp / "FAIL_REASON.txt").strip()
    failure_json_path = fp / "failure.json"
    failure = {}
    if failure_json_path.exists():
        try:
            failure = json.loads(read_text(failure_json_path))
        except Exception:
            failure = {}

    return {
        "has_failure_packet": True,
        "fail_dir": str(fp),
        "fail_reason": fail_reason,
        "failure_json": failure,
        "stdout": read_text(fp / "stdout.log"),
        "stderr": read_text(fp / "stderr.log"),
        "repro": read_text(fp / "repro.ps1"),
    }

def local_summary(payload: dict) -> str:
    if not payload.get("has_failure_packet"):
        return "No FAILURE_PACKET found in latest run.\n"

    failure = payload.get("failure_json") or {}
    stage = failure.get("stage", "(unknown stage)")
    inv = failure.get("invariant_id", "(unknown invariant)")
    msg = failure.get("message") or payload.get("fail_reason") or "(no message)"
    repro = payload.get("repro", "").strip()

    lines = []
    lines.append("# Operator Triage Summary\n")
    lines.append(f"- **Stage:** `{stage}`")
    lines.append(f"- **Invariant:** `{inv}`")
    lines.append(f"- **Message:** {msg}")
    lines.append("")
    if repro:
        lines.append("## Repro")
        lines.append("```powershell")
        lines.append(repro)
        lines.append("```")
        lines.append("")
    lines.append("## Next actions (conservative)")
    if "INV-NOT-IMPLEMENTED" in msg:
        lines.append("- Expected until Phase 7A (vertical slice).")
        lines.append("- No action required unless it appears in an unexpected stage.")
    else:
        lines.append("- Run the repro script and confirm the failure is stable.")
        lines.append("- Identify which invariant is violated and fix at the lowest layer.")
    lines.append("")
    return "\n".join(lines)

def build_plan(payload: dict) -> dict:
    if not payload.get("has_failure_packet"):
        return {"schema_version": "triage_plan.v1", "status": "no_failure_packet", "actions": []}

    failure = payload.get("failure_json") or {}
    msg = (failure.get("message") or payload.get("fail_reason") or "").strip()
    stage = failure.get("stage", "")

    actions = []
    if "INV-NOT-IMPLEMENTED" in msg:
        actions.append({
            "id": "PLAN-0001",
            "title": "No-op: expected not-implemented gate",
            "details": "Proceed with next step in roadmap; keep assembly line plumbing intact.",
            "files": []
        })
    else:
        actions.append({
            "id": "PLAN-0001",
            "title": "Reproduce failure",
            "details": "Run FAILURE_PACKET/repro.ps1 and capture stdout/stderr paths.",
            "files": ["FAILURE_PACKET/repro.ps1"]
        })
        actions.append({
            "id": "PLAN-0002",
            "title": "Fix invariant",
            "details": f"Fix invariant failure at stage {stage} without breaking determinism laws.",
            "files": []
        })

    return {
        "schema_version": "triage_plan.v1",
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "actions": actions,
    }

def maybe_ai_enhance(summary_md: str, payload: dict) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return summary_md

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = (
            "You are ODPv3 Operator. Produce a concise triage note.\n"
            "Rules:\n"
            "- Do not invent files.\n"
            "- Refer to invariant_id and stage.\n"
            "- Provide 3-7 bullet action plan.\n\n"
            f"Failure JSON:\n{json.dumps(payload.get('failure_json') or {}, indent=2)}\n\n"
            f"FAIL_REASON:\n{payload.get('fail_reason','')}\n"
        )
        resp = client.responses.create(
            model="gpt-5.2",
            input=prompt,
        )
        ai_text = (getattr(resp, "output_text", None) or "").strip()
        if ai_text:
            return summary_md + "\n\n---\n\n## AI Addendum\n\n" + ai_text + "\n"
    except Exception as e:
        return summary_md + f"\n\n---\n\n## AI Addendum (failed)\n\n{type(e).__name__}: {e}\n"

    return summary_md

def main() -> None:
    repo = Path(".")
    out_root = repo / "out" / "_runs"
    run_dir = find_latest_run(out_root)
    if not run_dir:
        die("NO_RUNS_FOUND: out/_runs is empty")

    payload = load_failure_packet(run_dir)

    summary = local_summary(payload)
    summary = maybe_ai_enhance(summary, payload)
    plan = build_plan(payload)

    (OUT_DIR / "triage_summary.md").write_text(summary, encoding="utf-8")
    (OUT_DIR / "triage_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

    print("OK=1")
    print(f"LATEST_RUN={run_dir}")
    if payload.get("has_failure_packet"):
        print(f"FAILURE_PACKET={payload.get('fail_dir')}")
    print(f"OUT_SUMMARY={OUT_DIR / 'triage_summary.md'}")
    print(f"OUT_PLAN={OUT_DIR / 'triage_plan.json'}")

if __name__ == "__main__":
    main()
