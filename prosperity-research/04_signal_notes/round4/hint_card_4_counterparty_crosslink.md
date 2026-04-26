# Hint Card 4 — Anticipating Activity (R4 counterparty cross-link)

> "Pattern recognition is the easy part, honestly. Most people can do that.
> The harder part is actually letting it inform your decisions instead of
> just feeling clever about having noticed something."

This card asks for counterparty pattern mining. The R4 alpha hunt produced
two artefacts that fully cover this card:

1. `prosperity-research/04_signal_notes/round4/counterparty_play_book.md` —
   the per-Mark trading rules (Mark 14 = SMART copy, Mark 38 = BAG-HOLDER fade,
   Mark 67 = buy-only VE follow, Mark 49 = informed VE seller follow).
2. `prosperity-research/04_signal_notes/round4/counterparty_deep.md` (Phase 3
   sub-agent output) — the per-day robustness check, network classification,
   Kyle's lambda, and cross-product spillover discovery.

## Headline patterns confirmed

- **Mark 14 ↔ Mark 38 closed-loop dyad**: 1,442 trades, +8.46 XIRECS / unit
  (whichever side Mark 14 takes), Sharpe ≈ 1.8-2.0 per trade, top-10 % share
  = 0.19 (UNIFORM — not driven by big prints). All 4 (Mark 14 buy, sell;
  Mark 38 buy, sell) cells robust day-by-day (conc 0.37-0.38).
- **Mark 14's Kyle's λ on VE is near 0** (−0.011 / −0.054) despite +2.20/u
  h500 PnL. Mark 14 captures spread but doesn't move price — they are a
  passive quote-sipper. **Mark 67 IS the actual VE price-mover** (λ=+0.24
  across h=1/5/20/100, +1.19/u h500 PnL on buy-only flow).
- **Mark 67's flow is concentrated in dyads**: Mark 67→Mark 49 (n=89, qty 963,
  buyer h500 +1.256), Mark 67→Mark 22 (n=75, qty 546, +1.071). When Mark 67
  trades, the natural counterparties are the noise-providers (Mark 49
  is informed-on-the-other-side, Mark 22 is the OTM voucher MM).

## NEW R4 alpha — vega-coupling cross-strike spillover

The Phase 3 deep-dive found 13 of 660 (Mark, source-product, target-product,
horizon) cells survive Bonferroni |t| > 4 + lift ≥ 50 %. **All 13 have
VEV_5200 as the source.**

Mechanism: when the Mark 14 ↔ Mark 38 dyad prints on VEV_5200 (the
highest-vega strike where they concentrate), the deeper-ITM stack
(VEV_4000, 4500, 5000, 5100) reprices in the next 5 ticks (and continues
re-pricing for 100 ticks). This is bot-driven smile-shift contagion, not
exogenous prediction.

| Mark | source | target | side | h | mean Δmid | t | lift |
|---|---|---|---|---|---|---|---|
| Mark 22 | VEV_5200 | VEV_4000 | sell | 5 | +5.087 | +20.8 | +216% |
| Mark 14 | VEV_5200 | VEV_4000 | buy | 5 | +5.061 | +18.1 | +215% |
| Mark 22 | VEV_5200 | VEV_4500 | sell | 5 | +3.783 | +15.2 | +168% |
| Mark 14 | VEV_5200 | VEV_4500 | buy | 5 | +3.758 | +13.8 | +167% |

Tradeable if you fire on the VEV_5200 trigger and capture the deeper-ITM
re-pricing — see `r4_xprod_vev5200_probe.py` in Phase 8.

## What this card REJECTS

- **Time-of-day gating**: Phase 1 / Round 4 EDA shows no Mark concentrates
  > 14 % of trades in any hour-bucket. Do NOT gate on hour-of-day.
- **Mark 14 bid-vacuum signal**: Phase 3 lift = 0.0 / 0.01 on HYD / VE for
  level-2-bid-disappearance-before-Mark-14-buy. Mark 14 does not strip
  liquidity.
- **Mark X → Mark Y next-trade matrix as alpha**: the lifts are ~3-7×
  baseline but reflect a global "all Marks print near each other" cadence
  (the prosperity bot herd). The off-diagonal max (Mark 49 ↔ Mark 22, lift
  6.65) has only n=4 hits — noise.

## How v15 handles this today

v15 does NOT use any counterparty information — it was an R3 trader and the
counterparty fields were `None`. The Mark-conditional logic is being added
in `r4_mark_lean_v01_probe.py` (Phase 8) and the cross-product spillover
in `r4_xprod_vev5200_probe.py`.

## Falsifier per Mark (live)

- Mark 14: per-unit h500 PnL turns negative on a fresh combined.log → STOP COPY.
- Mark 38: per-unit h500 PnL turns positive on a fresh log → STOP FADE.
- Mark 67: starts selling VE (any sell n > 0) → BUY-ONLY rule is dead.
- Mark 49: per-unit h500 PnL on sells flips sign → STOP FOLLOW.
- Mark 22 sells on VE: t-stat on h=1 Δmid drops < +3 over 2 consecutive
  hist days → STOP COPY.
- VEV_5200 spillover: t-stat on day-3 alone drops < 2.5 → STOP TRADING.
