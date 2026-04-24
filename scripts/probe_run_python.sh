#!/usr/bin/env bash
# Run the probe trader on the Python (prosperity4bt) backtester for Round 3
# day 2 and capture stdout + the IMC-format output log.
#
# Outputs:
#   runs/probes/python_bt_stdout.log   raw stdout (PROBE lines + summary)
#   runs/probes/python_bt_output.json  prosperity4bt 3-section log (renamed .json
#                                      for symmetry with rust output; the file
#                                      itself is the prosperity4bt text format
#                                      with embedded JSON sections)

set -euo pipefail

ROOT="/Users/tahakhan/Documents/Work/Projects/Prosperity"
TRADER="${ROOT}/prosperity_rust_backtester/traders/Round3/probes/probe_v1_matching.py"
DATA_SRC="${ROOT}/Data/ROUND_3"
PY_BT="${ROOT}/imc-prosperity-4-backtester"
PY="/opt/miniconda3/envs/prosperity/bin/python"
OUT_DIR="${ROOT}/runs/probes"
STDOUT_LOG="${OUT_DIR}/python_bt_stdout.log"
OUTPUT_JSON="${OUT_DIR}/python_bt_output.json"

mkdir -p "${OUT_DIR}"

# prosperity4bt expects data laid out as <root>/round<N>/prices_round_<N>_day_<D>.csv.
# Stage Round 3 CSVs into a temp directory matching that shape.
DATA_STAGE="$(mktemp -d -t probe_pybt_data_XXXX)"
trap 'rm -rf "${DATA_STAGE}"' EXIT

mkdir -p "${DATA_STAGE}/round3"
cp "${DATA_SRC}"/prices_round_3_day_*.csv "${DATA_STAGE}/round3/"
cp "${DATA_SRC}"/trades_round_3_day_*.csv "${DATA_STAGE}/round3/"

echo "[probe_run_python] trader: ${TRADER}"
echo "[probe_run_python] data:   ${DATA_STAGE}/round3"
echo "[probe_run_python] out:    ${OUTPUT_JSON}"
echo "[probe_run_python] log:    ${STDOUT_LOG}"

# Verify prosperity4bt is importable in the chosen interpreter.
"${PY}" -c "import prosperity4bt" >/dev/null 2>&1 || {
    echo "[probe_run_python] prosperity4bt not importable in ${PY}; attempting editable install" >&2
    "${PY}" -m pip install -e "${PY_BT}" >&2
}

# Run on Round 3 day 2 only. --print streams trader stdout (PROBE lines) so we
# can capture them. --no-progress avoids tqdm bars in the log.
"${PY}" -m prosperity4bt \
    "${TRADER}" \
    3-2 \
    --data "${DATA_STAGE}" \
    --out "${OUTPUT_JSON}" \
    --print \
    --no-progress \
    > "${STDOUT_LOG}" 2>&1

probe_count=$(grep -c "^PROBE" "${STDOUT_LOG}" || true)
echo "[probe_run_python] done; PROBE lines captured: ${probe_count}"
echo "[probe_run_python] stdout log size: $(wc -c < "${STDOUT_LOG}") bytes"
echo "[probe_run_python] output log size: $(wc -c < "${OUTPUT_JSON}") bytes"
