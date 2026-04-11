#!/usr/bin/env python3
"""
ODPv3 Operator: new_module.py

Generates patch candidates into:
assembly/ai/out/generated_patch/

This tool MUST NOT write into repo source directly.
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

OUT = Path("assembly/ai/out/generated_patch")
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    p = OUT / f"README_GENERATED_{stamp}.md"
    p.write_text(
        "# Generated Patch Placeholder\n\n"
        "Operator generation is not yet wired to real modules.\n"
        "When enabled, this folder will contain an overwrite-safe patch.\n",
        encoding="utf-8",
    )
    print("OK=1")
    print(f"OUT={OUT}")
    print(f"FILE={p}")

if __name__ == "__main__":
    main()
