# Round 4 probes

Single-idea experimental traders used to isolate one alpha at a time before
folding the winners into the production trader. Each `r4_*_probe.py` tests one
change (a bias term, a smile refit, a mark-lean variant, a cross-product take)
so its PnL effect can be read cleanly against a named baseline.

Two loose files from the top of `Round4/` were renamed into this folder during
cleanup, since they are the same kind of throwaway HYDROGEL experiment:

- `r4_hyd_microprice_anchor_probe.py` (was `a.py`): microprice plus soft-anchor
  fair value with a small order-book adjustment.
- `r4_hyd_anchor_baseline_probe.py` (was `b.py`): the simpler fixed-anchor,
  buy-only-when-cheap baseline it was compared against.

The shipped Round 4 trader is `../../../../submissions/r4_final_v01_imc_upload.py`.
