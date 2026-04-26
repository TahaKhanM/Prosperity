# Carry-over from Round 3 to Round 4

The algorithmic products and microstructure are unchanged across Round 3 →
Round 4. Therefore most R3 alphas apply directly. The only **new** alpha
class in Round 4 is the disclosed counterparty IDs (`Mark <NN>`).

## What carries over (use as-is)

| Alpha | R3 location | R4 status |
|---|---|---|
| A1 — HYDROGEL soft-anchor MM | `04_signal_notes/round3/ship_now.md` | Carry over. Re-validate anchor band on R4 day mids (9992 / 9999 / 10003). |
| B1 — VE wall-mid MM with AR(1) | `04_signal_notes/round3/ship_now.md` | Carry over. R4 VE drifted 5248 → 5239 across days; β remains slightly negative. |
| C1 — Top-2 imbalance skew | `04_signal_notes/round3/ship_now.md` | Carry over. |
| D1 — Voucher IV-residual scalping | `04_signal_notes/round3/ship_now.md` + `vol_surface_coeffs.csv` | Carry over. Re-fit TTE-indexed smile on R4 panel; skew −0.13, convexity 8.8 in R4 medians match R3. |
| E1 — Deep-ITM as VE-equivalent capacity | `04_signal_notes/round3/structural_quirks.md` | Carry over. VEV_4000/4500 remain TV ≈ 0 in R4. |
| G1 — Parity guard | `04_signal_notes/round3/ship_now.md` | Carry over. R4 mid-based scan flags 11,849 floor "violations" (mostly K=4500); same artefact as R3, not tradeable on ask. |

## What changes

- **NEW alpha class — copy/fade by Mark ID.** See `counterparty_play_book.md`.
- **TTE indexing now covers TTE 4 live** (R3 was TTE 5 live). Make sure the
  smile fit is generalized over `tte_years`, not hardcoded to one bucket.

## What is rejected

- HYDROGEL spectral 3330-tick rhythm — was a day-0-only artefact in R3.
  Revalidate on R4 days 1/2/3 before trusting.
- HYDROGEL 1-tick AC1 fade — spread cost (8) > revert edge (~0.27).
- Per-strike static IV biases — knife-edge in R3; do not port into R4.
- Counterparty time-of-day gating — R4 EDA shows weak temporal structure
  (peak hour-bucket share ≤ 14 %).

## R3 research artefacts (preserved, kept under `04_signal_notes/round3/`)

- `ship_now.md` — five R3 ship-now alphas with parameters.
- `structural_quirks.md` — four real R3 quirks (HYDROGEL not pinned at 10000;
  deep-ITM TV = 0; deterministic TTE drift in smile; clean tradeable parity).
  All four still apply in R4.
- `vol_surface_coeffs.csv` / `vol_surface_residuals.csv` — R3 smile fit.
- `counterparty_scan.csv` / `counterparty_findings.md` — R3 anonymous-only
  counterparty rollup (kept for reference).
- `parity_violations.csv` — R3 mid-vs-intrinsic violations.
- `alpha_registry.md` — pre-Round-4 alpha registry.
