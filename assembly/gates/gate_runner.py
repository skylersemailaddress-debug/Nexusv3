from __future__ import annotations
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    failures: list[str] = []
    required = [
        ROOT / 'docs' / 'doctrine' / 'MERGE_POLICY.md',
        ROOT / 'docs' / 'doctrine' / 'HYGIENE_POLICY.md',
        ROOT / 'tools' / 'canon' / 'compile.py',
    ]
    for path in required:
        if not path.exists():
            failures.append(f'missing required gate dependency: {path}')

    if failures:
        print('GATE RUN FAILED')
        for item in failures:
            print(f'- {item}')
        return 1

    print('GATE RUN PASSED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
