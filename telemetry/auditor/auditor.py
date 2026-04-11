from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    warnings: list[str] = []
    if (ROOT / '.venv').exists():
        warnings.append('forbidden .venv detected')
    if (ROOT / 'node_modules').exists():
        warnings.append('forbidden node_modules detected')

    if warnings:
        print('AUDITOR FOUND DRIFT')
        for item in warnings:
            print(f'- {item}')
        return 1

    print('AUDITOR CLEAN')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
