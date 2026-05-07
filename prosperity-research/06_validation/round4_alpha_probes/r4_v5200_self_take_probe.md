# r4_v5200_self_take_probe — REJECT

## Probe definition

Add an event-take on V_5200: when a market_trade in VEV_5200 fires with
qty ≥ 5, infer the aggressor side from trade price vs PRIOR tick's
bid/ask, and take VEV_5200 in the SAME direction (= follow the aggressor)
for 10 units. Daily cap 30 events.

Pre-registered: EVENT_QTY_THR=5, EVENT_TAKE_QTY=10, EVENT_HORIZON_TICKS=50,
EVENT_DAILY_CAP=30. No tuning.

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|
| day-1 | 1 | 1301 | 68,910.50 | -75.0 |
| day-2 | 2 | 1288 | 109,986.50 | -39.0 |
| day-3 | 3 | 1229 | 49,121.50 | -378.0 |
| total | | 3,818 | **228,018.50** | **−492.0** |

Trade count diff = +38 across 3 days → ~12-13 events per day (well below
the daily cap). Signal fires often enough.

## Per-product attribution (3-day Δ vs floor)

V_5200: 2,850.5 → 2,358.5 (Δ -492). All loss localised to V_5200.

## Diagnosis

The aggressor inference fires on qty≥5 prints, mostly from Mark 22 (the
OTM voucher MM) — Mark 14's V_5200 prints are mostly qty=4 (median 4 per
the dossier), which doesn't meet the threshold. So we follow Mark 22
flow, which is noise. Day-3 carries the largest loss (-378), consistent
with the down-trending VFE day where momentum-following hurts.

## Ship gate outcome

- 3-day Δ vs baseline ≥ +200: **FAIL (-492)**.
- Fires ≥ 10 times across 3 days: PASS.
- Day-3 Δ is the largest contributor (positive sense): FAIL (day-3
  carries the largest LOSS).

## Verdict — REJECT

The cross-product VEV_5200 spillover signal is real (Phase 6 nulls
source-shuffle z=+12-19) but the V_5200 self-take formulation captures
mostly Mark 22 noise rather than Mark 14's informed flow. Lower the
threshold below 5 and we'd just amplify noise; raise it and we lose
fires. The original Phase 6 finding stands: VEV_5200 spillover is
event-driven and real, but not tradeable in this form.
