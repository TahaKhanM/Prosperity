# Round 4 Strategy Playbook

Concrete ranked alpha set for Round 4 ("The More The Merrier", Salvinar). The
algorithmic products and microstructure are unchanged from Round 3, so the
five validated R3 alphas (HYDROGEL soft-anchor MM, VE wall-mid MM, top-2
imbalance skew, voucher IV-residual scalping with TTE-indexed smile, and the
parity guard) carry over. The new Round 4 alpha class is **counterparty
copy/fade by Mark ID** — disclosed for the first time this round.

Read alongside:
- `prosperity-research/08_playbooks/round3_strategy_playbook.md` — full
  parameters for the carry-over alphas (kept here intentionally; do not
  duplicate).
- `prosperity-research/04_signal_notes/round4/counterparty_play_book.md` —
  per-Mark trading rules.
- `prosperity-research/03_eda/round4/headline_findings.md` — counterparty
  EDA numbers (the source of truth for ranking).

## Ranked alpha set

| Rank | Alpha | Confidence | Reference |
|---|---|---|---|
| 1 | **Mark 14 copy + Mark 38 fade** on HYDROGEL/VE | High (NEW) | `counterparty_play_book.md` |
| 2 | A1 — HYDROGEL soft-anchor MM | High (carry) | R3 playbook §1 |
| 3 | B1 — VE wall-mid MM with AR(1) | High (carry) | R3 playbook §2 |
| 4 | D1 — Voucher IV-residual scalping (TTE-indexed) | High (carry) | R3 playbook §3 |
| 5 | C1 — Top-2 imbalance skew | Medium (carry) | R3 playbook §4 |
| 6 | Mark 67 buy-only confirm long-VE | Medium (NEW) | `counterparty_play_book.md` |
| 7 | E1 — Deep-ITM as VE-equivalent capacity | Medium (carry) | R3 `structural_quirks.md` |
| 8 | G1 — Parity guard | Low (carry, defensive) | R3 playbook §5 |

## Headline new alpha — Mark copy/fade

### Claim
The Round 4 historical data shows a clean **smart-bot / bag-holder pair**
on HYDROGEL_PACK and VELVETFRUIT_EXTRACT:

- **Mark 14**: +5.71 XIRECS per unit horizon-500 PnL (4,510 buys, 4,208 sells).
- **Mark 38**: −8.34 per unit (mirror image).
- They trade against each other 1,442 times — Mark 38 is consistently giving
  Mark 14 the right side of the trade.

### Hyperparameters (start)
```
LEAN_PER_UNIT_QTY   = 0.05   # decay-weighted skew per Mark print
LEAN_HALF_LIFE_TICKS= 50     # Mark prints expire over ~250 ticks
M14_M38_PRODUCTS    = ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_4000"]
M67_PRODUCTS        = ["VELVETFRUIT_EXTRACT"]
M67_LEAN_FACTOR     = 0.5    # half magnitude vs Mark 14
```

### Tick logic
```python
# 1. decay all leans
for product in lean:
    lean[product] *= 0.5 ** (1 / LEAN_HALF_LIFE_TICKS)

# 2. add new contributions
for product, trades in state.market_trades.items():
    if product not in M14_M38_PRODUCTS and product not in M67_PRODUCTS:
        continue
    for t in trades:
        if t.timestamp != state.timestamp:
            continue                 # only use this-tick prints
        w = float(t.quantity) * LEAN_PER_UNIT_QTY
        if t.buyer == "Mark 14" or t.seller == "Mark 38":
            lean[product] = lean.get(product, 0) + w
        elif t.seller == "Mark 14" or t.buyer == "Mark 38":
            lean[product] = lean.get(product, 0) - w
        if product in M67_PRODUCTS and t.buyer == "Mark 67":
            lean[product] = lean.get(product, 0) + M67_LEAN_FACTOR * w

# 3. apply lean to the MM fair (or to the take threshold)
fair_with_lean = fair + clamp(lean.get(product, 0), -3, +3)
```

### How it stacks with the R3 carry-overs
- HYDROGEL soft-anchor MM (§A1) and VE wall-mid MM (§B1) become **lean-aware
  MMs**: the same `clamp(EMA, anchor_lo, anchor_hi)` fair, but skewed by
  ±lean each tick. Take-thresholds also bias.
- The voucher residual scalp (§D1) is largely unaffected — Mark 14/38 PnL
  on vouchers is dominated by deep-ITM (delta-1) prints which are already
  captured by the underlying VE lean.

### Validation
- Cross-check on R4 day 1/2/3 against the no-lean baseline:
  `make round4 TRADER=traders/Round4/round4_no_lean_baseline.py DAY=all`
  vs `traders/Round4/round4_mark_lean_v01.py DAY=all`.
- Expected delta on the 3-day historical: **+8 to +15k XIRECS** per day if
  the lean is well-tuned. (Estimate: Mark 14 + Mark 38 net horizon PnL ≈
  91k/day across HYDROGEL+VE; capturing a third of that at our reaction
  speed is plausible.)

### Falsifier
If the per-unit horizon-500 PnL of Mark 14 falls below +2 (or Mark 38's rises
above −2) on a fresh `counterparty_scan.py` run after the next live
submission, **disable** the lean. Save daily snapshots of
`counterparty_findings.md` to `prosperity-research/03_eda/round4/snapshots/`.

## R3 carry-overs — quick recap (do not duplicate parameters)

The full hyperparameters for these are in
`prosperity-research/08_playbooks/round3_strategy_playbook.md` §1–§5.
Recap of what they do:

- **A1 — HYDROGEL soft-anchor MM**. `fair = clamp(EMA_200, 9980, 10010)`
  seeded at empirical day mean. Take ≤ fair−1 / ≥ fair+1, post one tick
  inside the next resting level. Soft inventory limit at ±80.
- **B1 — VE wall-mid MM**. Wall mid (largest-vol level on each side) with
  AR(1) `β ≈ -0.2` adjustment. Take/clear at ±1 / 0 from fair.
- **C1 — Top-2 imbalance skew**. Compute order-book imbalance from levels
  1+2 of both sides; skew the fair by ±1 tick when imbalance > ±0.6.
- **D1 — Voucher IV-residual scalping**. Per-tick smile fit (or frozen
  TTE-indexed coefficients), trade residuals > per-strike thresholds.
  **Re-fit per TTE bucket** (R4 has 7/6/5/4 buckets). VE wall mid → S; mid
  → V_K; vega = `bs_call_vega`.
- **E1 — Deep-ITM as VE-capacity**. Treat VEV_4000 + VEV_4500 as +600 of
  synthetic VE capacity. Long them when long-VE-lean is strong; do not
  trade them on residual.
- **G1 — Parity guard**. Defensive only. Validate on tradeable side, not
  mid. Expect ~0–2 violations / 10,000 ticks (R3 baseline).

## Build order for Round 4 traders

Recommended trader iteration:

1. `traders/Round4/round4_no_lean_baseline.py` — A1+B1+C1+D1+E1+G1 ported
   straight from the best R3 trader (`Round3/candidates/v15.py` is a strong
   starting point). Target: match or beat its R3 PnL on R4 days.
2. `traders/Round4/round4_mark_lean_v01.py` — adds the Mark 14 / 38 lean
   to A1 + B1 only. Smallest change with the largest expected gain.
3. `traders/Round4/round4_mark_lean_v02.py` — extends lean to E1 (deep-ITM
   delta-1 capacity).
4. `traders/Round4/round4_mark_lean_v03.py` — adds Mark 67 confirm-only on
   VE; tunes lean half-life and per-unit weight.
5. (Stretch) `traders/Round4/round4_mark_residual_scalp_v01.py` — uses Mark
   prints to *gate* residual entries on the voucher chain (only trade when
   the Mark lean and the vol-residual agree in sign).

Each promotion needs a named baseline and a single 3-day rust BT comparison.
One dominant change per iteration.
