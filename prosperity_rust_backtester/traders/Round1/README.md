# Round 1 Trader Layout

This directory holds structured Round 1 trader assets.

- `active/`: current named Round 1 milestones
  - `round1_overhaul_v63.py`: benchmark baseline
  - `round1_pepper_dual_carry_v11.py`: current best local carry frontier
- `work/`: staged future experiments before promotion
  - `work/pepper_carry/validated/`: tested carry-family evolution
  - `work/pepper_carry/unvalidated/`: later carry branches not yet validated
  - `work/pepper_carry/prototypes/`: oracle / microstructure / trade-gated prototypes

Historical Round 1 variants, probes, and research traders live in `../../trader_archive/Round1/`.
Keep only `latest_trader.py` and high-signal documentation at the top level of `../`.

Start with:

- `../../CODEX_ROUND1_STRATEGY_CONTEXT.md`
- `work/pepper_carry/README.md`
