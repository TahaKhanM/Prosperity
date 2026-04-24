#!/usr/bin/env bash
# Run the probe trader on the Rust backtester for Round 3 day 2 and capture
# its stdout (terminal summary) plus the IMC-format submission.log JSON.
#
# Outputs:
#   runs/probes/rust_bt_stdout.log   raw rust_backtester terminal output
#   runs/probes/rust_bt_output.json  IMC-format JSON (submissionId,
#                                    activitiesLog, logs[*], tradeHistory[*])

set -euo pipefail

ROOT="/Users/tahakhan/Documents/Work/Projects/Prosperity"
RUST_BT="${ROOT}/prosperity_rust_backtester"
TRADER="${RUST_BT}/traders/Round3/probes/probe_v1_matching.py"
DATASET_DIR="${RUST_BT}/datasets/round3"
OUT_DIR="${ROOT}/runs/probes"
STDOUT_LOG="${OUT_DIR}/rust_bt_stdout.log"
OUTPUT_JSON="${OUT_DIR}/rust_bt_output.json"
RUN_ID="probe_v1_matching_round3_day2"
TMP_RUN_ROOT="$(mktemp -d -t probe_rustbt_XXXX)"
trap 'rm -rf "${TMP_RUN_ROOT}"' EXIT

mkdir -p "${OUT_DIR}"

# Verify the dataset is in place.
if [[ ! -f "${DATASET_DIR}/prices_round_3_day_2.csv" ]]; then
    echo "[probe_run_rust] missing dataset: ${DATASET_DIR}/prices_round_3_day_2.csv" >&2
    exit 1
fi

# pyo3 needs a Python with libpython.dylib; conda env has one.
PYO3_PY="/opt/miniconda3/envs/prosperity/bin/python"
PY_LIBDIR="$("${PYO3_PY}" -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR") or "")')"

# Pick the release binary if present; otherwise fall back to debug.
BIN="${RUST_BT}/target/release/rust_backtester"
if [[ ! -x "${BIN}" ]]; then
    BIN="${RUST_BT}/target/debug/rust_backtester"
fi
if [[ ! -x "${BIN}" ]]; then
    echo "[probe_run_rust] rust_backtester binary not found; run 'make build-release' under ${RUST_BT}" >&2
    exit 1
fi

echo "[probe_run_rust] trader:  ${TRADER}"
echo "[probe_run_rust] dataset: ${DATASET_DIR} (day=2)"
echo "[probe_run_rust] bin:     ${BIN}"
echo "[probe_run_rust] out:     ${OUTPUT_JSON}"
echo "[probe_run_rust] log:     ${STDOUT_LOG}"

DYLD_FALLBACK_LIBRARY_PATH="${PY_LIBDIR}" \
PYO3_PYTHON="${PYO3_PY}" \
    "${BIN}" \
        --trader "${TRADER}" \
        --dataset round3 \
        --day 2 \
        --artifact-mode submission \
        --output-root "${TMP_RUN_ROOT}" \
        --run-id "${RUN_ID}" \
        > "${STDOUT_LOG}" 2>&1

# The rust BT writes <output-root>/<run-id>/submission.log. Move it to the
# canonical name.
SRC_LOG="${TMP_RUN_ROOT}/${RUN_ID}/submission.log"
if [[ ! -f "${SRC_LOG}" ]]; then
    echo "[probe_run_rust] missing submission.log at ${SRC_LOG}; rust BT failed" >&2
    cat "${STDOUT_LOG}" >&2
    exit 1
fi
cp "${SRC_LOG}" "${OUTPUT_JSON}"

# Count PROBE lines embedded in lambdaLog.
probe_count=$(/opt/miniconda3/envs/prosperity/bin/python -c "
import json
with open('${OUTPUT_JSON}') as f:
    data = json.load(f)
n = sum(1 for l in data.get('logs', []) if 'PROBE' in (l.get('lambdaLog') or ''))
print(n)
")
echo "[probe_run_rust] done; PROBE-bearing lambdaLog entries: ${probe_count}"
echo "[probe_run_rust] stdout log size: $(wc -c < "${STDOUT_LOG}") bytes"
echo "[probe_run_rust] output log size: $(wc -c < "${OUTPUT_JSON}") bytes"
