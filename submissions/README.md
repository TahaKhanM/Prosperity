# submissions

Traders submitted to the IMC Prosperity portal, kept exactly as uploaded.

- `r4_final_v01_imc_upload.py` is the Round 4 production trader. It composes
  the two ship-grade Round 4 alphas (mark-lean and a V_5000 imbalance take) on
  top of the Round 3 `v15` baseline (HYDROGEL soft-anchor market making,
  VELVETFRUIT wall-mid making, order-book imbalance skew and voucher
  IV-residual scalping).

To replay it locally, point the Rust backtester at it, for example:
`cd prosperity_rust_backtester && make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=1`.
