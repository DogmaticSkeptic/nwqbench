#!/usr/bin/env bash
set -euo pipefail

# Activate conda env (nwqp38 or fallback nwqpy38)
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  if conda activate nwqp38 2>/dev/null; then
    :
  elif conda activate nwqpy38 2>/dev/null; then
    :
  fi
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NWQBENCH_DIR="${ROOT_DIR}/../nwqbench"
OUT_DIR="${NWQBENCH_DIR}/nwq-control_bench"

mkdir -p "${OUT_DIR}"

# Temporary patched script for grover_search
TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

# Patch grover_search to accept argv for qubit count
GROVER_SRC="${NWQBENCH_DIR}/NWQ_Bench/grover_search/grover_search.py"
GROVER_TMP="${TMP_DIR}/grover_search.py"
GROVER_SRC_PATH="${GROVER_SRC}" GROVER_TMP_PATH="${GROVER_TMP}" python - <<'PY'
import os
from pathlib import Path
src = Path(os.environ["GROVER_SRC_PATH"])
dst = Path(os.environ["GROVER_TMP_PATH"])
text = src.read_text()
text = text.replace("#k = int(sys.argv[1])\nk=3", "k = int(sys.argv[1])")
dst.write_text(text)
PY

check_qasm_qubits() {
  local file="$1"
  local expected="$2"
  local count
  count="$(python -c "import re,sys; text=open(sys.argv[1],'r',errors='ignore').read(); m=re.search(r'\\bqreg\\s+\\w+\\[(\\d+)\\]', text) or re.search(r'\\bqubit\\[(\\d+)\\]\\s+\\w+', text); print(m.group(1) if m else '')" "$file")"
  if [[ -z "${count}" ]]; then
    echo "WARN: could not find qreg in ${file}"
    return 0
  fi
  if [[ "${count}" -ne "${expected}" ]]; then
    echo "ERROR: ${file} has ${count} qubits, expected ${expected}"
    return 1
  fi
  return 0
}

run_bench() {
  local bench="$1"
  local script="$2"
  local n="$3"
  local workdir="$4"
  local qasm_name="$5"
  local expect_qubits="$6"

  pushd "${workdir}" >/dev/null
  local before
  before="$(ls qasm 2>/dev/null || true)"
  python "${script}" "${n}"
  local after
  after="$(ls qasm 2>/dev/null || true)"
  popd >/dev/null

  # Copy generated QASM into output directory
  if [[ -f "${workdir}/qasm/${qasm_name}" ]]; then
    cp "${workdir}/qasm/${qasm_name}" "${OUT_DIR}/${bench}_n${n}.qasm"
    if [[ -n "${expect_qubits}" ]]; then
      check_qasm_qubits "${OUT_DIR}/${bench}_n${n}.qasm" "${expect_qubits}" || CHECK_FAILED=1
    fi
    return
  fi
  if [[ -f "${workdir}/qasm/${qasm_name}.qasm" ]]; then
    cp "${workdir}/qasm/${qasm_name}.qasm" "${OUT_DIR}/${bench}_n${n}.qasm"
    if [[ -n "${expect_qubits}" ]]; then
      check_qasm_qubits "${OUT_DIR}/${bench}_n${n}.qasm" "${expect_qubits}" || CHECK_FAILED=1
    fi
    return
  fi

  # Fall back to newest file created in this run
  if [[ -n "${after}" ]]; then
    local new_file
    new_file="$(comm -13 <(printf '%s\n' ${before} | sort) <(printf '%s\n' ${after} | sort) | head -n 1 || true)"
    if [[ -n "${new_file}" && -f "${workdir}/qasm/${new_file}" ]]; then
      cp "${workdir}/qasm/${new_file}" "${OUT_DIR}/${bench}_n${n}.qasm"
      echo "WARN: ${bench} n=${n} produced ${new_file}; copied as ${bench}_n${n}.qasm"
      if [[ -n "${expect_qubits}" ]]; then
        check_qasm_qubits "${OUT_DIR}/${bench}_n${n}.qasm" "${expect_qubits}" || CHECK_FAILED=1
      fi
      return
    fi
  fi
  # Fall back to most recent file in qasm directory
  if [[ -d "${workdir}/qasm" ]]; then
    local latest
    latest="$(ls -t "${workdir}/qasm" 2>/dev/null | head -n 1 || true)"
    if [[ -n "${latest}" && -f "${workdir}/qasm/${latest}" ]]; then
      cp "${workdir}/qasm/${latest}" "${OUT_DIR}/${bench}_n${n}.qasm"
      echo "WARN: ${bench} n=${n} used latest ${latest}; copied as ${bench}_n${n}.qasm"
      if [[ -n "${expect_qubits}" ]]; then
        check_qasm_qubits "${OUT_DIR}/${bench}_n${n}.qasm" "${expect_qubits}" || CHECK_FAILED=1
      fi
      return
    fi
  fi
  echo "WARN: expected output not found for ${bench} n=${n}"
}

CHECK_FAILED=0

for n in 4 5 6; do
  run_bench "bv" "${NWQBENCH_DIR}/NWQ_Bench/bv/bv.py" "${n}" "${NWQBENCH_DIR}/NWQ_Bench/bv" "bv_n${n}.qasm" "${n}"
  run_bench "grover" "${GROVER_TMP}" "${n}" "${NWQBENCH_DIR}/NWQ_Bench/grover_search" "grover_search_n${n}" "${n}"
  run_bench "ising" "${NWQBENCH_DIR}/NWQ_Bench/ising/ising.py" "${n}" "${NWQBENCH_DIR}/NWQ_Bench/ising" "ising_n${n}" "${n}"
  run_bench "qft" "${NWQBENCH_DIR}/NWQ_Bench/qft/qft.py" "${n}" "${NWQBENCH_DIR}/NWQ_Bench/qft" "qft_n${n}" "${n}"
  run_bench "vqe" "${NWQBENCH_DIR}/NWQ_Bench/vqe/vqe.py" "${n}" "${NWQBENCH_DIR}/NWQ_Bench/vqe" "vqe_n${n}" "${n}"
done

echo "QASM files written to: ${OUT_DIR}"
if [[ "${CHECK_FAILED}" -ne 0 ]]; then
  echo "ERROR: One or more benchmarks produced a different qubit count than requested."
  exit 1
fi
