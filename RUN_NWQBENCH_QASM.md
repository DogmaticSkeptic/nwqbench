How To Run NWQBench QASM Generation (Conda)

This guide explains how to create the conda environment and run the QASM
generation script:

Script:
- `generate_nwqbench_qasm.sh`

Output directory:
- `nwq-control_bench/`

Prerequisites
- Conda installed (Miniconda/Anaconda)

1) Create and activate the conda environment

The script will try to activate `nwqp38` first and then fall back to
`nwqpy38`. You can use either name. Recommended:

```
conda create -n nwqp38 python=3.8 -y
conda activate nwqp38
```

2) Install Python dependencies

From the NWQBench root directory:

```
pip install -r requirements.txt
```

3) Run the generator

From the NWQBench root directory:

```
./generate_nwqbench_qasm.sh
```

What it does
- Generates QASM for 4/5/6 qubits for: bv, grover, ising, qft, vqe
- Writes results into `nwq-control_bench/`
- Grover is generated without ancilla qubits

Notes
- If you used a different env name, edit the script or activate your env
  before running it.
- The script may print circuit diagrams and deprecation warnings from qiskit;
  these do not affect the generated QASM.
