# scripts/manual_round

Purpose: keep manual-challenge tooling separate from trader code and local
backtester behavior.

Inputs:
- documented manual mechanics from `Prosperity Context/20_MANUAL_TRADING_CONTEXT.md`
- explicit scenario files or CLI grids for the manual challenge

Outputs:
- Round 1 auction solver outputs under
  `prosperity-research/07_manual_round/round1_auction/`
- Round 2 budget allocator outputs under
  `prosperity-research/07_manual_round/round2_budget/`

Notes:
- these tools are scenario-driven because no hidden manual inputs are assumed to
  exist in the repo
- keep manual outputs separate from algo-trader implementation
