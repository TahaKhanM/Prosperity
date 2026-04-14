#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/environment.yml"
ENV_NAME="${1:-prosperity}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing environment file: ${ENV_FILE}" >&2
  exit 1
fi

if command -v conda >/dev/null 2>&1; then
  MANAGER_BIN="$(command -v conda)"
  MANAGER_NAME="conda"
elif command -v mamba >/dev/null 2>&1; then
  MANAGER_BIN="$(command -v mamba)"
  MANAGER_NAME="mamba"
elif command -v micromamba >/dev/null 2>&1; then
  MANAGER_BIN="$(command -v micromamba)"
  MANAGER_NAME="micromamba"
elif [[ -x "/opt/miniconda3/bin/conda" ]]; then
  MANAGER_BIN="/opt/miniconda3/bin/conda"
  MANAGER_NAME="conda"
elif [[ -x "$HOME/miniconda3/bin/conda" ]]; then
  MANAGER_BIN="$HOME/miniconda3/bin/conda"
  MANAGER_NAME="conda"
elif [[ -x "$HOME/anaconda3/bin/conda" ]]; then
  MANAGER_BIN="$HOME/anaconda3/bin/conda"
  MANAGER_NAME="conda"
else
  echo "No conda-compatible manager found. Install conda, mamba, or micromamba first." >&2
  exit 1
fi

cd "${ROOT_DIR}"

echo "Using ${MANAGER_NAME} with ${ENV_FILE}"
if ! "${MANAGER_BIN}" env create -f "${ENV_FILE}" -n "${ENV_NAME}" -y; then
  echo "Environment already exists or create failed; updating ${ENV_NAME} instead."
  "${MANAGER_BIN}" env update -f "${ENV_FILE}" -n "${ENV_NAME}" --prune
fi

echo
echo "Environment ready."
echo "Activate it with:"
if [[ "${MANAGER_NAME}" == "micromamba" ]]; then
  echo "  micromamba activate ${ENV_NAME}"
else
  echo "  conda activate ${ENV_NAME}"
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo
  echo "If you use the editable rust_backtester CLI from this env, also run:"
  echo '  export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"'
fi
