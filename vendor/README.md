# vendor

Third-party tools the team adapted rather than wrote from scratch. They are
kept here, separate from the team's own work, so the provenance is clear.

- `imc-prosperity-4-backtester/` is a Python backtester adapted from
  [jmerle's Prosperity 3 backtester](https://github.com/jmerle/imc-prosperity-3-backtester).
  It reproduces the format of the official submission environment output and
  bundles reference round data under `prosperity4bt/resources/`.
- `imc-prosperity-4-visualizer/` is a web replay viewer adapted from jmerle's
  Prosperity 3 visualizer (MIT, Copyright Jasper van Merle). The `upstream`
  git remote points at the original repository.

The centerpiece Rust backtester is not here: it lives at the top level in
`prosperity_rust_backtester/`. That one is adapted from
[GeyzsoN's prosperity_rust_backtester](https://github.com/GeyzsoN/prosperity_rust_backtester),
with the team's traders and options tooling built on top.
