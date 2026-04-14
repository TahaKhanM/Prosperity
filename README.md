# Prosperity

## Conda Environment

The repo root now includes a shared conda environment spec at
[environment.yml](/Users/tahakhan/Documents/Work/Projects/Prosperity/environment.yml).

It is set up for the active Python work in:

- [imc-prosperity-4-backtester](/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester)
- [prosperity_rust_backtester](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester)

From the repo root, create or update the environment with:

```bash
./scripts/setup_conda_env.sh
```

If you want a different environment name:

```bash
./scripts/setup_conda_env.sh my-env-name
```

The setup script works with `conda`, `mamba` or `micromamba`.

After activation, macOS users should export the conda env's `lib/` directory
before calling the editable Rust CLI installed from
[prosperity_rust_backtester](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester):

```bash
export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
```

This is not needed for the Python packages themselves, but it avoids a dynamic
linker error when invoking `rust_backtester` from the conda environment.
