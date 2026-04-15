#!/bin/sh
set -eu

os_name="$(uname -s)"
clean_path="${HOME}/.cargo/bin"
if [ -n "${VIRTUAL_ENV-}" ] && [ -d "${VIRTUAL_ENV}/bin" ]; then
    clean_path="${clean_path}:${VIRTUAL_ENV}/bin"
fi
if [ -n "${CONDA_PREFIX-}" ] && [ -d "${CONDA_PREFIX}/bin" ]; then
    clean_path="${clean_path}:${CONDA_PREFIX}/bin"
fi
clean_path="${clean_path}:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

effective_target_dir() {
    if [ -n "${CARGO_TARGET_DIR-}" ]; then
        printf '%s\n' "${CARGO_TARGET_DIR}"
        return
    fi

    case "${os_name}" in
        Darwin) printf '%s\n' "${HOME}/Library/Caches/rust_backtester/target" ;;
        *) printf '\n' ;;
    esac
}

case "${1-}" in
    --print-target-dir)
        effective_target_dir
        exit 0
        ;;
    --print-clean-path)
        printf '%s\n' "${clean_path}"
        exit 0
        ;;
esac

if [ "${os_name}" != "Darwin" ]; then
    exec cargo "$@"
fi

target_dir="$(effective_target_dir)"
if [ -n "${target_dir}" ]; then
    mkdir -p "${target_dir}"
fi

if [ -n "${PYO3_PYTHON-}" ]; then
    pyo3_python="${PYO3_PYTHON}"
elif [ -n "${VIRTUAL_ENV-}" ] && [ -x "${VIRTUAL_ENV}/bin/python" ]; then
    pyo3_python="${VIRTUAL_ENV}/bin/python"
elif [ -n "${CONDA_PREFIX-}" ] && [ -x "${CONDA_PREFIX}/bin/python" ]; then
    pyo3_python="${CONDA_PREFIX}/bin/python"
else
    pyo3_python="$(command -v python3 2>/dev/null || printf '%s\n' python3)"
fi

dyld_fallback_path="${DYLD_FALLBACK_LIBRARY_PATH-}"
python_lib_dir="$("${pyo3_python}" - <<'PY'
import sysconfig
print(sysconfig.get_config_var("LIBDIR") or "")
PY
)"
if [ -n "${python_lib_dir}" ]; then
    if [ -n "${dyld_fallback_path}" ]; then
        dyld_fallback_path="${python_lib_dir}:${dyld_fallback_path}"
    else
        dyld_fallback_path="${python_lib_dir}"
    fi
fi

exec env -i \
    HOME="${HOME}" \
    USER="${USER-}" \
    LOGNAME="${LOGNAME-${USER-}}" \
    PATH="${clean_path}" \
    TMPDIR="${TMPDIR-/tmp}" \
    TERM="${TERM-dumb}" \
    CARGO_TARGET_DIR="${target_dir}" \
    ${VIRTUAL_ENV+"VIRTUAL_ENV=${VIRTUAL_ENV}"} \
    ${CONDA_PREFIX+"CONDA_PREFIX=${CONDA_PREFIX}"} \
    ${CARGO_HOME+"CARGO_HOME=${CARGO_HOME}"} \
    ${RUSTUP_HOME+"RUSTUP_HOME=${RUSTUP_HOME}"} \
    ${HTTP_PROXY+"HTTP_PROXY=${HTTP_PROXY}"} \
    ${HTTPS_PROXY+"HTTPS_PROXY=${HTTPS_PROXY}"} \
    ${NO_PROXY+"NO_PROXY=${NO_PROXY}"} \
    ${SSL_CERT_FILE+"SSL_CERT_FILE=${SSL_CERT_FILE}"} \
    ${SSL_CERT_DIR+"SSL_CERT_DIR=${SSL_CERT_DIR}"} \
    PYO3_PYTHON="${pyo3_python}" \
    ${dyld_fallback_path+"DYLD_FALLBACK_LIBRARY_PATH=${dyld_fallback_path}"} \
    cargo "$@"
