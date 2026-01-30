import sys
import os
import numpy as np
import math
from qiskit import QuantumCircuit

if len(sys.argv) < 2:
    print("Usage: python grover_search.py <num_qubits>")
    sys.exit(1)
k = int(sys.argv[1])

if k < 1:
    print("Number of qubits should be positive.")
    sys.exit(1)

qc = QuantumCircuit(k, k)

# Prepare uniform superposition
qc.h(range(k))

def phase_oracle_mark_all_ones(circuit):
    if k == 1:
        circuit.z(0)
        return
    circuit.h(k - 1)
    circuit.mcx(list(range(k - 1)), k - 1, mode="noancilla")
    circuit.h(k - 1)

def diffuser(circuit):
    circuit.h(range(k))
    circuit.x(range(k))
    if k == 1:
        circuit.z(0)
    else:
        circuit.h(k - 1)
        circuit.mcx(list(range(k - 1)), k - 1, mode="noancilla")
        circuit.h(k - 1)
    circuit.x(range(k))
    circuit.h(range(k))

# Number of Grover iterations for 1 marked state
iters = max(1, int(round(math.pi / 4 * math.sqrt(2 ** k))))
for _ in range(iters):
    phase_oracle_mark_all_ones(qc)
    diffuser(qc)

qc.measure(range(k), range(k))

new_circuit = qc
while True:
    old_circuit = new_circuit
    new_circuit = new_circuit.decompose()
    if old_circuit == new_circuit:
        break


if not os.path.isdir("qasm"):
    os.mkdir("qasm")
with open(f"qasm/grover_search_n{k}", "w") as qasm_file:
    qasm_file.write(new_circuit.qasm())

# qasm_sim = qiskit.Aer.get_backend('aer_simulator')
# qobj = qiskit.compiler.assemble(new_circuit, backend=qasm_sim,shots=1024)
# job = qasm_sim.run(qobj).result().get_counts()
# plot_histogram(result['measurement'])
# plot_histogram(job)
# plt.show()
