# Round 1 Hosted Market Dynamics v2

Date: 2026-04-15

Scope:

- official IMC bundles:
  - `round1_candidate_v2.zip`
  - `round1_overhaul_v14.zip`
  - `round1_overhaul_v16.zip`
  - `round1_overhaul_v22.zip`
  - `round1_probe_ash_microstructur.zip`
  - `round1_probe_pepper_microstructure.zip`
- local Round 1 public datasets under `prosperity_rust_backtester/datasets/round1`

## Highest-confidence hosted facts

1. The official `activitiesLog` book stream is identical across `candidate_v2`, `v14`, `v16`, `v22`, and the supplied probe zip.
   - Same product, same timestamp, same top-3 book, same mid.
   - Conclusion: in these hosted Round 1 runs, our strategy does not alter the future displayed market path.
   - What changes between submissions is capture, not path.

2. The two supplied probe zip files are byte-identical duplicates.
   - Both hashes are `27290f735b7b7fcc15f68c255b567243`.
   - Both contain the same `134035.py/.json/.log`.

3. Pepper is a carry path, not a hosted passive-fill market.
   - Official path from the hosted snapshots: roughly `11998.5 -> 12099.5`.
   - Average spread is about `13.7`.
   - Passive Pepper fills are extremely rare.
   - `v22` Pepper is already near the simple carry ceiling for an 80-lot limit.

4. Ash is where later hosted improvements come from.
   - `v14 -> v22` official gain is entirely Ash.
   - Hosted Ash economics are strongest for passive inside-spread fills.
   - Aggressive Ash takes still work, but they are secondary to inside spread capture.

## Implications for strategy design

- Treat hosted Round 1 as a fixed-path extraction problem.
- Do not spend engineering time on market-impact theories for the displayed future book.
- Do not chase a Pepper passive microstructure edge from these payloads; the evidence is not there.
- The remaining scalable Round 1 edge is better Ash quote translation:
  - earn more one-tick-inside Ash fills,
  - keep join/deep quotes subordinate,
  - preserve selective aggressive Ash takes.

## Candidate selection after local validation

Local full-bundle Round 1 comparison:

| Trader | Default Total | `queue_penetration=0.5` | `trade_match_mode=none` |
| --- | ---: | ---: | ---: |
| `round1_overhaul_v22.py` | 288401.0 | 269361.5 | 248290.0 |
| `round1_overhaul_v23.py` | 288718.0 | 269413.5 | 248290.0 |
| `round1_overhaul_v27.py` | 288740.0 | 269413.5 | 248290.0 |

Interpretation:

- `v27` is the best current local candidate.
- It improves on `v23` without weakening the stricter queue or no-passive-fill checks.
- The change is intentionally narrow and Ash-only.

## `v27` change summary

Relative to `v23`, `v27` only adjusts Ash passive buy behavior:

- allow Ash inside bids one spread tick earlier (`spread >= 15` instead of `>= 16`)
- keep Ash inside sells unchanged
- add a small size bump to the first Ash inside bid when that inside-bid condition is active

This matches the hosted evidence that Ash passive inside buys are one of the cleanest remaining monetization channels.
