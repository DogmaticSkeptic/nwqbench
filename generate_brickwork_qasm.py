#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path


def brickwork_cx_pairs(n: int, layer: int) -> list[tuple[int, int]]:
    start = 0 if layer % 2 == 0 else 1
    pairs = []
    for i in range(start, n - 1, 2):
        pairs.append((i, i + 1))
    return pairs


def _u3(theta: float, phi: float, lam: float) -> str:
    return f"u3({theta:.12f},{phi:.12f},{lam:.12f})"


def _su4_layer(lines: list[str], a: int, b: int, tweak: int) -> None:
    params = [
        (math.pi / 7, math.pi / 5, math.pi / 3),
        (math.pi / 11, math.pi / 4, math.pi / 6),
        (math.pi / 9, math.pi / 8, math.pi / 10),
        (math.pi / 13, math.pi / 7, math.pi / 12),
    ]
    p0 = params[(0 + tweak) % len(params)]
    p1 = params[(1 + tweak) % len(params)]
    p2 = params[(2 + tweak) % len(params)]
    p3 = params[(3 + tweak) % len(params)]
    # A simple SU(4) decomposition via 3 CX and interleaved single-qubit U3 gates.
    lines.append(f"{_u3(*p0)} q[{a}];")
    lines.append(f"{_u3(*p1)} q[{b}];")
    lines.append(f"cx q[{a}],q[{b}];")
    lines.append(f"{_u3(*p2)} q[{a}];")
    lines.append(f"{_u3(*p3)} q[{b}];")
    lines.append(f"cx q[{a}],q[{b}];")
    lines.append(f"{_u3(*p1)} q[{a}];")
    lines.append(f"{_u3(*p0)} q[{b}];")
    lines.append(f"cx q[{a}],q[{b}];")
    lines.append(f"{_u3(*p3)} q[{a}];")
    lines.append(f"{_u3(*p2)} q[{b}];")


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
    # Brickwork SU(4) layers (via U3 + CX decomposition)
    for layer in range(layers):
        for a, b in brickwork_cx_pairs(n, layer):
            _su4_layer(lines, a, b, tweak=layer + a + b)
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
