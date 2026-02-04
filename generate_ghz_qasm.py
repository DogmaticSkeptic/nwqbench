#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def build_ghz_qasm(n: int) -> str:
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{n}];",
        f"creg c[{n}];",
    ]
    lines.append("h q[0];")
    for i in range(n - 1):
        lines.append(f"cx q[{i}],q[{i+1}];")
    for i in range(n):
        lines.append(f"measure q[{i}] -> c[{i}];")
    return "\n".join(lines) + "\n"


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "nwq-control_bench_ghz"
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in (4, 5, 6, 7, 8, 9):
        qasm = build_ghz_qasm(n)
        out_path = out_dir / f"ghz_n{n}.qasm"
        out_path.write_text(qasm)
    print(f"Wrote GHZ QASM files to: {out_dir}")


if __name__ == "__main__":
    main()
