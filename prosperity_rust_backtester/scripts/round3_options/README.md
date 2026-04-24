# Round 3 options analysis toolkit

Stateless utilities for Prosperity 4 Round 3 voucher analysis. These are pure
research tools: they never import trader code and never touch `runs/`.

Products in scope:
- `HYDROGEL_PACK` (delta-1, pinned ~10000, pos limit 200)
- `VELVETFRUIT_EXTRACT` (delta-1 underlying, pos limit 200)
- `VEV_{4000,4500,5000,5100,5200,5300,5400,5500,6000,6500}` (10 call vouchers, pos limit 300 each)

Voucher expiry: 7 trading rounds from start of Round 1.
- Historical `prices_round_3_day_0` → TTE = 8 days
- Historical `prices_round_3_day_1` → TTE = 7 days
- Historical `prices_round_3_day_2` → TTE = 6 days
- Start of Round 3 live → TTE = 5 days
- Round-to-round: TTE decreases by 1 per round.

Tick granularity: 100 ticks per day in Prosperity (confirm in forensics).

## Scripts

- `bs.py`: Black-Scholes call pricer, vega, implied-vol solver (Newton+bisection).
- `build_voucher_panel.py`: assembles underlying + 10 vouchers into a per-tick panel with intrinsic / time-value / IV / log-moneyness / moneyness bucket.
- `vol_surface_fit.py`: fits a per-tick quadratic in log-moneyness (parabolic smile) and returns residuals + ATM IV + curvature. Tracks base IV as a rolling series.
- `parity_scan.py`: identity-only checks: intrinsic floor, upper bound `V <= S`, strike monotonicity, butterfly convexity. Flags violations with timestamps.
- `iv_diagnostics.py`: distribution of IV, per-strike IV stability, vol term structure (IV at TTE=8 vs 7 vs 6).

## Output contract

All scripts default to writing compact CSV/JSON under
`prosperity-research/03_eda/round3/` or `prosperity-research/04_signal_notes/round3/`.
They never write into `runs/` or trader files.

## Assumptions (explicit)

- Risk-free rate: 0 (Prosperity has no stated rate: treat as zero).
- No dividends.
- Call payoff at expiry: `max(S_T - K, 0)`.
- Underlying mid: `(best_bid_1 + best_ask_1) / 2`. Microprice available as optional.
- A voucher with missing depth on one side uses the last valid mid and is flagged as stale.
