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

has_python_dylib() {
    candidate="$1"
    [ -x "${candidate}" ] || return 1
    libdir="$("${candidate}" - <<'PY' 2>/dev/null
import sysconfig
print(sysconfig.get_config_var("LIBDIR") or "")
PY
)"
    [ -n "${libdir}" ] || return 1
    # PyO3 links against a real libpython*.dylib / libpython*.so.
    # macOS /usr/bin/python3 in some CLT installs omits this.
    ls "${libdir}"/libpython*.dylib "${libdir}"/libpython*.so 2>/dev/null \
        | head -n 1 | grep -q . || return 1
    return 0
}

pick_python() {
    # Resolution order, most specific first:
    #   1. $PYO3_PYTHON explicit override.
    #   2. Active venv / conda interpreter (if it has a dylib).
    #   3. Homebrew python3 with dylib.
    #   4. /Library/Frameworks/Python.framework newest version with dylib.
    #   5. Plain python3 on PATH (may fail to link, but matches legacy behavior).
    [ -n "${PYO3_PYTHON-}" ] && printf '%s\n' "${PYO3_PYTHON}" && return 0
    if [ -n "${VIRTUAL_ENV-}" ] && has_python_dylib "${VIRTUAL_ENV}/bin/python"; then
        printf '%s\n' "${VIRTUAL_ENV}/bin/python"
        return 0
    fi
    if [ -n "${CONDA_PREFIX-}" ] && has_python_dylib "${CONDA_PREFIX}/bin/python"; then
        printf '%s\n' "${CONDA_PREFIX}/bin/python"
        return 0
    fi
    for cand in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        has_python_dylib "${cand}" && printf '%s\n' "${cand}" && return 0
    done
    if [ -d /Library/Frameworks/Python.framework/Versions ]; then
        for version in $(ls -r /Library/Frameworks/Python.framework/Versions/ 2>/dev/null); do
            [ "${version}" = "Current" ] && continue
            cand="/Library/Frameworks/Python.framework/Versions/${version}/bin/python${version}"
            has_python_dylib "${cand}" && printf '%s\n' "${cand}" && return 0
        done
    fi
    fallback="$(command -v python3 2>/dev/null || printf '%s\n' python3)"
    printf '%s\n' "${fallback}"
}

pyo3_python="$(pick_python)"

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
