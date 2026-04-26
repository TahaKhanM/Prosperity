# Prosperity 4 Round 4 Current Assumptions

Date: 2026-04-26

Scope: authoritative Round 4 (GOAT) facts for the current checkout. Official
Prosperity written docs outrank repo tooling, narrative hints, and any
older public repo material. Local-tool notes below are verified against
this checkout and must not be promoted into live-mechanics truth.

Prior version archived at
`prosperity-research/01_assumptions/archive/current_assumptions_2026-04-24_round3.md`.

Official rule sources used:
- `Prosperity Context/New Context/Round 4 Trading round.md`
- `Prosperity Context/New Context/Round 4 ARIA Uplink.md`
- `Prosperity Context/New Context/Round 4 Hint Cards.md`
- `Prosperity Context/Unrefined Context/Official Prosperity Context.md`

Local verification sources used:
- `prosperity_rust_backtester/README.md`
- `prosperity_rust_backtester/src/runner.rs::position_limit` (R3 product set,
  unchanged for R4)
- `prosperity_rust_backtester/datasets/round4/*.csv`
- `prosperity_rust_backtester/scripts/round4_options/*.py`
- `prosperity-research/03_eda/round4/{voucher_panel,headline_findings,counterparty_summary}.{csv,md}`
- `prosperity-research/04_signal_notes/round4/{parity_violations,vol_surface_coeffs,counterparty_scan,counterparty_findings}.{csv,md}`

## 1. Official facts (Round 4)

- **Phase**: GOAT (Great Orbital Ascension Trials). PnL was reset at the
  start of Round 3; Rounds 3 and 4 PnL accumulate on the same ledger.
- **Planet**: Salvinar. Round name: **"The More The Merrier"**.
- **Round cadence**: 48 hours per round.
- **Algorithmic products** (unchanged from Round 3):
  - `HYDROGEL_PACK` (delta-1, pos limit 200)
  - `VELVETFRUIT_EXTRACT` (delta-1 underlying, pos limit 200)
  - `VEV_{4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500}` —
    10 European call vouchers on `VELVETFRUIT_EXTRACT`, position limit
    300 each.
- **Voucher mechanics**:
  - Shared expiry. **TTE = 4 days at start of live Round 4.**
  - Historical day 1 / 2 / 3 (`prices_round_4_day_*.csv`) → TTE = 7 / 6 / 5.
  - Settlement: cash at `max(S_T - K, 0)` at expiry. Not exercisable early.
  - Inventory does NOT carry over into the next round (auto-liquidated).
- **Counterparty disclosure (NEW for Round 4)**: every other participant in
  the market is now named `Mark <NN>`. The historical CSVs show 7 distinct
  Marks: Mark 01, 14, 22, 38, 49, 55, 67. The `Trade.buyer` and
  `Trade.seller` fields are populated with these strings on
  `state.market_trades` and `state.own_trades`.
- **Manual challenge (Round 4)**: Aether Crystal vanilla + 3 exotic options.
  Independent of the algorithmic trader. Submit once before the round
  timer expires; final manual submission counts.
  - **Chooser**: K=50 XIRECS, expiry 21 Solvenarian days, decision day 14.
    Auto-converts to whichever of call/put is in-the-money at the decision
    date.
  - **Binary put**: K=40, expiry 21 days. Pays 10 if `S_T < 40`, else 0.
  - **Knockout (down-and-out) put**: K=45, barrier 35, expiry 21 days.
    Settles as a regular put with K=45 iff the underlying never touches
    the barrier; worthless on first breach.
  - Vanilla calls and puts on Aether Crystal also available; full chain
    surfaced only in the Manual Challenge UI.
- **bid() function**: ignored outside Round 2. Can be included as no-op.
- **Final submission of the round is scored.** Earlier drafts ignored.

## 2. Local tool behavior (verified 2026-04-26)

- **Rust position limits**: `prosperity_rust_backtester/src/runner.rs`
  contains explicit limits for all R3/R4 products (200/200/300). Round
  1/2 products (ASH_COATED_OSMIUM, INTARIAN_PEPPER_ROOT) retained at 80
  for cross-version reference; not live in R3+.
- **Round 4 dataset**: `prosperity_rust_backtester/datasets/round4/` has
  `prices_round_4_day_{1,2,3}.csv` and `trades_round_4_day_{1,2,3}.csv`,
  identical byte size to `Data/ROUND_4/` canon.
- **Counterparty fields ingested correctly**: confirmed via
  `traders/Round4/round4_mark_observer.py` smoke run; the
  trader_data persisted at end of day 1 contains non-zero per-product
  `mark_lean` values, proving Mark IDs reach trader code. (Run timestamp
  2026-04-26 ~15:50.)
- **`make round4` target wired**: existing Makefile already had `round4`
  and `round4-submission` targets; no change required.
- **Auto-pick trader**: still nondeterministic. Pass `--trader` explicitly.
- **`latest` dataset alias**: do not use. Pass `--dataset round4` explicitly.
- **CSV ingestion**: does NOT load `observations_round_*` files — unchanged.
- **Conversions**: recorded but not simulated — unchanged.
- **Python backtester**: unknown-product fallback limit remains 50, so
  VEV_* strikes are currently under-sized under the Python path (confirm
  Python backtester has Round 3/4 product table before relying on it).
- **Round 4 options toolkit**: `scripts/round4_options/{bs,
  build_voucher_panel, vol_surface_fit, parity_scan, counterparty_scan,
  exotic_pricers, stat_tests}.py` all execute cleanly on the Round 4
  dataset. Verified outputs:
  - voucher panel: 30,000 rows.
  - vol surface: 30,000 ticks fitted; ATM IV 0.119–0.276 (median 0.239),
    skew −0.131, convexity 8.81.
  - parity scan: 11,849 floor mid-violations (mostly K=4500), 6 butterfly
    violations across 30,000 ticks. Floor "violations" are the same R3
    deep-ITM mid-below-intrinsic artefact and are NOT tradeable on the ask.
  - counterparty scan: 137 (day, product, Mark, side) rows; 210 temporal
    rows. Auto-classification ranks Mark 14 = SMART (+5.71/unit),
    Mark 38 = BAG-HOLDER (−8.34/unit).
  - exotic pricers: smoke check (S=50, σ=0.30) gives chooser=2.61,
    binary put=0.011, knockout put≈0 — all consistent with closed-form
    expectations.

## 3. Round 4 EDA findings (2026-04-26)

See `prosperity-research/03_eda/round4/headline_findings.md` for full
detail. Top-line:

- **HYDROGEL_PACK** day-by-day mean: 9992.06 / 9999.5 / 10002.50 (range
  9908–10081). Soft-anchor in [9980, 10010] still holds. R3 spectral
  rhythm not yet revalidated on R4 days.
- **VELVETFRUIT_EXTRACT** day means 5248 / 5246 / 5239 (slow downward
  drift). Wall-mid microstructure unchanged from R3.
- **Voucher smile** still parabolic in log-moneyness; R4 medians match R3
  TTE=6 day fit (skew −0.13, convexity 8.8). TTE-indexed smile carries
  over directly.
- **Deep-OTM** (VEV_6000, 6500) stuck at 0.50 across all R4 days.
- **Deep-ITM** (VEV_4000, 4500) TV ≈ 0; synthetic delta-1 proxies (carry).
- **Counterparty roster (the headline R4 alpha)**:
  - Mark 14: 8,718 gross qty, +5.71/unit, 7 products. **Smart bot — copy.**
  - Mark 38: 5,000 gross qty, −8.34/unit, 7 products. **Bag-holder — fade.**
  - Mark 67: 1,510 buy qty, 0 sell qty, VE only, +1.19/unit. Buy-only.
  - Mark 01 ↔ Mark 22: voucher MM pair on OTM strikes (1,339 trades).
    Treat as noise.
  - Mark 49: modest informed seller of VE.
  - Mark 55: net mild loss-maker; light fade or ignore.
  - Mark 14 ↔ Mark 38 closed loop: 1,442 trades dominating
    HYDROGEL/VE/VEV_4000.
- **Temporal patterns weak**: no Mark concentrates >14 % of trades in any
  hour-bucket. Do not gate on time-of-day.
- **Price-level Hurst** ≈ 0.45–0.51 across liquid products → no standalone
  trend / mean-reversion alpha at the price level. Counterparty signal
  IS the alpha for Round 4.

## 4. Carry-overs from Round 3 (still valid)

The R3 alpha registry (`prosperity-research/04_signal_notes/round3/ship_now.md`)
identified 5 ship-now alphas. All carry over because algorithmic products
and microstructure are unchanged:

- A1 — HYDROGEL soft-anchor MM
- B1 — VE wall-mid MM with AR(1)
- C1 — Top-2 imbalance skew
- D1 — Voucher IV-residual scalping with TTE-indexed smile
- E1 — Deep-ITM as VE-equivalent capacity
- G1 — Parity guard (defensive)

Re-validation status on R4 data: deferred to first traders/Round4/ variant.

## 5. Known unknowns

- Whether the R3 HYDROGEL ~3330-tick spectral rhythm survives in R4 days
  1/2/3. Re-run `stat_tests.py` on the R4 voucher panel to check.
- The exact Aether Crystal spot price and full vanilla strike chain — only
  visible in the Manual Challenge UI, not in CSVs.
- Whether the Mark roster grows during live R4 (e.g. a new informed bot
  appears that wasn't in the 3-day historical). Run
  `counterparty_scan.py` on every fresh `combined.log`.
- Whether tradeable parity (ask-side) violations appear during live R4 or
  remain at 0 like R3. Run `parity_scan.py` on each refreshed panel.

## 6. Non-transferable by rule

- Do not use ASH_COATED_OSMIUM or INTARIAN_PEPPER_ROOT traders for Round 4.
  They do not trade the live products.
- Do not rely on Round 2 `bid()` logic. Irrelevant in Round 4.
- Do not assume hosted conversion behavior when the tooling flags it as
  unsimulated.
- Do not run the Round 3 Bio-Pods manual playbook — that auction has
  closed; Aether Crystal options are the live manual task.

## 7. Shipping constraints

- Preserve `(orders, conversions, traderData)` return shape.
- Keep traderData < 50,000 characters.
- One dominant change per iteration; declare the specific backtest that
  validates it.
- Do not mix HYDROGEL_PACK, VELVETFRUIT_EXTRACT, voucher, and Mark-lean
  logic in one monolithic tick function — use product-keyed sub-strategies
  with a separate `update_lean()` overlay.
