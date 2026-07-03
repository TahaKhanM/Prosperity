# official_replays

Logs and metrics pulled back from the official IMC submission environment,
kept as ground-truth reference for comparing local backtests against the real
exchange. These are read-only artifacts, not inputs to any build.

- `round3/` holds the Round 3 probe and strategy-version logs (matching and
  fill-granularity probes, plus versioned runs `v4` through `v15`).
- `round5/` holds the Round 5 pebble mean-reversion and basket logs.
- `v9/` is a standalone Round 3 v9 capture.

Directory names were normalized to snake_case during the post-competition
cleanup; the log contents are unchanged.
