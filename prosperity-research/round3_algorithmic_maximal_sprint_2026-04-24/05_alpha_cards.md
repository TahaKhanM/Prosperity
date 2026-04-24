# Round 3 alpha cards — 2026-04-24

All cards follow the alpha-hypothesis-lab format. `alpha_id` is stable and
scoped to Round 3. Every card ends with a decision.

---

## R3-VFE-voucher-intrinsic-arb-v01

- **Products:** `VELVET_FRUIT_EXTRACT` + every `VELVET_FRUIT_EXTRACT_VOUCHER_<K>`.
- **Mechanism:** when a voucher trades below `max(mid(VFE) - K, 0) - slack`,
  buy it at the best ask. When it trades above `mid(VFE) + slack`, sell at
  the best bid. These are identity arbs, not statistical bets.
- **Why it could create PnL:** voucher books on a fresh contract are often
  thin; occasional mis-quotes inside the intrinsic band are common in Prosperity-style games.
- **Required evidence:** at least one round of voucher CSV showing a non-trivial
  fraction of quotes in the ITM intrinsic band.
- **Evidence found:** NONE in this sandbox (no Round 3 CSVs).
- **Null:** voucher best-ask is never strictly below `max(mid(VFE) - K, 0)` on any tick.
- **Falsification test:** on day `-2` of Round 3, count ticks where `best_ask(V_K) + slack < max(mid(VFE) - K, 0)` for each K. If count is zero for every K, the alpha is falsified for this round.
- **Overfit risk:** zero (identity).
- **Complexity:** low.
- **Risk / inventory:** bounded by per-voucher position cap; unwind is free because the gate only fires on mispriced ITM vouchers.
- **Expected failure modes:** (1) settlement is not `max(S-K,0)`; (2) voucher timestamps lag VFE timestamps; (3) position limit on vouchers is so small that the aggregate worst-case rejection cancels the order.
- **Decision:** **IMPLEMENT**, gated by strict slack and per-voucher position caps. Safe to include even without Round 3 evidence because the action is bounded by an identity.

---

## R3-VFE-voucher-strike-monotonicity-v01

- **Products:** any two vouchers with strikes `K1 > K2`.
- **Mechanism:** if `best_bid(V_{K1}) > best_ask(V_{K2}) + slack`, sell V_{K1} and buy V_{K2} in equal size.
- **Why it could create PnL:** monotonicity is a hard identity; violation is a free arb modulo execution risk.
- **Required evidence:** at least one observed violation in any round of data.
- **Evidence found:** none.
- **Null:** no monotonicity violations exist.
- **Falsification test:** scan Round 3 day `-2` for simultaneous-tick violations.
- **Overfit risk:** zero.
- **Complexity:** medium (needs two-sided simultaneous fill; aggregate limit check must cover both products).
- **Risk / inventory:** the paired trade nets to zero directional exposure on VFE if the vouchers have the same payoff slope; it is long K2-K1 of strike-spread value.
- **Expected failure modes:** (1) one leg fills, the other does not → residual strike-spread position; (2) worst-case aggregate limit check rejects both legs.
- **Decision:** **HOLD** (implemented as an optional gate guarded by a conservative per-submission switch; disabled by default until Round 3 data confirms at least one violation).

---

## R3-HYDROGEL-mean-reversion-v01

- **Products:** `HYDROGEL_PACKS`.
- **Mechanism:** classic z-score mean reversion around a rolling mid.
- **Required evidence:** autocorrelation profile on day `-2` prices.
- **Evidence found:** none.
- **Null:** returns are a random walk.
- **Decision:** **REJECT for this sprint.** No data. Recording for future invocation once `datasets/round3/` is populated.

---

## R3-HYDROGEL-anchored-mean-v01

- **Products:** `HYDROGEL_PACKS`.
- **Mechanism:** treat the product as anchored around a fixed fair value (like tutorial `EMERALDS`); take at the band, quote around the anchor.
- **Required evidence:** flat day-over-day mid distribution.
- **Evidence found:** none.
- **Decision:** **REJECT for this sprint.** Would be an unjustified import of the tutorial assumption.

---

## R3-VFE-momentum-v01

- **Products:** `VELVET_FRUIT_EXTRACT`.
- **Mechanism:** follow the short-horizon drift in VFE via an EWMA of microprice changes.
- **Required evidence:** positive variance-ratio at 3–5 ticks.
- **Evidence found:** none.
- **Decision:** **REJECT for this sprint.**

---

## R3-VFE-book-imbalance-v01

- **Products:** `VELVET_FRUIT_EXTRACT`.
- **Mechanism:** lean quotes in the direction of best-level size imbalance; signal is known to matter in Round-1 / Round-2 analysis on ASH_COATED_OSMIUM.
- **Required evidence:** per-tick imbalance–future-return correlation on Round 3 data.
- **Evidence found:** none for Round 3. The existence of the signal on Round 1/2 ASH is not admissible as Round 3 evidence.
- **Decision:** **REJECT for this sprint.**

---

## R3-STRUCT-submission-safe-scaffold-v01

- **Products:** all.
- **Mechanism:** a submission-compatible, worst-case-position-safe trader that
  handles arbitrary product sets, tracks positions from `state.position`,
  never sends more than `max(cap - current, 0)` buy volume or `max(cap + current, 0)` sell volume, truncates all quotes against the aggregate limit rule, and stores a compact `traderData` blob under 50 KB.
- **Required evidence:** the interface contract in `imc-prosperity-4-backtester/prosperity4bt/datamodel.py` and the trader patterns in `traders/Round1/Ash.py` and `traders/Round 2/baseline.py`.
- **Evidence found:** both confirmed in this session.
- **Decision:** **IMPLEMENT.** This is the structural backbone the voucher-intrinsic alpha rides on.

---

## Summary

| alpha_id | decision | reason |
|---|---|---|
| R3-VFE-voucher-intrinsic-arb-v01 | IMPLEMENT | identity-bounded, safe even without Round 3 data |
| R3-VFE-voucher-strike-monotonicity-v01 | HOLD | implemented behind a default-off switch |
| R3-HYDROGEL-mean-reversion-v01 | REJECT | no data |
| R3-HYDROGEL-anchored-mean-v01 | REJECT | unjustified assumption import |
| R3-VFE-momentum-v01 | REJECT | no data |
| R3-VFE-book-imbalance-v01 | REJECT | no Round 3 evidence |
| R3-STRUCT-submission-safe-scaffold-v01 | IMPLEMENT | interface-verified |
