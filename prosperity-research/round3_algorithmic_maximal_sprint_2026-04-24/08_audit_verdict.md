# Round 3 backtest-audit verdict — 2026-04-24

Auditor: `prosperity-4-backtest-auditor` (manual invocation).
Audit inputs: `07_dry_run_results.md`, trader source, `01_current_assumptions.md`.

## Checks

| Check | Result | Notes |
|---|---|---|
| Submission interface (`run` + `(orders, conversions, traderData)`) | PASS | Confirmed across 30k ticks on Round 2. |
| `bid()` defined, returns int | PASS | Returns 20; ignored outside Round 2. |
| No unsupported imports | PASS | Only `json`, `math`, `typing`, `datamodel`. |
| No reliance on class / global state across `run()` calls | PASS | All state goes through `traderData`. |
| Position-limit safety (worst-case aggregate rule) | PASS (structurally) | `_clip_buy` / `_clip_sell` cap both sides against `cap ± position`. Not stressed empirically in this sprint because the trader never traded on Round 2. |
| `traderData` under 50k chars | PASS | Defensive 8 KB self-cap; falls back to empty `seen_vouchers` if exceeded. |
| Deterministic output | PASS | No RNG, no time-based nondeterminism. |
| Voucher parity gate is an identity, not a statistical bet | PASS | Gates implement `max(S-K,0)` lower bound and `S` upper bound only. |
| Dry-run on non-Round-3 data produces zero misapplied orders | PASS | 0 orders on 30k Round 2 ticks. |
| Edge on Round 3 data | **NOT EVALUATED** | No Round 3 data in repo. |
| Baseline comparison on Round 3 data | **NOT EVALUATED** | No Round 3 data in repo. |
| Day-over-day robustness on Round 3 | **NOT EVALUATED** | No Round 3 data in repo. |
| Ablation evidence on Round 3 | **NOT EVALUATED** | No Round 3 data in repo. |
| Parameter-sensitivity evidence on Round 3 | **NOT EVALUATED** | No Round 3 data in repo. |

## Verdict: FLAG

Reason: the submission-interface backbone and the identity-bounded voucher
arbitrage gate are both correct by construction and proven non-crashing on
30,000 ticks of Round 2 data. No Round 3 data exists in this repo, so the
edge claim cannot be backtested. Promoting this to `SHIP` would require
fabricating Round 3 PnL evidence, which is explicitly forbidden.

### Ranked unresolved tests, in priority order

1. Verify the actual voucher symbol strings in Round 3 day `-2` against the
   two assumed prefixes. If neither matches, `_parse_voucher_strike` returns
   `None` and the trader silently does nothing on vouchers — a safety
   property, but also a total-miss failure mode.
2. Confirm voucher position limits and widen `DEFAULT_CAP_VOUCHER` toward the
   true limit once known. A cap of 20 is defensible as a safety floor but is
   likely far below the true limit.
3. Confirm the payoff mapping is in fact `max(S - K, 0)`. If it is not, the
   intrinsic-arb gate is the wrong inequality and must be re-derived.
4. Measure on Round 3 day `-2` how often the intrinsic-arb gate fires and at
   what edge. If zero fires, the alpha is falsified for this round and the
   trader collapses to a no-op; consider adding the strike-monotonicity gate.
5. If monotonicity violations do appear, flip `ENABLE_STRIKE_MONOTONICITY` to
   True and re-audit.
6. Only then consider layering a `HYDROGEL_PACKS` or `VELVET_FRUIT_EXTRACT`
   underlying strategy; until Round 3 data exists, those alphas are
   explicitly rejected.

## Submission readiness

- The candidate *is* submission-valid in the sense that it would run on the
  hosted venue without raising. It does NOT have a defensible expected-PnL
  claim. Submitting it as-is before Round 3 data is available would reduce
  to an experiment that logs whether vouchers ever trade below intrinsic.
- `prosperity-research/10_experiment_logs/current_best.md` was NOT created
  for Round 3. No candidate earned it.
