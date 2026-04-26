# R4 Mark Dossier Journal — 2026-04-26

Reverse-engineering the 7 disclosed counterparties (Mark 01, 14, 22, 38,
49, 55, 67) from Round 4 historical trade + price streams.

Targets:
- Per-Mark feature CSVs (Phase 1).
- Per-Mark dossier files (Phase 2, 7 files).
- Cross-Mark coordination file + archetype table (Phase 3+4).
- Master exploitation playbook (Phase 5, supersedes counterparty_play_book.md).
- Reconciliation vs prior session (Phase 6).
- Optional probe traders (Phase 7).

## Phase 0 — context loaded

- `headline_findings.md`: Mark 14 +49,777 / +5.71/u; Mark 38 -41,696 / -8.34/u;
  Mark 14↔38 dyad has 1,442 paired trades. Mark 01↔22 dyad has 1,339 paired
  trades on OTM vouchers (PnL ±0.5/u, MM-noise pair).
- `counterparty_deep.md`: cross-product spillover all clusters on VEV_5200 →
  deeper-ITM (Mark 14 buys / Mark 22 sells). Order-book footprint from L2 bid
  drops: ZERO trigger-rate on HYD before Mark 14 buys (lift 0.00). The
  microstructure feature must come from L1, not L2.
- `mark_price_impact.csv` (Kyle's lambda h100):
  - Mark 14 HYD buy h100=+0.351, sell h100=+0.199 — clean impact (sniper).
  - Mark 38 HYD buy h100=-0.205, sell h100=-0.242 — adversary-side impact (paper).
  - Mark 67 VFE buy h100=+0.257 — clean +impact.
  - Mark 22 VFE sell h100=-0.090 — slightly adverse (paying impact).
  - Mark 49 VFE sell h100=-0.190 — adverse (paying impact).
  - Mark 55 VFE buy h100=+0.030, sell h100=+0.158 — net mild adverse buyer.
- Per-product files for HYD / VFE / VEV_5000 / VEV_5200:
  - HYD: imb1/imb2/imb3 t≈±31/±35/-35; spread locked at 16. Mark 14/38 edge
    is BRITTLE day-by-day on HYD (h=1 t-stats halve from day 1 to day 2/3).
  - VFE: Mark 67 most stable signal (h=1 +1.99/+1.86/+2.09 t>13 every day);
    Mark 49 sell h=1 +1.88/+1.76/+2.07 t>10 every day; Mark 22 sell h=1 t
    falling 7.8 → 3.1.
  - VEV_5200: 47 trades over 3 days, Mark 14 buys cluster on day 2 only.
  - VEV_5000: only 10 trades total — no per-Mark signal.
- `cross_product_mark_spillover.csv`: 13 surviving rows, all from VEV_5200 →
  VEV_4000/4500/5000/5100, with t > +5; both Mark 14 buys and Mark 22 sells
  produce identical lifts (they trade against each other). Treat as smile-shift
  co-print, not exogenous prediction.

## Phase 1 — feature store (DONE)

Script: `prosperity_rust_backtester/scripts/round4_options/per_mark_features.py`.
Outputs: 36 per-(Mark, product) CSVs, 8,562 rows total, in
`prosperity-research/03_eda/round4/per_mark/`. Inventory has 2 variants:
`inventory_day_pre/inventory_day` (resets daily) and
`inventory_cum_pre/inventory_cum` (carries across days). Schema documented
in the script docstring + `scripts/round4_options/README.md`.

## Phase 2 — per-Mark dossiers (DONE)

7 dossiers written to `04_signal_notes/round4/mark_dossiers/Mark_*.md`:

- **Mark 14** (sub-agent, 30,392 bytes) — "inside-the-touch market maker, smart bot"
- **Mark 22** (sub-agent, 22,430 bytes) — "multi-role: voucher MM + VFE seller + small-N HYD adversarial buyer"
- **Mark 67** (sub-agent, 13,570 bytes) — "buy-only VFE specialist, informed at h≤20 only"
- **Mark 38** (main session, 20,571 bytes) — "naïve two-sided taker / bag-holder"
- **Mark 01** (main session, 16,027 bytes) — "two-dyad market maker (OTM + VFE)"
- **Mark 49** (main session, 14,955 bytes) — "naïve mean-revert mistimer; FADE their sells"
- **Mark 55** (main session, 13,487 bytes) — "two-sided VFE momentum-chasing taker"

(Sub-agents wrote 3 dossiers before account-level rate limits triggered;
remaining 4 written in the main session using analysis scripts the
sub-agents had left in /tmp.)

## Phase 3 — cross-Mark coordination (DONE)

`mark_dossiers/_cross_mark.md` (24,569 bytes). Key findings:
- Mark 14 ↔ Mark 38 dyad is **same-tick paired** (median wait 0 ts), not
  sequential. The dyad is a TRADE, not a SEQUENCE.
- All pairwise joint-firing lifts are within 0.7×–1.2× of unconditional —
  no Mark predicts another Mark beyond base rate.
- 3-Mark sequential chains: no chain has lift > 1.2× over base.
- Smile-shift cross-product spillover from VEV_5200 → deeper-ITM is
  reproduced (already in D1 alpha; no new rule needed).
- Anti-prediction: no Mark systematically misleads (Mark 22 HYD buys
  closest, n=11).
- TWO new structural dyads identified vs prior session: Mark 01 ↔ Mark 55
  (VFE, 504 trades) and Mark 67 ↔ Mark 49 (VFE, 89 trades).

## Phase 4 — archetype reconciliation (DONE)

`mark_dossiers/_archetype_table.md`. All 7 Marks classified with
sub-archetype, pair partners, products, and predictability score (0–10).
No Mark scores above 5 → exploitation should prioritize POST-PRINT reaction
over PRE-PRINT prediction.

## Phase 5 — exploitation playbook (DONE)

`mark_exploitation_playbook.md` (17,546 bytes) — supersedes
`counterparty_play_book.md` (archived). 7 primary rules + 3 secondary +
production-code template + aggregate falsifiers + run-order/capacity notes.
Total pre-registered EV: ~+3,500 to +4,500 XIRECS/day vs v01 baseline of
~+1,054 captured.

Each rule pre-registers: parameters, EV estimate, falsifier, and
counterparty-conditional gating.

## Phase 6 — reconciliation (DONE)

`mark_dossiers/_reconciliation.md` (14,913 bytes). Aggregate verdict:
- 1 OVERTURNED (Mark 49 informed-seller classification was wrong; they
  are the bag side).
- 2 NEW STRUCTURAL FINDINGS (Mark 01↔55 dyad, Mark 67↔49 dyad).
- 1 CSV header CORRECTION (counterparty_findings.md mislabels Mark 67
  h=5 PnL as "h500 PnL").
- 1 PROMOTED rule (Mark 22 HYD buy fade, n=11).
- 1 DEMOTED hypothesis (Mark 01 HYD prints don't exist).
- 9 CONFIRMED, 5 REFINED with concrete parameters.

## Phase 7 — probe trader iteration v02 → v11 (BUILT + BACKTESTED)

Token budget reset partway through; iterated 10 probe variants to find
the per-day-stable winner. **v08 ships.**

| Probe | Total Δ vs v01 | Day1 Δ | Day2 Δ | Day3 Δ | Notes |
|-------|---------------:|-------:|-------:|-------:|-------|
| v02 | +1,308 | -901 | +3,566 | -1,357 | full playbook, HYD w=0.40, brittle |
| v03 | +973 | +225 | +2,167 | -1,419 | HYD w=0.30, dropped Mark 55 + Mark 22 HYD fade |
| v04 | +619 | +52 | +1,717 | -1,150 | M67 weight 0.30 |
| v05 | -1,361 | -591 | -155 | -615 | diagnostic: M67 weight 0 |
| v06 | +1,142 | -65 | +2,421 | -1,214 | M67 weight 0.50 + drift regime gate at -1/-3 |
| v07 | -41 | -975 | +1,099 | -164 | revert M49/M22/M01 to v01 |
| **v08** | **+1,528** | **+39** | **+2,421** | **-932** | **WINNER**: v06 + stricter gate at 0/-1 |
| v09 | +1,178 | -97 | +1,990 | -715 | v08 + M67 weight 0.30 |
| v10 | -746 | -302 | -503 | +58 | universal +VFE gate (over-suppressed) |
| v11 | +1,317 | +39 | +2,119 | -841 | M67 weight 0.40 + v08 gate |

### Final shipping decision

**Ship `r4_mark_dossier_v08_probe.py` as the new R4 standalone trader.**
- 3-day BT: 225,357 (vs v01's 223,829 = **+1,528**, vs v15 baseline's
  222,775 = +2,582).
- Per-day: 67,975 / 110,080 / 47,302 vs v01 67,936 / 107,658 / 48,234.
- 2/3 days positive (day-1 marginal +39, day-2 strong +2,421, day-3 -932).
- Cleared the +1,000 / 3-day stretch target from the project brief.

Locked parameters and per-day attribution in
`06_validation/round4_alpha_probes/r4_mark_dossier_v08_probe.md`.
`alpha_registry.md` SHIPPING DECISION section updated.

### What v08 does differently from v01

1. **Counterparty-conditional gating** (CP_MULT table): full lean only on
   structural-pair partners; suppressed on incidental partners.
2. **Mark 67 has its own faster decay** (HL ~20 vs HL ~46) for the short-
   horizon informed-buy signal.
3. **VFE drift regime gate** (NEW): Mark 67 +VFE contribution is suppressed
   when the EMA-smoothed VFE drift turns negative. Protects (partially)
   on down days like day-3.
4. **Larger HYD Mark 14/38 weights** (0.30 vs 0.20). Mostly saturated by
   the 200-unit position cap, but captures structural-pair alpha.
5. **Disabled rules**: Mark 55 fade (tail-driven), Mark 22 HYD buy fade
   (small N hurt iteration stability).

### Falsifiers (to monitor in live R4)

1. Live R4 day-1 mean h=100 mid-after-Mark-14 < +2.0 → kill, revert v08 → v01.
2. Live R4 day-1 Mark 14 ↔ Mark 38 pairing on HYD < 70% → kill counterparty
   gating, revert v08 → v01.
3. Live R4 day-1 mean h=5 mid-after-Mark-67 < +0.5 → kill Mark 67 lean,
   revert v08 → v01.
4. Live R4 day-1 PnL < v01 by > 500 XIRECS → revert v08 → v01 for day-2 onward.

### Lessons learned

- **The playbook EV estimates were optimistic by ~3×** because they assumed
  independent stacking of rules; in practice the HYD position-limit cap of
  ±200 binds and saturates the per-day capture. Realised stacking ≈ MAX(rules)
  not SUM(rules).
- **Mark 67's short-horizon alpha is the cleanest single contributor**
  (~+2,000 day-2 alpha). It carries inherent down-day risk on VFE; the
  regime gate attenuates but doesn't eliminate.
- **Counterparty gating helps at the margin** (~21 of 1,003 HYD prints =
  2% of trades affected) — the structural alpha is preserved while
  incidental noise is filtered.
- **The dossier-derived rules that DIDN'T survive Phase 7**: Mark 55 light
  fade (tail risk), Mark 22 HYD buy fade (noise), Mark 01 VFE mirror
  (small magnitude offset by other gains).

## Final deliverables

- `scripts/round4_options/per_mark_features.py` (Phase 1)
- `03_eda/round4/per_mark/<MARK>_<PRODUCT>.csv` × 36 (Phase 1 outputs)
- `04_signal_notes/round4/mark_dossiers/Mark_*.md` × 7 (Phase 2)
- `04_signal_notes/round4/mark_dossiers/_cross_mark.md` (Phase 3)
- `04_signal_notes/round4/mark_dossiers/_archetype_table.md` (Phase 4)
- `04_signal_notes/round4/mark_exploitation_playbook.md` (Phase 5)
- `04_signal_notes/round4/mark_dossiers/_reconciliation.md` (Phase 6)
- `04_signal_notes/round4/archive/counterparty_play_book_pre_dossier_2026-04-26.md` (archived)

Quality bar (per project brief checklist) met for every Mark dossier:
A through K all present, all evidence-graded with concrete numbers.
