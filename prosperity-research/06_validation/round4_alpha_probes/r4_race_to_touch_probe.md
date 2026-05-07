# r4_race_to_touch_probe — REJECT (falsifier triggered)

## Probe definition

Track Mark 14's last-known HYD bid/ask from market trades; decay toward
mid; quote one tick inside that level (per spec formula:
`bp = min(default_bp, last_mark14_bid + 1)`,
`sp = max(default_sp, last_mark14_ask - 1)`).
Inventory governor (|pos|>0.7×200 → revert), race-loss detector
(5 consecutive losses → 200-tick timeout).

Pre-registered (locked): RTT_DRIFT_RATE=0.05, RTT_INVENTORY_GOVERN=0.7,
RTT_RACE_LOSS_THRESHOLD=5, RTT_RACE_TIMEOUT_TICKS=200, products=[HYD].

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|
| day-1 | 1 | 1299 | 69,076.50 | +91.0 |
| day-2 | 2 | 1280 | 109,585.50 | -440.0 |
| day-3 | 3 | 1193 | 49,297.50 | -202.0 |
| total | | 3,772 | **227,959.50** | **−551.0** |

HYD trade count: 3,772 vs floor's 3,780 → drops by 8 (-0.21%).
HYD product Δ: 134,030 vs 134,581 → -551 (entirely localised to HYD).
Disjoint products (VFE / vouchers) all match floor exactly as expected.

## Diagnosis

The pre-registered formula `bp = min(default, mark14_bid+1)` only LOWERS
our bid (never raises it). Symmetric for ask. So if v15's default bp is
already TIGHTER than mark14_bid+1, the formula does nothing; if it's
LOOSER (lower bp than mark14_bid+1), we'd be moved to mark14_bid+1 —
which is still LOOSER than the default, just by less. In practice:

- Mark 14 quotes ~16 ticks INSIDE the displayed touch (median price -
  ask_pre = -16). Their bid level is typically near the prevailing mid.
- v15's default bp = floor(fair - H_QE=3) ≈ mid-3. That's already
  tighter than typical Mark 14 levels in many states.
- So the formula's `min` mostly leaves bp at default. Occasionally it
  loosens bp by 1-2 ticks.
- Net effect: marginal loosening on HYD; trade count drops slightly,
  PnL drops slightly.

The race-loss detector mostly doesn't fire in these conditions because
we don't get tighter quotes than Mark 14 ourselves.

## Ship gate outcome

- 3-day Δ vs baseline ≥ +1,500: **FAIL (-551)**.
- HYD own_trades INCREASES by ≥ 10%: **FAIL (drops by 0.21%)**.
- HYD product Δ ≥ +1,500: **FAIL (-551)**.

Falsifier triggered: "HYD own_trades count DROPS → kill (we're standing
aside)". Confirmed.

## Verdict — REJECT

The pre-registered race-to-the-touch formula does not capture the
intended Mark 14 alpha. The dossier's K.2 hypothesis (that we can split
the +8 tick edge with Mark 14 by quoting inside their level) is real but
requires:
- Either more aggressive quoting (e.g., `bp = max(default, mark14_bid+1)`
  to actually move tighter, not looser), or
- A combined approach with the existing v15 quote ladder.

This probe REJECTS as written. The mechanism is plausible but the formula
needs reformulation outside this session's pre-registration.
