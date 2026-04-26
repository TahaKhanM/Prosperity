# Prosperity 4 Round 3 Current Assumptions

Date: 2026-04-24

Scope: authoritative Round 3 (GOAT) facts for the current checkout. Official
Prosperity written docs outrank repo tooling, narrative hints, and any older
public repo material. Local-tool notes below are verified against this
checkout and must not be promoted into live-mechanics truth.

Official rule sources used:
- `Prosperity Context/New Context/Round 3 Trading round.md`
- `Prosperity Context/New Context/Video Transcript.pdf`
- `Prosperity Context/Unrefined Context/Official Prosperity Context.md`

Local verification sources used:
- `prosperity_rust_backtester/README.md`
- `prosperity_rust_backtester/src/runner.rs` (post-R3 position limits patch)
- `prosperity_rust_backtester/datasets/round3/*.csv`
- `prosperity_rust_backtester/scripts/round3_options/*.py`
- `prosperity-research/03_eda/round3/voucher_panel.csv`
- `prosperity-research/04_signal_notes/round3/{parity_violations,vol_surface_coeffs,counterparty_scan}.csv`

## 1. Official facts (Round 3)

- **Phase**: GOAT (Great Orbital Ascension Trials). All prior PnL is reset.
- **Planet**: Salvinar. Round name: "Gloves Off".
- **Round cadence**: 48 hours per round, not 72.
- **Algorithmic products**:
  - `HYDROGEL_PACK` (delta-1, pos limit 200)
  - `VELVETFRUIT_EXTRACT` (delta-1 underlying, pos limit 200)
  - `VEV_{4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500}` — 10
    European call vouchers on VELVETFRUIT_EXTRACT, position limit 300 each.
- **Voucher mechanics**:
  - Shared expiry 7 rounds from Round 1 start; TTE = 5 days at Round 3 start.
  - Historical day 0/1/2 → TTE = 8/7/6.
  - Settlement: cash at `max(S_T - K, 0)` at expiry. Not exercisable early.
  - Inventory does NOT carry over into the next round (auto-liquidated).
- **Manual challenge (Round 3)**: Bio-Pods / Celestial Gardeners.
  Submit two bids. Gardener reserve prices are on multiples of 5. Resale
  value V = 920. Second-bid gate uses the global average second bid;
  probability collapses cubically below that average.
- **bid() function**: ignored outside Round 2. Can be included as noop.
- **Final submission of the round is scored.** Earlier drafts ignored.

## 2. Local tool behavior (verified 2026-04-24)

- **Rust position limits**: `prosperity_rust_backtester/src/runner.rs`
  now contains explicit limits for all Round 3 products (200/200/300).
  Round 1/2 products (ASH_COATED_OSMIUM, INTARIAN_PEPPER_ROOT) are retained
  at 80 for cross-version reference; they are not live in Round 3.
- **Round 3 dataset**: `prosperity_rust_backtester/datasets/round3/` has
  `prices_round_3_day_{0,1,2}.csv` and `trades_round_3_day_{0,1,2}.csv`,
  identical byte size to `Data/ROUND_3/` canon.
- **Auto-pick trader**: still nondeterministic. Pass `--trader` explicitly.
- **`latest` dataset alias**: do not use. Pass `--dataset round3` explicitly.
- **CSV ingestion**: does NOT load `observations_round_*` files — unchanged.
- **Conversions**: recorded but not simulated — unchanged.
- **Python backtester**: unknown-product fallback limit remains 50, so
  VEV_* strikes are currently under-sized under the Python path (confirm
  Python backtester has Round 3 product table before relying on it).
- **Options toolkit**: `scripts/round3_options/{bs, build_voucher_panel,
  vol_surface_fit, parity_scan, counterparty_scan, stat_tests}.py` all
  execute cleanly on the Round 3 historical dataset.

## 3. EDA findings (from the 2026-04-24 alpha hunt, axes A–O)

See `prosperity-research/09_master_reports/round3_alpha_hunt_2026-04-24.md`
for full detail. Top-line facts:

- **HYDROGEL_PACK** centre is **9991**, not 10000. Only 13.8 % of ticks
  within ±5 of 10000; mid persistence ρ₁ = 0.997; OU half-life ≈ 300 ticks;
  Hurst ≈ 0.47. Treat as slow OU, not a pin. Also shows a ~3330-tick
  spectral rhythm (~19.5 seashells peak-to-peak) that is not yet exploited.
- **VELVETFRUIT_EXTRACT** drifts slowly ~5250. Wall-mid (levels with
  qty ≥ 20) predicts 1-tick Δmid with slope 0.77, t = 39 across 3 days.
- **Voucher smile** fits `IV(m) = a0 + a1·m + a2·m²` cleanly, with
  deterministic TTE drift: ATM IV 0.242 → 0.247, skew −0.011 → −0.161,
  convexity 7.21 → 8.84 as TTE 8d → 6d.
- **Deep-OTM vouchers** (VEV_6000, VEV_6500) stuck at ~0.5 all days.
  Selling them naked has trivial downside given z(S > 6000 | 5d) ~ 4.4.
- **Deep-ITM vouchers** (VEV_4000, VEV_4500) carry zero time value (median
  TV = 0, 90 % of VEV_4000 ticks have TV ≤ 0, min TV = −7). They are
  synthetic delta-1 proxies. +600 VE-equivalent capacity available.
- **Parity (tradeable side)**: 0–2 floor violations per 10,000 ticks at
  edge ≥ 1 seashell. Zero cap / monotonicity / butterfly. Chain is clean.
- **Counterparty scan**: all historical trades anonymous (0 named parties
  across 4,049 trades). Counterparty copy is a live-only hook.
- **Order-book imbalance (top-2 levels)**: predicts 1-tick return with
  t ≈ 35 on HYDROGEL, t ≈ 20 on VE. k=3 flips sign (level-3 adversarial).
- **Spectral / seasonality**: no planted sub-100-tick seasonality. No EOD
  squeeze. HYDROGEL 3330-tick rhythm is the only non-trivial finding.
- **Ship-now alphas**: A1, B1, C1 (top-tier), G1 (defensive guard).
  Research-more: D1 (IV scalp), E1 (deep-ITM overlay), L1 (TTE carry),
  F1 (counterparty live hook).

## 4. Known unknowns

- Exact reserve-price distribution of Celestial Gardeners (cluster
  boundaries, exact multiples). Addressed via (b1, b2) = (907, 915)
  under a conservative prior.
- Whether a planted "smart bot" counterparty emerges in VE or VEV_*
  trades during live Round 3. Run `counterparty_scan.py` on every
  submission's trades to detect.
- Whether the voucher chain exhibits any intra-day seasonality that
  would justify switching pricing model mid-round.
- The exact fair-value estimator for HYDROGEL_PACK — currently assume
  10000 but confirm with `anchor_guard = 5`.

## 5. Non-transferable by rule

- Do not use ASH_COATED_OSMIUM or INTARIAN_PEPPER_ROOT traders for Round 3.
  They do not trade the live products.
- Do not rely on Round 2 `bid()` logic. Irrelevant in Round 3.
- Do not assume hosted conversion behavior when the tooling flags it as
  unsimulated.

## 6. Shipping constraints

- Preserve `(orders, conversions, traderData)` return shape.
- Keep traderData < 50,000 characters.
- One dominant change per iteration; declare the specific backtest that
  validates it.
- Do not mix HYDROGEL_PACK, VELVETFRUIT_EXTRACT, and voucher logic in one
  monolithic tick function — use product-keyed sub-strategies.
