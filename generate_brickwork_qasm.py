#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def brickwork_cx_pairs(n: int, layer: int) -> list[tuple[int, int]]:
    start = 0 if layer % 2 == 0 else 1
    pairs = []
    for i in range(start, n - 1, 2):
        pairs.append((i, i + 1))
    return pairs


def build_brickwork_qasm(n: int, layers: int = 2) -> str:
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{n}];",
        f"creg c[{n}];",
    ]
    # Prepare |+>^n
    for i in range(n):
        lines.append(f"h q[{i}];")
    # Brickwork CX layers
    for layer in range(layers):
        for a, b in brickwork_cx_pairs(n, layer):
            lines.append(f"cx q[{a}],q[{b}];")
    # Measure all qubits
    for i in range(n):
        lines.append(f"measure q[{i}] -> c[{i}];")
    return "\n".join(lines) + "\n"


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "nwq-control_bench_brickwork"
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in (4, 5, 6):
        qasm = build_brickwork_qasm(n, layers=2)
        out_path = out_dir / f"brickwork_n{n}.qasm"
        out_path.write_text(qasm)
    print(f"Wrote brickwork QASM files to: {out_dir}")


if __name__ == "__main__":
    main()
