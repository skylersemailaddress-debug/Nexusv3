from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    failures: list[str] = []
    required = [
        ROOT / 'canon' / 'invariants' / 'INVARIANTS.md',
        ROOT / 'canon' / 'contracts' / 'RUNTIME_CONTRACT.yaml',
        ROOT / 'canon' / 'contracts' / 'AUTH_CONTRACT.yaml',
        ROOT / 'canon' / 'contracts' / 'EXECUTION_GRAPH_CONTRACT.yaml',
        ROOT / 'tools' / 'canon' / 'rules' / 'invariants.yaml',
        ROOT / 'tools' / 'canon' / 'rules' / 'contracts.yaml',
        ROOT / 'tools' / 'canon' / 'rules' / 'forbidden_patterns.yaml',
    ]
    for path in required:
        if not path.exists():
            failures.append(f'missing required canon file: {path}')

    for forbidden in [ROOT / '.venv', ROOT / 'node_modules']:
        if forbidden.exists():
            failures.append(f'forbidden path present: {forbidden}')

    if failures:
        print('CANON COMPILE FAILED')
        for item in failures:
            print(f'- {item}')
        return 1

    print('CANON COMPILE PASSED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
